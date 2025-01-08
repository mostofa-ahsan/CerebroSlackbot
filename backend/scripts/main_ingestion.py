import os
from scraper_brandcentral import scrape_site, load_progress_file, save_progress_file
from authenticator import login_to_verizon_with_playwright
from pdf_parser import parse_pdfs
from chunking import chunk_parsed_data
from embedding import embed_chunks
from indexer import create_index
from map_metadata import map_metadata
from ingest_to_neo4j import ingest_data_to_neo4j

# Configuration
LIMIT = 3  # Limit on the number of pages to scrape in each run
DATA_DIR = "../data"
PROGRESS_FILE = os.path.join(DATA_DIR, "progress_summary.json")
PAGES_AS_PDF_DIR = os.path.join(DATA_DIR, "pages_as_pdf")
PARSED_DIR = os.path.join(DATA_DIR, "parsed_text_files")
CHUNKED_DIR = os.path.join(DATA_DIR, "chunked_text_files")
EMBEDDING_DIR = os.path.join(DATA_DIR, "embeddings")
INDEX_DIR = os.path.join(DATA_DIR, "indexes")
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

os.makedirs(PAGES_AS_PDF_DIR, exist_ok=True)
os.makedirs(PARSED_DIR, exist_ok=True)
os.makedirs(CHUNKED_DIR, exist_ok=True)
os.makedirs(EMBEDDING_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)


def main():
    print("##############################################")
    print("Starting the pipeline...")

    BASE_URL = "https://brandcentral.verizonwireless.com"

    # Step 1: Load progress summary
    progress_data = load_progress_file(PROGRESS_FILE)
    last_page_id = progress_data[-1]["page_id"] if progress_data else 0

    # Step 2: Authenticate using Playwright and start scraping
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        context, page = login_to_verizon_with_playwright(playwright)
        if not context or not page:
            print("Authentication failed. Exiting pipeline.")
            return

        try:
            # Step 3: Start scraping
            print(f"Scraping with limit: {LIMIT}")
            progress_data = scrape_site(
                page=page,
                start_url=BASE_URL,
                base_url=BASE_URL,
                progress_data=progress_data,
                limit=LIMIT,
                last_page_id=last_page_id,
            )
        finally:
            # Ensure context is closed
            context.close()

    # Step 4: Save updated progress summary
    save_progress_file(progress_data, PROGRESS_FILE)

    # Step 5: Parse PDFs
    print("Parsing PDF files...")
    parse_pdfs([PAGES_AS_PDF_DIR], PARSED_DIR)

    # Step 6: Chunk parsed data
    print("Chunking parsed data...")
    chunk_parsed_data(PARSED_DIR, CHUNKED_DIR)

    # Step 7: Embed chunks
    print("Embedding chunked data...")
    embed_chunks(CHUNKED_DIR, EMBEDDING_DIR)

    # Step 8: Create indexes
    print("Creating indexes...")
    create_index(EMBEDDING_DIR, INDEX_DIR)

    # Step 9: Map metadata
    print("Mapping metadata...")
    try:
        mapped_metadata_path = os.path.join(DATA_DIR, "mapped_metadata.json")
        map_metadata(
            progress_file=PROGRESS_FILE,
            mapped_metadata_file=mapped_metadata_path,
            index_dir=INDEX_DIR,
            embedding_dir=EMBEDDING_DIR,
        )
    except Exception as e:
        print(f"Error during metadata mapping: {e}")


    # Step 10: Ingest data into Neo4j
    print("Ingesting data to Neo4j...")
    mapped_metadata_path = os.path.normpath(os.path.join(DATA_DIR, "mapped_metadata.json"))
    if os.path.exists(mapped_metadata_path):
        try:
            ingest_data_to_neo4j(mapped_metadata_path, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        except Exception as e:
            print(f"Error during Neo4j ingestion: {e}")
    else:
        print(f"Error: {mapped_metadata_path} not found. Ensure map_metadata.py ran successfully.")


    print("##############################################")
    print("Pipeline execution completed.")


if __name__ == "__main__":
    main()
