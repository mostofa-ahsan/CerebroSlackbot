import os
import psycopg2
import numpy as np
import fitz  # PyMuPDF for PDF processing
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
dotenv_path = os.path.abspath("../../../.env")
load_dotenv(dotenv_path=dotenv_path)

# Retrieve database credentials from environment variables
SSH_HOST = os.getenv("SSH_HOST")  # e.g., 155.138.192.178
SSH_PORT = int(os.getenv("SSH_PORT", 22))  # Default SSH port
SSH_USER = os.getenv("SSH_USER")  # e.g., "ahsamo6"
SSH_PASSWORD = os.getenv("SSH_PASSWORD")  # Your SSH password

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")  # Localhost since we use SSH tunnel
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER", "dbuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_db_password")
DB_NAME = os.getenv("DB_NAME", "vdsdata")
SCHEMA_NAME = "vds_v2"
TABLE_NAME = f"{SCHEMA_NAME}.vds_documents_3"  # Specify schema explicitly
VECTOR_DIM = 768

# PDF processing config
PDF_FOLDERS = ["../../data/converted_downloads_2", "../../data/pages_as_pdf_2"]
CHUNK_SIZE = 2000  # Increased chunk size
CHUNK_OVERLAP = 200  # Overlapping tokens

# Establish SSH tunnel
server = SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASSWORD,
    remote_bind_address=(DB_HOST, DB_PORT),
    local_bind_address=("127.0.0.1", 5433)  # Redirect to local port
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
            port=DB_PORT  # Use the local port from SSH tunnel
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        exit()

# Function to create table in the specified schema
def create_table(cursor):
    try:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};")
        cursor
