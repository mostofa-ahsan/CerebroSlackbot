import os
import glob
from scripts.scraper import scrape_website
from scripts.parser import parse_all
from scripts.chunker import chunk_text, chunk_all
from scripts.indexer import create_index

BASE_URL = "https://brandcentral.verizon.wireless.com"
SCRAPED_DIR = "./scraped_pages"
PARSED_DIR = "./parsed_pages"
CHUNKED_DIR = "./chunked_pages"
INDEX_PATH = "./faiss_index/index.faiss"

def process_website(scraped_dir, parsed_dir, chunked_dir, index_path):
    parse_all(scraped_dir, parsed_dir)
    chunk_all(parsed_dir, chunked_dir)
    
    # Combine all chunks into a single list
    all_chunks = []
    for file in glob.glob(f"{chunked_dir}/*.txt"):
        with open(file, "r", encoding="utf-8") as f:
            all_chunks.extend(f.read().split("

"))
    
    create_index(all_chunks, index_path)

if __name__ == "__main__":
    scrape_website(BASE_URL, SCRAPED_DIR)
    process_website(SCRAPED_DIR, PARSED_DIR, CHUNKED_DIR, INDEX_PATH)
