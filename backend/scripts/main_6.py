import os
import glob
import json
from datetime import datetime
from scraper_playwright_w_pdf import main as scraper
from map_metadata import map_metadata
from ingest_to_neo4j import ingest_data_to_neo4j
from pdf_parser import parse_pdfs
from chunking import chunk_parsed_data
from embedding import embed_chunks
from indexer import create_index

# Configuration
LIMIT = 10  # Limit on the number of pages to scrape in each run
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


def load_links_from_file(file_path):
    """Load links from a file into a set."""
    try:
        with open(file_path, "r") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


def save_links_to_file(links, file_path):
    """Save a set of links to a file."""
    with open(file_path, "w") as f:
        for link in sorted(links):
            f.write(f"{link}\n")


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


def main():
    print("##############################################")
    print("Starting the pipeline...")

    # Step 1: Detect the most recent visited_links file
    visited_links_files = glob.glob(os.path.join(DATA_DIR, "visited_links_*.txt"))
    if visited_links_files:
        most_recent_visited_file = max(visited_links_files, key=os.path.getctime)
        print(f"Most recent visited links file: {most_recent_visited_file}")
        previous_links = load_links_from_file(most_recent_visited_file)
        last_link = list(previous_links)[-1]
        print(f"Last visited link: {last_link}")
    else:
        print("No visited links file found. Starting fresh.")
        previous_links = set()
        last_link = None

    # Step 2: Run the scraper
    print(f"Scraping with limit: {LIMIT}")
    new_links = scraper(skip_links=set(previous_links[:-1]), limit=LIMIT, start_url=last_link)

    # Step 3: Combine the visited links
    combined_visited_links_file = os.path.join(
        DATA_DIR, f"visited_links_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    combined_links = previous_links.union(new_links)
    save_links_to_file(combined_links, combined_visited_links_file)
    print(f"Combined visited links saved to {combined_visited_links_file}")
    print(f"Total visited links so far: {len(combined_links)}")

    # Step 4: Combine scrap summaries
    scrap_summary_files = glob.glob(os.path.join(DATA_DIR, "scrap_summary_*.json"))
    combined_scrap_summary_file = os.path.join(DATA_DIR, "combined_scrap_summary.json")
    combine_scrap_summaries(scrap_summary_files, combined_scrap_summary_file)
    print(f"Combined scrap summary saved to {combined_scrap_summary_file}")

    # Step 5: Parse PDFs
    print("Parsing PDF files...")
    parse_pdfs([PAGES_AS_PDF_DIR, CONVERTED_DOWNLOADS_DIR], PARSED_DIR)

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
        map_metadata()
    except Exception as e:
        print(f"Error during metadata mapping: {e}")

    # Step 10: Ingest data into Neo4j
    print("Ingesting data to Neo4j...")
    mapped_metadata_path = os.path.join(DATA_DIR, "mapped_metadata.json")
    if os.path.exists(mapped_metadata_path):
        try:
            ingest_data_to_neo4j(CHUNKED_DIR, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        except Exception as e:
            print(f"Error during Neo4j ingestion: {e}")
    else:
        print(f"Error: {mapped_metadata_path} not found. Ensure map_metadata.py ran successfully.")

    print("##############################################")
    print("Pipeline execution completed.")


if __name__ == "__main__":
    main()
