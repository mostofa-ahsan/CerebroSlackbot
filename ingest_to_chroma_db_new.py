import os
from pathlib import Path
from PyPDF2 import PdfReader
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configuration
PDF_FOLDERS = ["../data/converted_downloads", "../data/pages_as_pdf"]
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
SENTENCE_MODEL_PATH = "../models/all-mpnet-base-v2"
CACHE_FOLDER = "../cache"


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    """
    try:
        reader = PdfReader(pdf_path)
        text = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None


def load_pdfs_from_folders(folders):
    """
    Load all PDFs from the specified folders.
    """
    documents = []
    for folder in folders:
        folder_path = Path(folder)
        for pdf_file in folder_path.glob("*.pdf"):
            print(f"Processing: {pdf_file}")
            content = extract_text_from_pdf(pdf_file)
            if content:
                documents.append({"id": str(pdf_file), "text": content})
    return documents


def chunk_documents(documents):
    """
    Chunk the documents into smaller pieces for embedding.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " "],
    )
    return text_splitter.split_documents(documents)


def initialize_chroma_vectorstore(documents):
    """
    Initialize the Chroma vector store and persist it.
    """
    # Ensure the ChromaDB directory exists
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)

    # Set up embedding model
    embedding_model = HuggingFaceEmbeddings(
        model_name=SENTENCE_MODEL_PATH, 
        cache_folder=CACHE_FOLDER
    )

    # Initialize Chroma vector store
    vectorstore = Chroma(
        collection_name="verizon_docs",
        embedding_function=embedding_model,
        persist_directory=CHROMA_DB_DIR,
    )
    vectorstore.add_documents(documents)
    vectorstore.persist()
    print(f"Vectorstore created and persisted at {CHROMA_DB_DIR}")
    return vectorstore


def main():
    # Step 1: Load PDFs from the specified folders
    print("Loading PDFs from folders...")
    documents = load_pdfs_from_folders(PDF_FOLDERS)

    if not documents:
        print("No documents found. Exiting.")
        return

    # Step 2: Chunk the documents
    print("Chunking documents...")
    chunked_documents = chunk_documents(documents)

    # Step 3: Initialize the Chroma vector store
    print("Initializing Chroma vector store...")
    initialize_chroma_vectorstore(chunked_documents)


if __name__ == "__main__":
    main()
