import os
import glob

from scraper_playwright_w_pdf import main as scraper
from convert_to_pdf import main as converter
from parse_text_urls import main as parser
from map_metadata import main as mapper
from ingest_to_neo4j import ingest_data_to_neo4j

LIMIT = 50
MOST_RECENT_VISITED = max(glob.glob("../data/visited_links_*.txt"), key=os.path.getctime)

def main():
    print("Starting the pipeline...")
    scraper(limit=LIMIT, skip_links=MOST_RECENT_VISITED)
    converter()
    parser()
    mapper()
    ingest_data_to_neo4j("../data/mapped_metadata.json")
    print("Pipeline completed!")

if __name__ == "__main__":
    main()
