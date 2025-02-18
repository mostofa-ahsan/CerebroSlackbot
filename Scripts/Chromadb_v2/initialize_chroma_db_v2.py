import os
from pydantic import RootModel
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document  # Import Document object
# import chromadb
# from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Configuration
CHROMA_DB_DIR = "../../data/cerebro_chroma_db_v2"
SENTENCE_MODEL_PATH = "../../models/all-mpnet-base-v2"
CACHE_FOLDER = "../../cache"
os.makedirs(CHROMA_DB_DIR, exist_ok=True)
    

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

    # embedding_model  = SentenceTransformerEmbeddingFunction(model_name=SENTENCE_MODEL_PATH)

    # Initialize ChromaDB vector store
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        # persist_directory=CHROMA_DB_DIR,
    )
    vectorstore.persist()

    # Print confirmation message
    print(f"Database 'verizon_docs' created at {CHROMA_DB_DIR}")
    return vectorstore


def main():
    # Example documents to add to the database
    documents = [
        Document(page_content="This is a sample document.", metadata={"source": "sample_doc_1.pdf"}),
        Document(page_content="This is another sample document.", metadata={"source": "sample_doc_2.pdf"}),
    ]

    print("Initializing ChromaDB...")
    initialize_chroma_db(documents)


if __name__ == "__main__":
    main()
