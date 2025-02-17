import os
import psycopg2
import numpy as np
import fitz  # PyMuPDF for PDF processing
import pandas as pd
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_postgres.vectorstores import PGVector
from langchain_core.documents import Document

# Load environment variables
dotenv_path = os.path.abspath("../../../.env")
load_dotenv(dotenv_path=dotenv_path)

# Retrieve database credentials from environment variables
SSH_HOST = os.getenv("SSH_HOST")  
SSH_PORT = int(os.getenv("SSH_PORT", 22))  
SSH_USER = os.getenv("SSH_USER")  
SSH_PASSWORD = os.getenv("SSH_PASSWORD")  

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")  
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER", "dbuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_db_password")
DB_NAME = os.getenv("DB_NAME", "vdsdata")
COLLECTION_NAME = "VDS_Collection"  # Collection for storing vectors
VECTOR_DIM = 768

# PDF processing config
PDF_FOLDERS = ["../../data/converted_downloads_2", "../../data/pages_as_pdf_2"]
CHUNK_SIZE = 2000  
CHUNK_OVERLAP = 200  

# Load embedding model
SENTENCE_MODEL_PATH = "../../models/all-mpnet-base-v2"
embedding_model = SentenceTransformer(SENTENCE_MODEL_PATH)

# Establish SSH tunnel
server = SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASSWORD,
    remote_bind_address=(DB_HOST, DB_PORT),
    local_bind_address=("127.0.0.1", 5433)
)
server.start()

# Update DB_PORT to the tunneled local port
DB_PORT = 5433

# Create PostgreSQL connection string for LangChain PGVector
PG_CONN_STRING = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{DB_PORT}/{DB_NAME}"

# Initialize PGVector
vector_store = PGVector(embeddings=embedding_model, collection_name=COLLECTION_NAME, connection=PG_CONN_STRING)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text += page.get_text()
    except Exception as e:
        print(f"❌ Failed to extract text from {pdf_path}: {e}")
    return text

# Function to chunk text with overlap
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    for i in range(0, len(words), chunk_size - overlap):
        yield " ".join(words[i:i + chunk_size])

# Function to generate embeddings using LangChain
def generate_embedding(text):
    return embedding_model.encode(text).tolist()

# Function to insert data into the PGVector collection
def insert_data(file_name, chunk_id, content):
    try:
        embedding = generate_embedding(content)
        doc = Document(page_content=content, metadata={"file_name": file_name, "chunk_id": chunk_id})
        vector_store.add_documents([doc])
        print(f"✅ Data inserted for chunk {chunk_id} of {file_name}")
    except Exception as e:
        print(f"❌ Error inserting data for chunk {chunk_id} of {file_name}: {e}")

# Main ingestion function
def ingest_to_pgvector():
    print("### 🚀 Starting Data Ingestion for PGVector ###")

    # Process PDF files
    for folder in PDF_FOLDERS:
        for file_name in os.listdir(folder):
            if file_name.endswith(".pdf"):
                file_path = os.path.join(folder, file_name)
                print(f"📄 Processing: {file_path}")

                # Extract text from PDF
                text = extract_text_from_pdf(file_path)
                if not text.strip():
                    print(f"⚠️ No text extracted from {file_path}")
                    continue

                # Chunk the text
                chunks = list(chunk_text(text))

                # Insert each chunk into the collection
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{file_name}_{i}"
                    insert_data(file_name, chunk_id, chunk)

    print("### ✅ Data Ingestion Completed ###")

if __name__ == "__main__":
    try:
        ingest_to_pgvector()
    finally:
        server.stop()  # Ensure SSH tunnel is stopped after execution
        print("🔒 SSH Tunnel closed.")
