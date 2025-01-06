import os
import re
from PyPDF2 import PdfReader

PDF_DIRS = ["../data/pages_as_pdf", "../data/converted_downloads"]
PARSED_DIR = "../data/parsed_text_files"

os.makedirs(PARSED_DIR, exist_ok=True)

def extract_text_and_urls(pdf_path):
    """Extract text and URLs from a PDF."""
    try:
        reader = PdfReader(pdf_path)
        text = "".join(page.extract_text() for page in reader.pages)
        urls = re.findall(r"https?://\S+", text)
        return text, urls
    except Exception as e:
        print(f"Failed to parse {pdf_path}: {e}")
        return "", []

def save_parsed_data(file_name, text, urls):
    """Save extracted text and URLs."""
    base_name = os.path.basename(file_name)
    text_file = os.path.join(PARSED_DIR, f"{base_name}.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(text + "\n\n" + "\n".join(urls))
    print(f"Saved parsed data for {base_name}")

def main():
    for dir_path in PDF_DIRS:
        pdf_files = [os.path.join(dir_path, file) for file in os.listdir(dir_path) if file.endswith(".pdf")]
        for pdf_file in pdf_files:
            text, urls = extract_text_and_urls(pdf_file)
            save_parsed_data(pdf_file, text, urls)

if __name__ == "__main__":
    main()
