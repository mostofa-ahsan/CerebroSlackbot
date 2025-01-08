import os
import json
import pdfplumber

INPUT_DIRS = ["../data/pages_as_pdf", "../data/converted_downloads"]

PARSED_TEXT_DIR = "../data/parsed_text_plain"

# Ensure output directories exist

os.makedirs(PARSED_TEXT_DIR, exist_ok=True)

def extract_text_and_links(pdf_path):
    """
    Extract text and hyperlinks from a PDF.
    
    Args:
        pdf_path (str): Path to the PDF file.
    
    Returns:
        tuple: A list of parsed data (JSON format) and plain text content.
    """
    parsed_data = []
    plain_text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                links = []

                # Attempt to extract links if annotations are available
                try:
                    annotations = getattr(page, "annotations", [])
                    for annotation in annotations:
                        if annotation.get("uri"):
                            links.append(annotation["uri"])
                except AttributeError:
                    print(f"No annotations found on page {page_num + 1} in {pdf_path}. Skipping links extraction.")
                
                parsed_data.append({
                    "page_number": page_num + 1,
                    "text": text.strip() if text else "",
                    "links": links,
                })

                # Append text content to plain text list with page numbers
                plain_text.append(f"Page {page_num + 1}:\n{text.strip() if text else ''}\n")
        return parsed_data, "\n".join(plain_text)
    except Exception as e:
        print(f"Error parsing {pdf_path}: {e}")
        return None, None

def parse_pdfs(input_dirs,  text_output_dir):
    """
    Parse PDFs from multiple directories and save extracted data.
    
    Args:
        input_dirs (list): List of directories containing PDF files.
        json_output_dir (str): Directory where parsed JSON files will be saved.
        text_output_dir (str): Directory where plain text files will be saved.
    """
    for input_dir in input_dirs:
        for pdf_file in os.listdir(input_dir):
            if pdf_file.endswith(".pdf"):
                pdf_path = os.path.join(input_dir, pdf_file)
                print(f"Parsing {pdf_path}...")
                parsed_data, plain_text = extract_text_and_links(pdf_path)
                
                
                if plain_text:
                    # Save plain text output
                    text_output_file = os.path.join(text_output_dir, f"{os.path.splitext(pdf_file)[0]}.txt")
                    with open(text_output_file, "w", encoding="utf-8") as f:
                        f.write(plain_text)
                    print(f"Plain text data saved to {text_output_file}")

if __name__ == "__main__":
    parse_pdfs(INPUT_DIRS,  PARSED_TEXT_DIR)
