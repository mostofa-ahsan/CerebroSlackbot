import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

BASE_URL = "https://brandcentral.verizonwireless.com/home"
OUTPUT_DIR = "./data/scraped_pages"

def scrape_website():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Set up Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    try:
        # Step 1: Start from home page (login already done)
        driver.get(BASE_URL)
        time.sleep(3)

        # Step 2: Scrape all internal links
        visited = set()
        to_visit = [BASE_URL]

        def save_page(url, content):
            """Save page content to a file."""
            filename = os.path.join(OUTPUT_DIR, f"{url.replace(BASE_URL, '').replace('/', '_')}.html")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

        while to_visit:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)

            driver.get(current_url)
            time.sleep(3)
            content = driver.page_source
            save_page(current_url, content)

            links = driver.execute_script("""
                return Array.from(document.querySelectorAll('a')).map(a => a.href);
            """)
            for link in links:
                if BASE_URL in link and link not in visited:
                    to_visit.append(link)

        print(f"Scraping completed. Files saved in {OUTPUT_DIR}.")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_website()
