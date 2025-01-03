import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin

# Selenium setup
CHROME_DRIVER_PATH = "path/to/chromedriver"  # Update this with your ChromeDriver path
BASE_URL = "https://brandcentral.verizon.wireless.com"
OUTPUT_DIR = "../data/scraped_pages"

def scrape_website(base_url, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    visited = set()
    to_visit = [base_url]

    # Configure Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=chrome_options)

    def save_page(url, content):
        """Save page content to a file."""
        filename = os.path.join(output_dir, f"{url.replace(base_url, '').replace('/', '_')}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

    while to_visit:
        current_url = to_visit.pop()
        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            # Load the page
            driver.get(current_url)
            time.sleep(3)  # Allow time for JavaScript to load
            content = driver.page_source
            save_page(current_url, content)

            # Extract and queue new links
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and base_url in href and href not in visited:
                    to_visit.append(href)

        except Exception as e:
            print(f"Error scraping {current_url}: {e}")

    driver.quit()
    print(f"Scraping completed. Files saved in {output_dir}.")

if __name__ == "__main__":
    scrape_website(BASE_URL, OUTPUT_DIR)
