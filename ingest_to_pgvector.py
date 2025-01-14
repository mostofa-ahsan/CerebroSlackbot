import os
import psycopg2
from psycopg2.extensions import AsIs
from pathlib import Path

# Function to connect to PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname="cerebro_pgvectordb",
            user="postgres",
            password="your_password",
            host="127.0.0.1",
            port=5434
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        exit()

# Function to create a table with a vector column
def create_table(cursor, table_name, vector_dim=768):
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                file_name TEXT,
                content TEXT,
                embedding VECTOR(%s)
            );
        """, (vector_dim,))
        print(f"Table '{table_name}' is ready.")
    except Exception as e:
        print(f"Error creating table: {e}")

# Function to extract content from PDF and HTML files
def extract_content(file_path):
    try:
        if file_path.suffix.lower() == ".pdf":
            from PyPDF2 import PdfReader
            reader = PdfReader(str(file_path))
            return " ".join(page.extract_text() for page in reader.pages)
        elif file_path.suffix.lower() == ".html":
            from bs4 import BeautifulSoup
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
            return soup.get_text()
        else:
            return None
    except Exception as e:
        print(f"Error extracting content from {file_path}: {e}")
        return None

# Function to generate embeddings (dummy embeddings for demonstration)
def generate_embedding(text, dim=768):
    import numpy as np
    return np.random.rand(dim).tolist()

# Function to insert data into the table
def insert_data(cursor, table_name, file_name, content, embedding):
    try:
        cursor.execute(f"""
            INSERT INTO {table_name} (file_name, content, embedding)
            VALUES (%s, %s, %s);
        """, (file_name, content, embedding))
        print(f"Inserted data for {file_name}")
    except Exception as e:
        print(f"Error inserting data for {file_name}: {e}")

# Main function for ingestion
def ingest_files_to_pgvector(pdf_dir, html_dir, table_name, vector_dim=768):
    conn = connect_to_db()
    cursor = conn.cursor()

    # Ensure the table exists
    create_table(cursor, table_name, vector_dim)

    # Ingest PDF files
    pdf_path = Path(pdf_dir)
    for file in pdf_path.glob("*.pdf"):
        content = extract_content(file)
        if content:
            embedding = generate_embedding(content, vector_dim)
            insert_data(cursor, table_name, file.name, content, embedding)

    # Ingest HTML files
    html_path = Path(html_dir)
    for file in html_path.glob("*.html"):
        content = extract_content(file)
        if content:
            embedding = generate_embedding(content, vector_dim)
            insert_data(cursor, table_name, file.name, content, embedding)

    # Close the database connection
    cursor.close()
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    # Directories for PDF and HTML files
    pdf_directory = "../data/converted_downloads_1"
    html_directory = "../data/scraped_pages_1"

    # Table name and vector dimension
    table_name = "documents"
    vector_dimension = 768

    # Run the ingestion
    ingest_files_to_pgvector(pdf_directory, html_directory, table_name, vector_dimension)
