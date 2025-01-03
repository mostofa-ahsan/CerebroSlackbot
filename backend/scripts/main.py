import os
from scripts.scraper import scrape_website
from scripts.parser import parse_html, parse_pdf
from scripts.ocr import ocr_image
from scripts.chunker import chunk_text
from scripts.tagger import tag_chunks
from scripts.indexer import create_index

def main():
    # Step 1: Scrape
    scrape_website("https://brandcentral.verizon.wireless.com", "../data/scraped_pages")
    
    # Step 2: Parse
    parsed_texts = []
    for file in os.listdir("../data/scraped_pages"):
        if file.endswith(".html"):
            parsed_texts.append(parse_html(f"../data/scraped_pages/{file}"))
        elif file.endswith(".pdf"):
            parsed_texts.append(parse_pdf(f"../data/scraped_pages/{file}"))
    
    # Step 3: OCR
    for file in os.listdir("../data/ocr_images"):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            parsed_texts.append(ocr_image(f"../data/ocr_images/{file}"))
    
    # Step 4: Chunk
    all_chunks = [chunk_text(text) for text in parsed_texts]
    flattened_chunks = [chunk for sublist in all_chunks for chunk in sublist]

    # Step 5: Tag
    tagged_chunks = tag_chunks(flattened_chunks)

    # Step 6: Index
    index = create_index(flattened_chunks)
    print("Index created and tagged successfully.")

if __name__ == "__main__":
    main()
