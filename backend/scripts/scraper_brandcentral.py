import os
import json
import requests
from urllib.parse import urljoin, urlparse
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


def handle_downloads(page, progress_entry):
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

                progress_entry["download_list"].append(save_path)

        except Exception as e:
            print(f"Error clicking button or downloading: {e}")


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
            child_links, images, downloads = extract_links_and_assets(page, current_url)

            print(f"Extracted {len(child_links)} child links from {current_url}.")

            # Download assets
            downloaded_files = [download_file(dl, DOWNLOAD_DIR) for dl in downloads]
            saved_images = [download_file(img, IMAGE_DIR) for img in images]

            progress_entry = {
                "page_id": last_page_id + count + 1,
                "page_link": current_url,
                "saved_as_pdf": saved_as_pdf,
                "saved_as_html": saved_as_html,
                "child_pages": child_links,
                "parent_pages": [start_url],
                "download_list": downloaded_files,
                "saved_images_list": saved_images,
            }

            handle_downloads(page, progress_entry)

            progress_data.append(progress_entry)
            visited.add(current_url)
            to_visit.extend(link for link in child_links if link not in visited)
            count += 1

            # Save intermediate progress after each page
            save_progress_file(progress_data, PROGRESS_FILE)

            print(f"Scraped {count}/{limit} pages so far.")

        except Exception as e:
            print(f"Error scraping {current_url}: {e}")
            continue

    print("Scraping completed!")
    return progress_data
