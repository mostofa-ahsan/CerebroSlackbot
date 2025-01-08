import os
import json
import pdfplumber
from urllib.parse import urljoin

INPUT_DIRS = ["../data/pages_as_pdf", "../data/converted_downloads"]
OUTPUT_DIR = "../data/parsed_text_files"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_text_and_links(pdf_path):
    """Extract text and hyperlinks from a PDF."""
    parsed_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                links = []
                for annotation in page.annotations:
                    if annotation.get("uri"):
                        links.append(annotation["uri"])
                
                parsed_data.append({
                    "page_number": page_num + 1,
                    "text": text.strip() if text else "",
                    "links": links,
                })
        return parsed_data
    except Exception as e:
        print(f"Error parsing {pdf_path}: {e}")
        return None

def parse_pdfs(input_dirs, output_dir):
    """Parse PDFs from multiple directories and save extracted data."""
    for input_dir in input_dirs:
        for pdf_file in os.listdir(input_dir):
            if pdf_file.endswith(".pdf"):
                pdf_path = os.path.join(input_dir, pdf_file)
                print(f"Parsing {pdf_path}...")
                parsed_data = extract_text_and_links(pdf_path)
                
                if parsed_data:
                    output_file = os.path.join(output_dir, f"{os.path.splitext(pdf_file)[0]}.json")
                    with open(output_file, "w") as f:
                        json.dump(parsed_data, f, indent=4)
                    print(f"Parsed data saved to {output_file}")

if __name__ == "__main__":
    parse_pdfs(INPUT_DIRS, OUTPUT_DIR)
