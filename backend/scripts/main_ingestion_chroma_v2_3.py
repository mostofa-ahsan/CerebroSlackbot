import os
import json
from scraper_vds import scrape_site, load_progress_file, save_progress_file
from convert_to_pdf_vds import convert_to_pdf
from authenticator import login_to_verizon_with_playwright
from ingest_to_cerebro_collection_VDS_v2 import extract_text_from_pdf, chunk_text, initialize_chroma_vectorstore, load_pdfs_from_folders
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


def ingest_documents_and_initialize_vectorstore():
    """
    Load PDFs, chunk documents, and initialize or update the ChromaDB vector store.
    """
    # Step 1: Load PDFs from folders
    print("Loading PDFs from folders...")
    documents = load_pdfs_from_folders(PDF_FOLDERS)

    if not documents:
        print("No documents found for ingestion. Exiting Step 7.")
        return

    # Step 2: Chunk the loaded documents
    print("Chunking documents...")
    chunked_documents = chunk_documents(documents)

    # Step 3: Initialize or update ChromaDB vector store
    print("Initializing or updating the Chroma vector store...")
    initialize_chroma_vectorstore(chunked_documents)

    print(f"Step 7 completed. Number of original documents: {len(documents)}")
    print(f"Number of chunks created: {len(chunked_documents)}")


def main():
    # Step 6: Initilize ChromaDB [For the first time]
    initialize_chroma_db(CHROMA_DB_DIR)

    # Step 7: Ingest data into ChromaDB
    ingest_documents_and_initialize_vectorstore()

    # Test ChromaDB Query
    query_cerebro_v3()

    print("##############################################")
    print("Pipeline execution completed.")


if __name__ == "__main__":
    main()
