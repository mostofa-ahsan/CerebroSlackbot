import os
import chromadb
from chromadb.config import Settings

# Define the directory for ChromaDB
CHROMA_DB_DIR = "../../data/cerebro_chroma_db_v1"

def initialize_chroma_db(chroma_db_dir=CHROMA_DB_DIR):
    """Initialize the ChromaDB."""
    # Ensure the directory exists
    os.makedirs(chroma_db_dir, exist_ok=True)
    
    # Initialize ChromaDB client using the Settings configuration
    client = chromadb.Client(
        Settings(
            persist_directory=chroma_db_dir,
            chroma_db_impl="duckdb+parquet"  # Default local storage implementation
        )
    )
    
    # Print confirmation message
    print(f"Database 'cerebro_chroma_db_v1' created at {chroma_db_dir}")

def main():
    initialize_chroma_db()

if __name__ == "__main__":
    initialize_chroma_db()
