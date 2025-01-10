import os
import chromadb
from chromadb.config import Settings

# Define the directory for ChromaDB
CHROMA_DB_DIR = "../data/cerebro_chroma_db"

def initialize_chroma_db():
    """Initialize the ChromaDB."""
    # Ensure the directory exists
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)
    
    # Initialize ChromaDB client using the Settings configuration
    client = chromadb.Client(
        Settings(
            persist_directory=CHROMA_DB_DIR,
            chroma_db_impl="duckdb+parquet"  # Default local storage implementation
        )
    )
    
    # Print confirmation message
    print(f"Database 'cerebro_chroma_db' created at {CHROMA_DB_DIR}")

if __name__ == "__main__":
    initialize_chroma_db()
