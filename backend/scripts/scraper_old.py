import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from authenticator import login_to_verizon

BASE_URL = "https://brandcentral.verizonwireless.com"
OUTPUT_DIR = "./scraped_pages"
SIGNOUT_KEYWORDS = ["signout", "logout", "restricted", "restricted-assets"]
PROGRESS_FILE = "progress.txt"

def extract_links(driver):
    """Extract all unique links within the domain."""
    print("Extracting all possible links...")
    visited = set()
    to_visit = [BASE_URL]
    all_links = []

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        print(f"Collecting links from: {current_url}")
        try:
            driver.get(current_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Try to expand dynamically loaded links
            try:
                driver.execute_script("document.querySelectorAll('a').forEach(a => a.click());")
            except Exception:
                pass

            # Extract all links on the page
            links = driver.execute_script(
                "return Array.from(document.querySelectorAll('a[href]')).map(a => a.href);"
            )
            for link in links:
                if link.startswith(BASE_URL) and link not in visited:
                    all_links.append(link)
                    to_visit.append(link)

        except TimeoutException:
            print(f"Timeout while trying to load: {current_url}")
        except Exception as e:
            print(f"Error collecting links from {current_url}: {e}")

    print(f"Total unique links collected: {len(set(all_links))}")
    return list(set(all_links))

def scrape_links(driver, links):
    """Scrape all links and save the content."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load progress if it exists
    completed = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            completed = set(line.strip() for line in f)

    for link in links:
        # Skip already scraped links
        if link in completed:
            continue

        # Skip links with signout/logout keywords
        if any(keyword in link.lower() for keyword in SIGNOUT_KEYWORDS):
            print(f"Skipping signout/logout link: {link}")
            continue

        print(f"Scraping: {link}")
        try:
            driver.get(link)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Save page content
            content = driver.page_source
            filename = os.path.join(OUTPUT_DIR, f"{link.replace('/', '_').replace(':', '')}.html")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            # Save progress
            with open(PROGRESS_FILE, "a") as f:
                f.write(link + "\n")

        except TimeoutException:
            print(f"Timeout while trying to load: {link}")
        except Exception as e:
            print(f"Error scraping {link}: {e}")

        # Print the last link visited
        print(f"Last visited link: {link}")

    print(f"Scraping completed. Pages saved in {OUTPUT_DIR}.")

if __name__ == "__main__":
    driver = login_to_verizon()
    if driver:
        try:
            # Step 1: Extract all links
            links = extract_links(driver)

            # Step 2: Scrape the links
            scrape_links(driver, links)
        finally:
            driver.quit()