import os
from langchain_huggingface import HuggingFaceEmbeddings  # Updated import
from langchain_chroma import Chroma  # Updated import
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
SENTENCE_MODEL_PATH = "../models/all-mpnet-base-v2"
CACHE_FOLDER = "../cache"


def chunk_documents(documents):
    """
    Chunk the documents into smaller pieces for embedding.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " "],
    )
    return text_splitter.split_documents(documents)


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

    # Chunk the documents before adding
    print("Chunking documents...")
    chunked_documents = chunk_documents(documents)

    # Add documents to the vector store and persist
    print("Adding documents to the vector store...")
    vectorstore.add_documents(chunked_documents)
    vectorstore.persist()

    # Print confirmation message
    print(f"Database 'verizon_docs' created at {CHROMA_DB_DIR}")
    return vectorstore


def main():
    # Example documents to add to the database
    documents = [
        {
            "page_content": "This is a sample document.",
            "metadata": {"source": "sample_doc_1.pdf"}
        },
        {
            "page_content": "This is another sample document.",
            "metadata": {"source": "sample_doc_2.pdf"}
        },
    ]

    print("Initializing ChromaDB...")
    initialize_chroma_db(documents)


if __name__ == "__main__":
    main()
