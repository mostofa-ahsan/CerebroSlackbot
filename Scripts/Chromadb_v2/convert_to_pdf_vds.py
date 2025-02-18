import os
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from pptx import Presentation
from docx import Document
from PIL import Image
import shutil  # For copying files

DOWNLOAD_DIR = "../../data/downloads"
CONVERTED_DIR = "../../data/converted_downloads"

os.makedirs(CONVERTED_DIR, exist_ok=True)

def convert_to_pdf(file_path, output_dir):
    """Convert various file formats to PDF."""
    try:
        file_ext = Path(file_path).suffix.lower()
        output_file = os.path.join(output_dir, f"{Path(file_path).stem}.pdf")

        if file_ext == ".pdf":
            # Simply copy valid PDFs to the converted folder
            shutil.copy(file_path, output_file)
            print(f"Copied PDF file {file_path} to {output_file}")
            return output_file
        elif file_ext == ".potx":
            # Skip .potx files
            print(f"Skipped .potx file: {file_path}")
            return None
        elif file_ext in [".ppt", ".pptx"]:
            # Convert PowerPoint to PDF
            presentation = Presentation(file_path)
            presentation.save(output_file)
            print(f"Converted presentation {file_path} to {output_file}")
        elif file_ext == ".docx":
            # Convert Word to PDF
            document = Document(file_path)
            document.save(output_file)
            print(f"Converted Word document {file_path} to {output_file}")
        elif file_ext in [".png", ".jpeg", ".jpg"]:
            # Convert images to PDF
            image = Image.open(file_path)
            image.convert("RGB").save(output_file, "PDF")
            print(f"Converted image {file_path} to {output_file}")
        else:
            print(f"Unsupported file format for: {file_path}")
            return None

        return output_file
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Failed to convert {file_path}: {e}")
    return None


def main():
    files = [os.path.join(DOWNLOAD_DIR, file) for file in os.listdir(DOWNLOAD_DIR)]
    for file in files:
        convert_to_pdf(file, CONVERTED_DIR)

if __name__ == "__main__":
    main()
