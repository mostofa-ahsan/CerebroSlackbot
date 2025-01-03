from bs4 import BeautifulSoup
import os

def parse_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, 'html.parser')
    return soup.get_text()

def parse_all(scraped_dir, parsed_dir):
    os.makedirs(parsed_dir, exist_ok=True)
    for file in os.listdir(scraped_dir):
        if file.endswith(".html"):
            text = parse_html(os.path.join(scraped_dir, file))
            with open(os.path.join(parsed_dir, file.replace(".html", ".txt")), "w", encoding="utf-8") as f:
                f.write(text)
    print(f"Parsing completed. Files saved in {parsed_dir}.")
