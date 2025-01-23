import os
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import fitz  # PyMuPDF for PDF processing

# Configuration
CHROMA_DB_DIR = "../../data/cerebro_chroma_db_v1"
COLLECTION_NAME = "cerebro_vds_v1"
PDF_FOLDERS = ["../../data/converted_downloads_2", "../../data/pages_as_pdf_2"]
CHUNK_SIZE = 1000  # Adjust chunk size as needed
LOCAL_MODEL_PATH = "../../models/all-mpnet-base-v2"  # Path to the locally downloaded model


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    text = ""
    try:
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text += page.get_text()
    except Exception as e:
        print(f"❌ Failed to extract text from {pdf_path}: {e}")
    return text


def chunk_text(text, chunk_size=CHUNK_SIZE):
    """Splits text into chunks."""
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])


def ingest_to_cerebro_vds():
    print("### Starting Data Ingestion for Chroma DB Collection ###")

    # Initialize embedding function using the local model
    embeddings = SentenceTransformerEmbeddingFunction(model_name=LOCAL_MODEL_PATH)

    # Initialize Chroma DB client
    client = chromadb.Client(
        Settings(
            persist_directory=CHROMA_DB_DIR,
            chroma_db_impl="duckdb+parquet"
        )
    )

    # Create or get collection
    collection = client.get_or_create_collection(COLLECTION_NAME, embedding_function=embeddings)
    print(f"✅ Collection '{COLLECTION_NAME}' initialized")

    # Process PDF files
    for folder in PDF_FOLDERS:
        for file_name in os.listdir(folder):
            if file_name.endswith(".pdf"):
                file_path = os.path.join(folder, file_name)
                print(f"Processing: {file_path}")

                # Extract text from PDF
                text = extract_text_from_pdf(file_path)
                if not text.strip():
                    print(f"⚠️ No text extracted from {file_path}")
                    continue

                # Chunk the text
                chunks = list(chunk_text(text))

                # Prepare data for ingestion
                ids = [f"{file_name}_{i}" for i in range(len(chunks))]
                metadatas = [{"source": file_name, "chunk_id": f"{file_name}_{i}"} for i in range(len(chunks))]

                # Add to collection
                try:
                    collection.add(
                        ids=ids,
                        documents=chunks,
                        metadatas=metadatas,
                    )
                    print(f"✅ Successfully added data from {file_name}")
                except Exception as e:
                    print(f"❌ Failed to add data from {file_name}: {e}")

    # Persist data
    try:
        client.persist()
        print(f"✅ Data persisted to directory: {CHROMA_DB_DIR}")
    except Exception as e:
        print(f"⚠️ Failed to persist data: {e}")

    print("### Data Ingestion Completed ###")


if __name__ == "__main__":
    ingest_to_cerebro_vds()
