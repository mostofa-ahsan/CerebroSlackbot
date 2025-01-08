import os
import glob
import json
from datetime import datetime
from scraper_playwright_w_pdf import scrape_site, create_playwright_context
from authenticator import login_to_verizon
from map_metadata import map_metadata
from ingest_to_neo4j import ingest_data_to_neo4j
from pdf_parser import parse_pdfs
from chunking import chunk_parsed_data
from embedding import embed_chunks
from indexer import create_index

# Configuration
LIMIT = 5  # Limit on the number of pages to scrape in each run
DATA_DIR = "../data"
PAGES_AS_PDF_DIR = os.path.join(DATA_DIR, "pages_as_pdf")
CONVERTED_DOWNLOADS_DIR = os.path.join(DATA_DIR, "converted_downloads")
PARSED_DIR = os.path.join(DATA_DIR, "parsed_text_files")
CHUNKED_DIR = os.path.join(DATA_DIR, "chunked_text_files")
EMBEDDING_DIR = os.path.join(DATA_DIR, "embeddings")
INDEX_DIR = os.path.join(DATA_DIR, "indexes")
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

os.makedirs(PARSED_DIR, exist_ok=True)
os.makedirs(CHUNKED_DIR, exist_ok=True)
os.makedirs(EMBEDDING_DIR, exist_ok=True)
os.makedirs(INDEX_DIR, exist_ok=True)


def get_most_recent_file(pattern):
    """Get the most recent file matching a pattern."""
    files = glob.glob(pattern)
    return max(files, key=os.path.getctime) if files else None


def load_visited_links(file_path):
    """Load visited links from a JSON file into a list."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return data, max([entry["page_id"] for entry in data]) if data else 0
    except FileNotFoundError:
        return [], 0


def save_visited_links(visited_links, file_path):
    """Save visited links to a JSON file."""
    with open(file_path, "w") as f:
        json.dump(visited_links, f, indent=4)
    print(f"Visited links saved to {file_path}")


def combine_scrap_summaries(files, output_file):
    """Combine multiple scrap_summary JSON files into one."""
    combined = []
    for file in files:
        try:
            with open(file, "r") as f:
                combined.extend(json.load(f))
        except Exception as e:
            print(f"Error reading {file}: {e}")

    with open(output_file, "w") as f:
        json.dump(combined, f, indent=4)
    print(f"Combined scrap summary saved to {output_file}")


def save_data_to_file(data, file_path):
    """Save data to a JSON file."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Data saved to {file_path}")
    except Exception as e:
        print(f"Error saving data to {file_path}: {e}")


def main():
    print("##############################################")
    print("Starting the pipeline...")

    BASE_URL = "https://brandcentral.verizonwireless.com"  # Define the base URL
    LIMIT = 10  # Limit on the number of pages to scrape in each run

    # Step 1: Detect the most recent visited_links file
    visited_links_files = glob.glob(os.path.join(DATA_DIR, "visited_links_*.json"))
    previous_links_set = set()
    last_visited_link = BASE_URL
    previous_links = []
    last_page_id = 0

    if visited_links_files:
        most_recent_visited_file = max(visited_links_files, key=os.path.getctime)
        print(f"Most recent visited links file: {most_recent_visited_file}")
        previous_links, last_page_id = load_visited_links(most_recent_visited_file)
        previous_links_set = {entry["page_link"] for entry in previous_links}
        last_visited_link = previous_links[-1]["page_link"] if previous_links else BASE_URL

        # Exclude last_visited_link from the skip list
        if last_visited_link:
            previous_links_set.discard(last_visited_link)

        print(f"Last visited link: {last_visited_link}")
    else:
        print("No visited links file found. Starting fresh.")

    # Step 2: Authenticate and get Selenium cookies
    from authenticator import login_to_verizon
    selenium_cookies = login_to_verizon()

    # Step 3: Create Playwright context with cookies
    from scraper_playwright_w_pdf import scrape_site, create_playwright_context
    context, page = create_playwright_context(selenium_cookies)

    try:
        # Step 4: Run the scraper
        print(f"Scraping with limit: {LIMIT}")
        print(f"Starting recursive scraping from {last_visited_link}")
        new_links, scrap_summary_data = scrape_site(
            page=page,
            start_url=last_visited_link,
            base_url=BASE_URL,
            skip_links=previous_links_set,
            limit=LIMIT,
        )
    finally:
        context.close()

    # Step 5: Update visited links
    new_visited_links = [
        {
            "page_id": last_page_id + idx + 1,
            "timestamp": datetime.now().isoformat(),
            "page_link": link,
            "saved_as": os.path.join(
                os.path.normpath(PAGES_AS_PDF_DIR),
                f"{link.replace('/', '_').replace(':', '').replace('.', '_')}.pdf",
            ).replace("\\", "/"),
        }
        for idx, link in enumerate(new_links)
    ]

    combined_visited_links = previous_links + new_visited_links
    visited_links_file_path = os.path.join(
        DATA_DIR, f"visited_links_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    save_visited_links(combined_visited_links, visited_links_file_path)

    # Step 6: Update scrap summaries
    scrap_summary_file_path = os.path.join(DATA_DIR, f"scrap_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    save_data_to_file(scrap_summary_data, scrap_summary_file_path)

    # Combine all scrap summaries
    scrap_summary_files = glob.glob(os.path.join(DATA_DIR, "scrap_summary_*.json"))
    combined_scrap_summary_file = os.path.join(DATA_DIR, "combined_scrap_summary.json")
    combine_scrap_summaries(scrap_summary_files, combined_scrap_summary_file)

    # Step 7: Parse PDFs
    print("Parsing PDF files...")
    parse_pdfs([PAGES_AS_PDF_DIR, CONVERTED_DOWNLOADS_DIR], PARSED_DIR)

    # Step 8: Chunk parsed data
    print("Chunking parsed data...")
    chunk_parsed_data(PARSED_DIR, CHUNKED_DIR)

    # Step 9: Embed chunks
    print("Embedding chunked data...")
    embed_chunks(CHUNKED_DIR, EMBEDDING_DIR)

    # Step 10: Create indexes
    print("Creating indexes...")
    create_index(EMBEDDING_DIR, INDEX_DIR)

    # Step 11: Map metadata
    print("Mapping metadata...")
    try:
        map_metadata()
    except Exception as e:
        print(f"Error during metadata mapping: {e}")

    # Step 12: Ingest data into Neo4j
    print("Ingesting data to Neo4j...")
    mapped_metadata_path = os.path.join(DATA_DIR, "mapped_metadata.json")
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
