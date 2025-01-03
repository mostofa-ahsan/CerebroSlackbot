import os
import json
from playwright.sync_api import sync_playwright
from authenticator import login_to_verizon  # Import the existing function

BASE_URL = "https://brandcentral.verizonwireless.com"
OUTPUT_DIR = "./scraped_pages"
SIGNOUT_KEYWORDS = ["signout", "logout"]


def get_cookies_from_selenium():
    """Authenticate using the existing Selenium-based authenticator and extract cookies."""
    print("Authenticating with Selenium...")
    cookies = login_to_verizon()
    if not cookies:
        raise ValueError("No cookies retrieved after authentication. Please check the login process.")
    print("Retrieved cookies:", cookies)
    return cookies




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


def save_page_content(page, url):
    """Save the page content."""
    filename = os.path.join(OUTPUT_DIR, f"{url.replace('/', '_').replace(':', '')}.html")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(page.content())
    print(f"Page content saved: {filename}")


def extract_links(page):
    """Extract all links from the current page."""
    links = page.evaluate(
        """Array.from(document.querySelectorAll('a[href]')).map(a => a.href);"""
    )
    return links


def scrape_site(page, start_url):
    """Recursively scrape all links on the website."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    to_visit = [start_url]
    visited = set()

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited or any(keyword in current_url.lower() for keyword in SIGNOUT_KEYWORDS):
            continue

        print(f"Scraping: {current_url}")
        try:
            page.goto(current_url)
            page.wait_for_load_state("networkidle")

            # Save page content
            save_page_content(page, current_url)

            # Extract and queue new links
            links = extract_links(page)
            for link in links:
                if link.startswith(BASE_URL) and link not in visited:
                    to_visit.append(link)

            visited.add(current_url)

        except Exception as e:
            print(f"Error scraping {current_url}: {e}")

    print("Scraping completed!")


def main():
    # Authenticate with Selenium and extract cookies
    selenium_cookies = get_cookies_from_selenium()
    playwright_cookies = transfer_cookies_to_playwright(selenium_cookies)

    # Use Playwright for scraping
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_cookies(playwright_cookies)
        page = context.new_page()

        print("Starting recursive scraping...")
        scrape_site(page, BASE_URL)

        browser.close()


if __name__ == "__main__":
    main()
