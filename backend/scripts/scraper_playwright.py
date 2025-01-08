import os
import json
import atexit
import datetime
from playwright.sync_api import sync_playwright

BASE_URL = "https://brandcentral.verizonwireless.com"
OUTPUT_DIR = "../data/scraped_pages"
PDF_OUTPUT_DIR = "../data/pages_as_pdf"
DOWNLOAD_DIR = "../data/downloads"
IMAGE_DIR = "../data/saved_images"
SIGNOUT_KEYWORDS = ["signout", "logout", "print"]

# Add a timestamp to the visited links file and summary JSON file
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
VISITED_LINKS_FILE = f"visited_links_{timestamp}.txt"
SCRAP_SUMMARY_FILE = f"scrap_summary_{timestamp}.json"

visited_links = set()  # Set to track visited links
scrap_summary = []  # List to hold page-wise details


def save_visited_links():
    """Save visited links and scrap summary to files."""
    with open(VISITED_LINKS_FILE, "w") as f:
        for link in visited_links:
            f.write(link + "\n")
    print(f"Visited links saved to {VISITED_LINKS_FILE}")

    with open(SCRAP_SUMMARY_FILE, "w") as f:
        json.dump(scrap_summary, f, indent=4)
    print(f"Scrap summary saved to {SCRAP_SUMMARY_FILE}")


# Register the save_visited_links function to run on exit
atexit.register(save_visited_links)


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

def handle_downloads(page):
    """Click buttons with 'download' attributes and intercept downloads."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Define selectors for buttons and anchors
    button_selectors = ["button", "a", "svg"]  # Add or adjust selectors as needed
    for selector in button_selectors:
        elements = page.query_selector_all(selector)

        for element in elements:
            try:
                # Initialize variables for attributes
                aria_label = element.get_attribute("aria-label")
                title = element.get_attribute("title")
                inner_text = None

                # Only call inner_text() if the element is an HTMLElement
                if selector in ["button", "a"]:  # HTMLElement types
                    inner_text = element.inner_text()

                # Check if the element is a download button
                if (
                    (aria_label and "download" in aria_label.lower()) or
                    (title and "download" in title.lower()) or
                    (inner_text and "download" in inner_text.lower())
                ):
                    print(f"Found download button: {aria_label or title or inner_text}")

                    # Intercept the download
                    with page.expect_download() as download_info:
                        element.click()  # Click the download button
                    download = download_info.value

                    # Save the downloaded file
                    save_path = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
                    download.save_as(save_path)
                    print(f"Downloaded: {save_path}")

                else:
                    print(f"Skipping non-download element: {aria_label or title or inner_text}")

            except Exception as e:
                print(f"Error clicking button or downloading: {e}")



def scrape_site(page, start_url):
    """Recursively scrape all links on the website."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    to_visit = [start_url]

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited_links or any(keyword in current_url.lower() for keyword in SIGNOUT_KEYWORDS):
            continue

        print(f"Scraping: {current_url}")
        try:
            # Try loading the page with increased timeout
            page.goto(current_url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_selector("body", timeout=30000)  # Wait for body element as a fallback

            # Save page content and PDF
            save_page_content_and_pdf(page, current_url)

            # Handle downloads
            handle_downloads(page)

            # Add to summary
            scrap_summary.append({
                "visited_page_id": len(scrap_summary) + 1,
                "visited_page_link": current_url,
                "parent_page_link": None,  # Add logic to track parent if needed
                "child_web_links": [],  # Optional: Extract child links
                "image_list": [],  # Optional: Extract images
                "downloadable_file_list": []  # Handled dynamically via download intercepts
            })

            visited_links.add(current_url)

        except Exception as e:
            print(f"Error scraping {current_url}: {e}")

    print("Scraping completed!")


def main():
    # Authenticate with Selenium and extract cookies
    from authenticator import login_to_verizon
    selenium_cookies = login_to_verizon()

    if selenium_cookies is None:
        print("Error: No cookies retrieved from authenticator. Exiting...")
        return

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
            print("Process interrupted! Saving visited links and summary...")
        finally:
            save_visited_links()
            browser.close()


if __name__ == "__main__":
    main()
