import os
import psycopg2
import numpy as np
import fitz  # PyMuPDF for PDF processing
import pandas as pd
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector

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

# Function to connect to PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host="127.0.0.1",
            port=DB_PORT
        )
        register_vector(conn)  # Register pgvector for psycopg2
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        exit()

# Function to create collection
def create_collection(cursor):
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")  # Ensure pgvector is enabled

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {COLLECTION_NAME} (
                id SERIAL PRIMARY KEY,
                file_name TEXT,
                chunk_id TEXT,
                content TEXT,
                tokens INTEGER,
                embedding vector({VECTOR_DIM})
            );
        """)
        print(f"✅ Collection '{COLLECTION_NAME}' is ready.")
    except Exception as e:
        print(f"❌ Error creating collection: {e}")

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

# Function to insert data into the collection
def insert_data(cursor, file_name, chunk_id, content, embedding):
    try:
        embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding

        query = f"INSERT INTO {COLLECTION_NAME} (file_name, chunk_id, content, tokens, embedding) VALUES %s"
        values = [(file_name, chunk_id, content, len(content.split()), embedding_list)]

        execute_values(cursor, query, values)
        print(f"✅ Data inserted for chunk {chunk_id} of {file_name}")
    except Exception as e:
        print(f"❌ Error inserting data for chunk {chunk_id} of {file_name}: {e}")

# Main ingestion function
def ingest_to_pgvector():
    print("### 🚀 Starting Data Ingestion for PGVector ###")

    # Connect to the database
    conn = connect_to_db()
    cursor = conn.cursor()

    # Ensure the collection exists
    create_collection(cursor)

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
                    embedding = generate_embedding(chunk)
                    insert_data(cursor, file_name, chunk_id, chunk, embedding)

    # Close the database connection
    cursor.close()
    conn.close()
    print("### ✅ Data Ingestion Completed ###")

if __name__ == "__main__":
    try:
        ingest_to_pgvector()
    finally:
        server.stop()  # Ensure SSH tunnel is stopped after execution
        print("🔒 SSH Tunnel closed.")
