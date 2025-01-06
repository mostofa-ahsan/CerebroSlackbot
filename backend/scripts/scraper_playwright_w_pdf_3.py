import os
import json
import atexit
import datetime
from urllib.parse import urljoin, urlparse
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
            "sameSite": cookie.get("sameSite", "None")
        }
        for cookie in selenium_cookies
    ]


def download_files_from_buttons(page):
    """Click buttons with 'aria-label' containing file extensions to download files."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Find all elements with type="button" and aria-label containing file extensions
    file_extensions = [".pdf", ".ppt", ".pptx", ".potx", ".zip", ".png", ".mp4"]
    buttons = page.query_selector_all("button[aria-label]")

    for button in buttons:
        try:
            aria_label = button.get_attribute("aria-label")
            if aria_label and any(ext in aria_label.lower() for ext in file_extensions):
                print(f"Found download button: {aria_label}")

                # Intercept the download
                with page.expect_download() as download_info:
                    button.click()  # Click the button to trigger download
                download = download_info.value

                # Save the downloaded file
                save_path = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
                download.save_as(save_path)
                print(f"Downloaded: {save_path}")

        except Exception as e:
            print(f"Error clicking button or downloading: {e}")


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
            page.goto(current_url)
            page.wait_for_load_state("networkidle")

            # Save page content and PDF
            save_page_content_and_pdf(page, current_url)

            # Download files from buttons
            download_files_from_buttons(page)

            # Extract links to continue scraping
            child_links = page.evaluate(
                """Array.from(document.querySelectorAll('a[href]')).map(a => a.href);"""
            )
            child_links = [urljoin(current_url, link) for link in child_links]

            # Add to summary
            scrap_summary.append({
                "visited_page_id": len(scrap_summary) + 1,
                "visited_page_link": current_url,
                "parent_page_link": None,  # Add logic to track parent if needed
                "child_web_links": child_links,
                "image_list": [],  # Optional: Extract images if needed
                "downloadable_file_list": []  # Handled dynamically via download intercepts
            })

            # Add child links to the queue
            for link in child_links:
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
            print("Process interrupted! Saving visited links and summary...")
        finally:
            save_visited_links()
            browser.close()


if __name__ == "__main__":
    main()
