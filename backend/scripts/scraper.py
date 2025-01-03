import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin

BASE_URL = "https://brandcentral.verizon.wireless.com"
OUTPUT_DIR = "./scraped_pages"

def scrape_website(base_url, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    visited = set()
    to_visit = [base_url]

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    def save_page(url, content):
        filename = os.path.join(output_dir, f"{url.replace(base_url, '').replace('/', '_')}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            driver.get(current_url)
            time.sleep(3)
            content = driver.page_source
            save_page(current_url, content)

            links = driver.execute_script("""
                return Array.from(document.querySelectorAll('a')).map(a => a.href);
            """)
            for link in links:
                if base_url in link and link not in visited:
                    to_visit.append(link)

        except Exception as e:
            print(f"Error scraping {current_url}: {e}")

    driver.quit()
    print(f"Scraping completed. Files saved in {output_dir}.")
