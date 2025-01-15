import os
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
SENTENCE_MODEL_PATH = "../models/all-mpnet-base-v2"
CACHE_FOLDER = "../cache"

def initialize_chroma_db(documents):
    """
    Initialize the ChromaDB with documents.
    """
    # Ensure the directory exists
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)

    # Set up embedding model
    embedding_model = HuggingFaceEmbeddings(
        model_name=SENTENCE_MODEL_PATH, 
        cache_folder=CACHE_FOLDER
    )

    # Initialize ChromaDB vector store
    vectorstore = Chroma(
        collection_name="verizon_docs",
        embedding_function=embedding_model,
        persist_directory=CHROMA_DB_DIR,
    )

    # Add documents to the vector store and persist
    vectorstore.add_documents(documents)
    vectorstore.persist()

    # Print confirmation message
    print(f"Database 'verizon_docs' created at {CHROMA_DB_DIR}")
    return vectorstore

def main():
    # Example documents to add to the database
    documents = [
        {"id": "1", "text": "This is a sample document."},
        {"id": "2", "text": "This is another sample document."},
    ]
    initialize_chroma_db(documents)

if __name__ == "__main__":
    main()
