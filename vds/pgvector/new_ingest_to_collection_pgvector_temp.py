import os
import psycopg2
import numpy as np
import fitz  # PyMuPDF for PDF processing
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer

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
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "vdsdata")

COLLECTION_NAME = "VDS_Collection"
VECTOR_DIM = 768

# PDF processing config
PDF_FOLDERS = ["../../data/converted_downloads_2", "../../data/pages_as_pdf_2"]
CHUNK_SIZE = 2000  
CHUNK_OVERLAP = 200  

# Load local embedding model
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
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        exit()

# Create Collection (Table in PGVector)
def create_collection():
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {COLLECTION_NAME} (
        id bigserial PRIMARY KEY, 
        file_name TEXT,
        chunk_id TEXT,
        content TEXT,
        tokens INTEGER,
        embedding vector({VECTOR_DIM})
    );"""
    
    cur.execute(create_table_query)
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Collection '{COLLECTION_NAME}' is ready.")

# Extract text from PDFs
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text += page.get_text()
    except Exception as e:
        print(f"❌ Failed to extract text from {pdf_path}: {e}")
    return text

# Chunk text with overlap
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    for i in range(0, len(words), chunk_size - overlap):
        yield " ".join(words[i:i + chunk_size])

# Generate embeddings
def generate_embedding(text):
    return embedding_model.encode(text).tolist()

# Insert data into collection
def insert_data(df):
    conn = connect_to_db()
    cur = conn.cursor()
    
    data_list = [(row['file_name'], row['chunk_id'], row['content'], len(row['content'].split()), np.array(row['embedding'])) for _, row in df.iterrows()]
    
    execute_values(cur, f"INSERT INTO {COLLECTION_NAME} (file_name, chunk_id, content, tokens, embedding) VALUES %s", data_list)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Data successfully inserted into collection.")

# Main ingestion function
def ingest_to_pgvector():
    print("🚀 Starting Data Ingestion for PGVector")
    create_collection()
    
    import pandas as pd
    df = pd.DataFrame(columns=["file_name", "chunk_id", "content", "embedding"])
    
    for folder in PDF_FOLDERS:
        for file_name in os.listdir(folder):
            if file_name.endswith(".pdf"):
                file_path = os.path.join(folder, file_name)
                text = extract_text_from_pdf(file_path)
                
                if not text.strip():
                    print(f"⚠️ No text extracted from {file_path}")
                    continue
                
                chunks = list(chunk_text(text))
                
                for i, chunk in enumerate(chunks):
                    df = df.append({
                        "file_name": file_name,
                        "chunk_id": f"{file_name}_{i}",
                        "content": chunk,
                        "embedding": generate_embedding(chunk)
                    }, ignore_index=True)

    insert_data(df)

if __name__ == "__main__":
    try:
        ingest_to_pgvector()
    finally:
        server.stop()
        print("🔒 SSH Tunnel closed.")
