import os
from pathlib import Path
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter
from pptx import Presentation
from docx import Document
from PIL import Image

DOWNLOAD_DIR = "../data/downloads"
CONVERTED_DIR = "../data/converted_downloads"

os.makedirs(CONVERTED_DIR, exist_ok=True)

def convert_to_pdf(file_path, output_dir):
    """Convert various file formats to PDF."""
    try:
        file_ext = Path(file_path).suffix.lower()
        output_file = os.path.join(output_dir, f"{Path(file_path).stem}.pdf")

        if file_ext in [".pdf"]:
            # Copy PDF directly
            PdfWriter().write(open(output_file, "wb"), PdfReader(file_path))
        elif file_ext in [".ppt", ".pptx"]:
            # Convert PowerPoint to PDF
            presentation = Presentation(file_path)
            presentation.save(output_file)
        elif file_ext in [".docx"]:
            # Convert Word to PDF
            document = Document(file_path)
            document.save(output_file)
        elif file_ext in [".png", ".jpeg", ".jpg"]:
            # Convert images to PDF
            image = Image.open(file_path)
            image.save(output_file, "PDF")
        print(f"Converted {file_path} to {output_file}")
    except Exception as e:
        print(f"Failed to convert {file_path}: {e}")

def main():
    files = [os.path.join(DOWNLOAD_DIR, file) for file in os.listdir(DOWNLOAD_DIR)]
    for file in files:
        convert_to_pdf(file, CONVERTED_DIR)

if __name__ == "__main__":
    main()
