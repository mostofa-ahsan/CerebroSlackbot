import os
from pathlib import Path
from PyPDF2 import PdfReader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
# from langchain_chroma import Chroma
# from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document  # Import Document object

# Configuration
PDF_FOLDERS = ["../../data/converted_downloads_test", "../../data/pages_as_pdf_test"]
CHROMA_DB_DIR = "../../data/cerebro_chroma_db_test_2"
SENTENCE_MODEL_PATH = "../../models/all-mpnet-base-v2"
CACHE_FOLDER = "../../cache"
COLLECTION_NAME = "cerebro_vds_test_2"


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    """
    try:
        reader = PdfReader(pdf_path)
        text = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None


def load_pdfs_from_folders(folders):
    """
    Load all PDFs from the specified folders and format them correctly as Document objects.
    """
    documents = []
    for folder in folders:
        folder_path = Path(folder)
        for pdf_file in folder_path.glob("*.pdf"):
            print(f"Processing: {pdf_file}")
            content = extract_text_from_pdf(pdf_file)
            if content:
                # Create Document objects
                documents.append(Document(page_content=content, metadata={"source": str(pdf_file)}))
    return documents


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


def initialize_chroma_vectorstore(documents):
    """
    Initialize the Chroma vector store and persist it.
    """
    # Ensure the ChromaDB directory exists
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)

    # Set up embedding model
    embedding_model = HuggingFaceEmbeddings(
        model_name=SENTENCE_MODEL_PATH, 
        cache_folder=CACHE_FOLDER
    )

    # Initialize Chroma vector store
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DB_DIR,
        collection_metadata={"hnsw:space":"cosine"}
    )
    vectorstore.persist()
    print(f"Vectorstore created and persisted at {CHROMA_DB_DIR}")
    return vectorstore


def inspect_collection():
    
    embedding_model = HuggingFaceEmbeddings(
        model_name=SENTENCE_MODEL_PATH, 
        cache_folder=CACHE_FOLDER
    )
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embedding_model,
        
    )
    # stored_docs = vectorstore.similarity_search("what are the components of a toggle?", k=10)
    print(f" Inspecting Collection: {COLLECTION_NAME}")
    print(f" Vectorstore created and persisted at {CHROMA_DB_DIR}")
    

    stored_docs = vectorstore.get()
    print(f"Total Documents in collection: {len(stored_docs)}")
    for doc in stored_docs:
        print(f"  - Context: {doc.page_content[:500]}")
        print(f"  - Metadata: {doc.metadata}\n")


    print(f" Inspecting Collection : {COLLECTION_NAME}")
    
    # for doc in stored_docs:
    #     print(f"  - Context: {doc.page_content[:500] + '...' if len(doc.page_content) > 500 else doc.page_content}")
    #     print(f"  - Metadata: {doc.metadata}")
    #     print("\n")

def main():
    # Step 1: Load PDFs from the specified folders
    print("Loading PDFs from folders...")
    documents = load_pdfs_from_folders(PDF_FOLDERS)

    if not documents:
        print("No documents found. Exiting.")
        return

    # Step 2: Chunk the documents
    print("Chunking documents...")
    chunked_documents = chunk_documents(documents)

    # Step 3: Initialize the Chroma vector store
    print("Initializing Chroma vector store...")
    initialize_chroma_vectorstore(chunked_documents)
    print(f" Number of documents: {len(documents)}")
    print(f" Number of chunks: {len(chunked_documents)}")


    # print("Inspecting Collection!!!!")
    # inspect_collection()


if __name__ == "__main__":
    main()
