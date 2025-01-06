import os
import json
import atexit
import datetime
from playwright.sync_api import sync_playwright

BASE_URL = "https://brandcentral.verizonwireless.com"
OUTPUT_DIR = "../data/scraped_pages"
PDF_OUTPUT_DIR = "../data/pages_as_pdf"
SIGNOUT_KEYWORDS = ["signout", "logout", "print"]

# Add a timestamp to the visited links file
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
VISITED_LINKS_FILE = f"visited_links_{timestamp}.txt"

visited_links = set()  # Set to track visited links


def save_visited_links():
    """Save visited links to a file."""
    with open(VISITED_LINKS_FILE, "w") as f:
        for link in visited_links:
            f.write(link + "\n")
    print(f"Visited links saved to {VISITED_LINKS_FILE}")


# Register the save_visited_links function to run on exit
atexit.register(save_visited_links)


def transfer_cookies_to_playwright(selenium_cookies):
    """Convert Selenium cookies to Playwright cookies."""
    playwright_cookies = []
    for cookie in selenium_cookies:
        playwright_cookies.append({
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": cookie["domain"],
            "path": cookie["path"],
            "expires": cookie.get("expiry"),
            "httpOnly": cookie.get("httpOnly", False),
            "secure": cookie.get("secure", False),
            "sameSite": cookie.get("sameSite", "None")
        })
    return playwright_cookies


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
        format="A3",  # Larger format for more content
        print_background=True,
        margin={"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"}
    )
    print(f"Page content saved as PDF: {pdf_filename}")


def extract_links(page):
    """Extract all links from the current page."""
    links = page.evaluate(
        """Array.from(document.querySelectorAll('a[href]')).map(a => a.href);"""
    )
    return links


def scrape_site(page, start_url):
    """Recursively scrape all links on the website."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    to_visit = [start_url]

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited_links or any(keyword in current_url.lower() for keyword in SIGNOUT_KEYWORDS):
            continue

        print(f"Scraping: {current_url}")
        try:
            page.goto(current_url)
            page.wait_for_load_state("networkidle")

            # Save page content and PDF
            save_page_content_and_pdf(page, current_url)

            # Extract and queue new links
            links = extract_links(page)
            for link in links:
                if link.startswith(BASE_URL) and link not in visited_links:
                    to_visit.append(link)

            visited_links.add(current_url)

        except Exception as e:
            print(f"Error scraping {current_url}: {e}")

    print("Scraping completed!")


def main():
    # Authenticate with Selenium and extract cookies
    from authenticator import login_to_verizon
    selenium_cookies = login_to_verizon()
    playwright_cookies = transfer_cookies_to_playwright(selenium_cookies)

    # Use Playwright for scraping
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_cookies(playwright_cookies)
        page = context.new_page()

        print("Starting recursive scraping...")
        try:
            scrape_site(page, BASE_URL)
        except KeyboardInterrupt:
            print("Process interrupted! Saving visited links...")
        finally:
            save_visited_links()
            browser.close()


if __name__ == "__main__":
    main()
