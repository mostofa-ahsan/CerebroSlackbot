import os
import json
from scraper_vds import scrape_site, load_progress_file, save_progress_file
from convert_to_pdf_vds import convert_to_pdf
from authenticator import login_to_verizon_with_playwright
from ingest_to_cerebro_collection_VDS_v2 import ingest_to_cerebro_vds, extract_text_from_pdf, chunk_text
from initialize_chroma_db_v2 import initialize_chroma_db
from query_cerebro_chromadb_v2 import query_cerebro_v3

# Configuration
LIMIT = 500  # Limit on the number of pages to scrape in each run
DATA_DIR = "../../data/"
CHROMA_DB_DIR = os.path.join(DATA_DIR, "cerebro_chroma_db_v2")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress_summary_vds_v2.json")
PAGES_AS_PDF_DIR = os.path.join(DATA_DIR, "pages_as_pdf_test")
DOWNLOAD_DIR = os.path.join(DATA_DIR, "downloads_test")
CONVERTED_DIR = os.path.join(DATA_DIR, "converted_downloads_test")


COLLECTION_NAME = "cerebro_vds_v2"
PDF_FOLDERS = ["../../data/converted_downloads_test", "../../data/pages_as_pdf_test"]
CHUNK_SIZE = 1000  # Adjust chunk size as needed
LOCAL_MODEL_PATH = "../../models/all-mpnet-base-v2"  # Path to the locally downloaded model



os.makedirs(PAGES_AS_PDF_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(CONVERTED_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# Check if PROGRESS_FILE exists, if not create a sample file with provided data
if not os.path.exists(PROGRESS_FILE):
    sample_data = [
        {
            "page_id": 1,
            "page_link": "https://designsystem.verizon.com",
            "saved_as_pdf": "../data/pages_as_pdf_1/https__designsystem.verizon.com.pdf",
            "saved_as_html": "../data/scraped_pages_1/https__designsystem.verizon.com.html",
            "child_pages": [
                "https://designsystem.verizon.com/getting-started/introduction",
                "https://designsystem.verizon.com/components/component-status",
                "https://designsystem.verizon.com/support/whats-new/release-history",
                "https://designsystem.verizon.com/blog/monarch-updates/monarch-updates-november",
                "https://designsystem-storybook.verizon.com/",
                "https://designsystem.verizon.com/getting-started/introduction",
                "https://designsystem.verizon.com/components/component-status",
                "https://designsystem.verizon.com/support/whats-new/release-history"
            ],
            "parent_pages": [
                "https://designsystem.verizon.com"
            ],
            "download_list": [],
            "saved_images_list": []
        }
    ]
    with open(PROGRESS_FILE, 'w') as file:
        json.dump(sample_data, file, indent=4)
    print(f"Sample progress file created at {PROGRESS_FILE}")


def main():
    # print("##############################################")
    # print("Starting the pipeline...")
    # BASE_URL = "https://designsystem.verizon.com"
    # # BASE_URL = "https://brandcentral.verizonwireless.com"

    # # Step 1: Load progress summary
    # progress_data = load_progress_file(PROGRESS_FILE)
    # last_page_id = progress_data[-1]["page_id"] if progress_data else 0

    # # Step 2: Authenticate using Playwright and start scraping
    # from playwright.sync_api import sync_playwright
    # with sync_playwright() as playwright:
    #     context, page = login_to_verizon_with_playwright(playwright)
    #     if not context or not page:
    #         print("Authentication failed. Exiting pipeline.")
    #         return

    #     try:
    #         # Step 3: Start scraping
    #         print(f"Scraping with limit: {LIMIT}")
    #         progress_data = scrape_site(
    #             page=page,
    #             start_url=BASE_URL,
    #             base_url=BASE_URL,
    #             progress_data=progress_data,
    #             limit=LIMIT,
    #             last_page_id=last_page_id,
    #         )
    #     finally:
    #         # Ensure context is closed
    #         context.close()

    # # Step 4: Save updated progress summary
    # save_progress_file(progress_data, PROGRESS_FILE)

    # # Step 5: Convert scraped pages to PDF
    # convert_to_pdf(DOWNLOAD_DIR, CONVERTED_DIR)


    # Step 6: Initilize ChromaDB [For the first time]
    initialize_chroma_db(CHROMA_DB_DIR)


    # Step 7: Ingest data into ChromaDB
    ingest_to_cerebro_vds()


    # Test ChromaDB Query
    query_cerebro_v3()

    print("##############################################")
    print("Pipeline execution completed.")


if __name__ == "__main__":
    main()
