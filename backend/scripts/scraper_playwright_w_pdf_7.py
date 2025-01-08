import os
import json
import atexit
import datetime
import requests
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "../data/scraped_pages"
PDF_OUTPUT_DIR = "../data/pages_as_pdf"
DOWNLOAD_DIR = "../data/downloads"
IMAGE_DIR = "../data/saved_images"
SIGNOUT_KEYWORDS = ["signout", "logout", "print"]

# Global variables for visited links and scrap summary
visited_links = []
scrap_summary = []

# File paths with timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
VISITED_LINKS_FILE = f"../data/visited_links_{timestamp}.json"
SCRAP_SUMMARY_FILE = f"../data/scrap_summary_{timestamp}.json"


def save_visited_links():
    """Save visited links and scrap summary to files."""
    with open(VISITED_LINKS_FILE, "w") as f:
        json.dump(visited_links, f, indent=4)
    print(f"Visited links saved to {VISITED_LINKS_FILE}")

    with open(SCRAP_SUMMARY_FILE, "w") as f:
        json.dump(scrap_summary, f, indent=4)
    print(f"Scrap summary saved to {SCRAP_SUMMARY_FILE}")


# Register the save_visited_links function to run on exit
atexit.register(save_visited_links)


def transfer_cookies_to_playwright(selenium_cookies):
    """Convert Selenium cookies to Playwright cookies."""
    return [
        {
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": cookie["domain"],
            "path": cookie["path"],
            "expires": cookie.get("expiry"),
            "httpOnly": cookie.get("httpOnly", False),
            "secure": cookie.get("secure", False),
            "sameSite": cookie.get("sameSite", "Lax"),
        }
        for cookie in selenium_cookies
    ]

def create_playwright_context(selenium_cookies):
    """
    Create a Playwright browser context and apply cookies.

    Args:
        selenium_cookies (list): A list of cookies from Selenium to apply in Playwright.

    Returns:
        tuple: (Playwright context, Playwright page)
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    # Convert Selenium cookies to Playwright format
    playwright_cookies = transfer_cookies_to_playwright(selenium_cookies)

    # Apply cookies to the context
    context.add_cookies(playwright_cookies)

    # Create a new page
    page = context.new_page()
    return context, page

def download_file(file_url, save_dir):
    """Download a file and save it."""
    try:
        os.makedirs(save_dir, exist_ok=True)
        local_filename = os.path.join(save_dir, os.path.basename(urlparse(file_url).path))
        response = requests.get(file_url, stream=True, timeout=10)
        response.raise_for_status()

        with open(local_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded file: {local_filename}")
        return local_filename
    except Exception as e:
        print(f"Error downloading {file_url}: {e}")
        return None


def save_page_content_and_pdf(page, url):
    """Save the page content as HTML and PDF."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

    # Save as HTML
    html_filename = os.path.join(OUTPUT_DIR, f"{url.replace('/', '_').replace(':', '')}.html")
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(page.content())
    print(f"Page content saved as HTML: {html_filename}")

    # Save as PDF
    pdf_filename = os.path.join(PDF_OUTPUT_DIR, f"{url.replace('/', '_').replace(':', '')}.pdf")
    page.pdf(
        path=pdf_filename,
        format="A3",
        print_background=True,
        margin={"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"}
    )
    print(f"Page content saved as PDF: {pdf_filename}")
    return pdf_filename


def extract_links_and_assets(page, url):
    """Extract all links, images, and downloadable files from the page."""
    links = page.evaluate("""Array.from(document.querySelectorAll('a[href]')).map(a => a.href);""")
    images = page.evaluate("""Array.from(document.querySelectorAll('img[src]')).map(img => img.src);""")
    downloads = [
        link for link in links
        if link.lower().endswith(('.pdf', '.ppt', '.pptx', '.potx', '.docx'))
    ]

    # Convert relative URLs to absolute URLs
    links = [urljoin(url, link) for link in links]
    images = [urljoin(url, img) for img in images]
    downloads = [urljoin(url, dl) for dl in downloads]

    return links, images, downloads



def handle_downloads(page):
    """Find and click buttons to download files."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    file_extensions = [".pdf", ".ppt", ".pptx", ".potx", ".docx"]

    buttons = page.query_selector_all("button, div, a")

    for button in buttons:
        try:
            aria_label = button.get_attribute("aria-label")
            role = button.get_attribute("role")
            data_testid = button.get_attribute("data-testid")
            button_type = button.get_attribute("type")

            if (
                aria_label
                and any(aria_label.lower().endswith(ext) for ext in file_extensions)
                and role == "button"
                and data_testid == "download-file-text-button"
                and button_type == "button"
            ):
                print(f"Found download button for file: {aria_label}")

                with page.expect_download() as download_info:
                    button.click()
                download = download_info.value

                save_path = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
                download.save_as(save_path)
                print(f"Downloaded: {save_path}")

                scrap_summary[-1]["downloadable_file_list"].append(save_path)

        except Exception as e:
            print(f"Error clicking button or downloading: {e}")


def scrape_site(page, start_url, base_url, skip_links: set, limit=None):
    """Recursively scrape all links on the website."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    to_visit = [start_url]
    visited = set(skip_links)
    count = 0

    print(f"Starting from URL: {start_url}")
    print(f"Base URL: {base_url}")
    print(f"Scraping limit: {limit}")
    print(f"Skip links count: {len(skip_links)}")

    while to_visit:
        if limit and count >= limit:
            print(f"Visited limit of {limit} pages reached. Stopping.")
            break

        current_url = to_visit.pop(0)
        if current_url in visited or any(keyword in current_url.lower() for keyword in SIGNOUT_KEYWORDS):
            print(f"Skipping already visited URL: {current_url}")
            continue

        print(f"Scraping: {current_url}")
        try:
            page.goto(current_url)
            page.wait_for_load_state("networkidle")

            # Save page content and PDF
            pdf_path = save_page_content_and_pdf(page, current_url)
            child_links, images, downloads = extract_links_and_assets(page, current_url)

            print(f"Extracted {len(child_links)} child links from {current_url}.")

            # Download assets
            [download_file(img, IMAGE_DIR) for img in images]
            [download_file(dl, DOWNLOAD_DIR) for dl in downloads]

            # Save scrap summary
            scrap_summary.append(
                {
                    "visited_page_id": len(scrap_summary) + 1,
                    "visited_page_link": current_url,
                    "parent_page_link": start_url,
                    "child_web_links": child_links,
                    "saved_as": pdf_path,
                }
            )

            # Add child links to the queue
            for link in child_links:
                if link.startswith(base_url) and link not in visited:
                    to_visit.append(link)

            visited.add(current_url)
            visited_links.append({"page_id": len(visited_links) + 1, "page_link": current_url, "saved_as": pdf_path})
            count += 1

            print(f"Scraped {count}/{limit} pages so far.")

        except Exception as e:
            print(f"Error scraping {current_url}: {e}")

    print("Scraping completed!")
    print(f"Total pages scraped: {count}")
    return visited, scrap_summary



def main(skip_links=None, limit=None, start_url=None):
    from authenticator import login_to_verizon
    selenium_cookies = login_to_verizon()
    playwright_cookies = transfer_cookies_to_playwright(selenium_cookies)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_cookies(playwright_cookies)
        page = context.new_page()

        try:
            print("Starting recursive scraping...")
            new_links = scrape_site(page, start_url, skip_links, limit)
            return new_links
        finally:
            save_visited_links()
            browser.close()


if __name__ == "__main__":
    main()
