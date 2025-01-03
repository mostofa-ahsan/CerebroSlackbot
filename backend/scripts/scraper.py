import os
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from authenticator import login_to_verizon

BASE_URL = "https://brandcentral.verizonwireless.com"
OUTPUT_DIR = "./scraped_pages"
IMAGE_DIR = "./saved_images"
SIGNOUT_KEYWORDS = ["signout", "logout"]
PROGRESS_FILE = "progress.txt"

def download_image(image_url, image_dir):
    """Download an image from the given URL."""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        filename = os.path.join(image_dir, os.path.basename(image_url))
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded image: {filename}")
    except Exception as e:
        print(f"Failed to download image {image_url}: {e}")

def explore_and_scrape(driver):
    """Explore all menus, buttons, and scrape content."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    # Load progress if it exists
    completed = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            completed = set(line.strip() for line in f)

    to_visit = [BASE_URL]
    visited = set()

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited or any(keyword in current_url.lower() for keyword in SIGNOUT_KEYWORDS):
            continue
        visited.add(current_url)

        print(f"Exploring: {current_url}")
        try:
            driver.get(current_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Save page content
            content = driver.page_source
            filename = os.path.join(OUTPUT_DIR, f"{current_url.replace('/', '_').replace(':', '')}.html")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            # Find and download images
            images = driver.execute_script(
                "return Array.from(document.querySelectorAll('img')).map(img => img.src);"
            )
            for image_url in images:
                if not image_url.startswith("http"):
                    image_url = BASE_URL + image_url
                download_image(image_url, IMAGE_DIR)

            # Find interactive elements: menu items, buttons, etc.
            elements = driver.execute_script(
                """
                return Array.from(document.querySelectorAll('a[href], button, input[type="button"], input[type="submit"]'))
                    .map(e => e.href || e.dataset.url || e.getAttribute('onclick') || e.innerText || '');
                """
            )
            for element in elements:
                if element.startswith(BASE_URL) and element not in visited:
                    to_visit.append(element)

            # Save progress
            with open(PROGRESS_FILE, "a") as f:
                f.write(current_url + "\n")

        except TimeoutException:
            print(f"Timeout while trying to load: {current_url}")
        except ElementClickInterceptedException:
            print(f"Element could not be clicked on page: {current_url}")
        except Exception as e:
            print(f"Error exploring {current_url}: {e}")

        # Print the last link visited
        print(f"Last visited link: {current_url}")

    print(f"Exploration and scraping completed. Pages saved in {OUTPUT_DIR}, images in {IMAGE_DIR}.")

if __name__ == "__main__":
    driver = login_to_verizon()
    if driver:
        try:
            explore_and_scrape(driver)
        finally:
            driver.quit()
