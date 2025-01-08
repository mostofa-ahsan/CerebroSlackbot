import os
import json
import datetime
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

DATA_DIR = "../data"
OUTPUT_DIR = os.path.join(DATA_DIR, "scraped_pages")
PDF_OUTPUT_DIR = os.path.join(DATA_DIR, "pages_as_pdf")
DOWNLOAD_DIR = os.path.join(DATA_DIR, "downloads")
IMAGE_DIR = os.path.join(DATA_DIR, "saved_images")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress_summary.json")
SIGNOUT_KEYWORDS = ["signout", "logout", "print"]

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)


def load_progress_file(file_path):
    """Load progress summary from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []


def save_progress_file(data, file_path):
    """Save progress to the progress summary file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Progress saved to {file_path}")


def save_page_content(page, url):
    """Save page content as HTML and PDF."""
    html_filename = os.path.join(OUTPUT_DIR, f"{url.replace('/', '_').replace(':', '')}.html")
    pdf_filename = os.path.join(PDF_OUTPUT_DIR, f"{url.replace('/', '_').replace(':', '')}.pdf")
    
    # Save HTML
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(page.content())
    print(f"Saved HTML: {html_filename}")
    
    # Save PDF
    page.pdf(path=pdf_filename, format="A4", print_background=True)
    print(f"Saved PDF: {pdf_filename}")
    return html_filename, pdf_filename

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
    playwright_cookies = [
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

    # Apply cookies to the context
    context.add_cookies(playwright_cookies)

    # Create a new page
    page = context.new_page()
    return context, page


def scrape_site(page, start_url, base_url, progress_data, limit, last_page_id):
    """Scrape the site recursively and update progress summary."""
    to_visit = [start_url]
    visited = {entry["page_link"] for entry in progress_data}
    count = 0

    print(f"Starting from URL: {start_url}")
    print(f"Base URL: {base_url}")
    print(f"Scraping limit: {limit}")
    print(f"Skip links count: {len(visited)}")

    while to_visit:
        if limit and count >= limit:
            print(f"Visited limit of {limit} pages reached. Stopping.")
            break

        current_url = to_visit.pop(0)
        
        # Allow scraping the start_url even if it is in visited
        if current_url != start_url and (current_url in visited or any(keyword in current_url.lower() for keyword in SIGNOUT_KEYWORDS)):
            print(f"Skipping URL: {current_url}")
            continue

        try:
            print(f"Scraping: {current_url}")
            page.goto(current_url)
            page.wait_for_load_state("networkidle")

            saved_as_html, saved_as_pdf = save_page_content(page, current_url)

            child_links = page.evaluate("Array.from(document.querySelectorAll('a[href]')).map(a => a.href);")
            child_links = [urljoin(base_url, link) for link in child_links if link.startswith(base_url)]

            progress_data.append({
                "page_id": last_page_id + count + 1,
                "timestamp": datetime.datetime.now().isoformat(),
                "page_link": current_url,
                "saved_as_pdf": saved_as_pdf,
                "saved_as_html": saved_as_html,
                "child_pages": child_links,
                "parent_pages": [start_url],
                "download_list": [],
                "saved_images_list": [],
            })

            visited.add(current_url)
            to_visit.extend(link for link in child_links if link not in visited)
            count += 1
            print(f"Scraped {count}/{limit} pages so far.")

        except Exception as e:
            print(f"Error scraping {current_url}: {e}")
            continue

    print("Scraping completed!")
    return progress_data
