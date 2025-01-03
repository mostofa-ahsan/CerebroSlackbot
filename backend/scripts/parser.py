import pdfplumber
from bs4 import BeautifulSoup
import os

def parse_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, 'html.parser')
    return soup.get_text()

def parse_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

if __name__ == "__main__":
    input_path = "../data/scraped_pages/"
    output_path = "../data/parsed_data/"
    os.makedirs(output_path, exist_ok=True)

    for file in os.listdir(input_path):
        if file.endswith(".html"):
            parsed_text = parse_html(os.path.join(input_path, file))
        elif file.endswith(".pdf"):
            parsed_text = parse_pdf(os.path.join(input_path, file))

        with open(os.path.join(output_path, file.replace(".html", ".txt").replace(".pdf", ".txt")), "w", encoding="utf-8") as f:
            f.write(parsed_text)
