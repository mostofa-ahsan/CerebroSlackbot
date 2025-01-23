import os
import psycopg2
from psycopg2.extensions import AsIs
from pathlib import Path
import fitz  # PyMuPDF for PDF processing
import numpy as np

# Configuration
PDF_FOLDERS = ["../../data/converted_downloads", "../../data/pages_as_pdf"]
CHUNK_SIZE = 1000
DB_CONFIG = {
    "dbname": "postgres",
    "user": "ahsamo6",
    "password": "1056092",
    "host": "localhost",
    "port": 5432
}
TABLE_NAME = "vds_documents"
VECTOR_DIM = 768

# Function to connect to PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        exit()

# Function to create the table
def create_table(cursor):
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id SERIAL PRIMARY KEY,
                file_name TEXT,
                chunk_id TEXT,
                content TEXT,
                embedding VECTOR(%s)
            );
        """, (VECTOR_DIM,))
        print(f"Table '{TABLE_NAME}' is ready.")
    except Exception as e:
        print(f"Error creating table: {e}")

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

# Function to chunk text
def chunk_text(text, chunk_size=CHUNK_SIZE):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])

# Function to generate dummy embeddings
def generate_embedding(text, dim=VECTOR_DIM):
    return np.random.rand(dim).tolist()

# Function to insert data into the table
def insert_data(cursor, file_name, chunk_id, content, embedding):
    try:
        cursor.execute(f"""
            INSERT INTO {TABLE_NAME} (file_name, chunk_id, content, embedding)
            VALUES (%s, %s, %s, %s);
        """, (file_name, chunk_id, content, embedding))
        print(f"✅ Data inserted for chunk {chunk_id} of {file_name}")
    except Exception as e:
        print(f"❌ Error inserting data for chunk {chunk_id} of {file_name}: {e}")

# Main ingestion function
def ingest_to_pgvector():
    print("### Starting Data Ingestion for PostgreSQL ###")

    # Connect to the database
    conn = connect_to_db()
    cursor = conn.cursor()

    # Ensure the table exists
    create_table(cursor)

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

                # Insert each chunk into the database
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{file_name}_{i}"
                    embedding = generate_embedding(chunk)
                    insert_data(cursor, file_name, chunk_id, chunk, embedding)

    # Close the database connection
    cursor.close()
    conn.close()
    print("### Data Ingestion Completed ###")

if __name__ == "__main__":
    ingest_to_pgvector()
