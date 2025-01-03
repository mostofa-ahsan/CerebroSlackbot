import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://brandcentral.verizon.wireless.com"
OUTPUT_DIR = "../data/scraped_pages"

def scrape_website(base_url, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    visited = set()

    def scrape_page(url):
        if url in visited:
            return
        visited.add(url)

        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch {url}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        filename = os.path.join(output_dir, f"{url.replace(base_url, '').replace('/', '_')}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(soup.prettify())

        for link in soup.find_all("a", href=True):
            href = urljoin(base_url, link['href'])
            if base_url in href and href not in visited:
                scrape_page(href)

    scrape_page(base_url)
    print(f"Scraping completed. Files saved in {output_dir}.")

if __name__ == "__main__":
    scrape_website(BASE_URL, OUTPUT_DIR)
