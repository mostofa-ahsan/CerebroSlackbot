import os
import psycopg2
from psycopg2.extensions import AsIs
from pathlib import Path
import fitz  # PyMuPDF for PDF processing
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.abspath("../../../.env")
load_dotenv(dotenv_path=dotenv_path)

# Retrieve database credentials from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

# Print for debugging (Remove in production)
print("DB_USER:", DB_USER)
print("DB_PASSWORD:", DB_PASSWORD)
print("DB_PORT:", DB_PORT)
print("DB_NAME:", DB_NAME)
print("DB_HOST:", DB_HOST)

# Configuration
PDF_FOLDERS = ["../../data/converted_downloads_2", "../../data/pages_as_pdf_2"]
CHUNK_SIZE = 2000  # Increased chunk size
CHUNK_OVERLAP = 200  # Overlapping tokens
VECTOR_DIM = 768
SCHEMA_NAME = "vds_v2"
TABLE_NAME = f"{SCHEMA_NAME}.vds_documents_3"  # Table inside schema

# Function to connect to PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        exit()

# Function to create schema (if not exists)
def create_schema(cursor):
    try:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};")
        print(f"✅ Schema '{SCHEMA_NAME}' is ready.")
    except Exception as e:
        print(f"❌ Error creating schema: {e}")

# Function to create the table inside schema
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
        print(f"✅ Table '{TABLE_NAME}' is ready.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")

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

    # Ensure the schema exists
    create_schema(cursor)

    # Ensure the table exists
    create_table(cursor)

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
                chunks = list(chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP))

                # Insert each chunk into the database
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{file_name}_{i}"
                    embedding = generate_embedding(chunk)
                    insert_data(cursor, file_name, chunk_id, chunk, embedding)

    # Close the database connection
    cursor.close()
    conn.close()
    print("### ✅ Data Ingestion Completed ###")

if __name__ == "__main__":
    ingest_to_pgvector()
