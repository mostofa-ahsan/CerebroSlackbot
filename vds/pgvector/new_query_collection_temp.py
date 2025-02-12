import os
import sys
import base64
import logging
from dotenv import load_dotenv
from rich import print
from sshtunnel import SSHTunnelForwarder
from langchain.vectorstores import PGVector
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

# Load environment variables
dotenv_path = os.path.abspath("../../../.env")
load_dotenv(dotenv_path=dotenv_path)

# SSH Configuration
SSH_HOST = os.getenv("SSH_HOST")  
SSH_PORT = int(os.getenv("SSH_PORT", 22))  
SSH_USER = os.getenv("SSH_USER")  
SSH_PASSWORD = os.getenv("SSH_PASSWORD")  

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")  
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER", "dbuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_db_password")
DB_NAME = os.getenv("DB_NAME", "vdsdata")
SCHEMA_NAME = "vds_v2"
COLLECTION_NAME = "VDS_Collection"  
VECTOR_DIM = 768

# Logging Configuration
logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

# Load embedding model
SENTENCE_MODEL_PATH = "../../models/all-mpnet-base-v2"
embedding_model = HuggingFaceEmbeddings(model_name=SENTENCE_MODEL_PATH)

# Establish SSH tunnel
server = SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASSWORD,
    remote_bind_address=(DB_HOST, DB_PORT),
    local_bind_address=("127.0.0.1", 5433)  
)
server.start()

# Update DB_PORT to use local tunnel
DB_PORT = 5433

# Function to connect to PGVector with LangChain
def get_pgvector_store():
    try:
        connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{DB_PORT}/{DB_NAME}"
        vectorstore = PGVector(
            connection_string=connection_string,
            embedding_function=embedding_model,
            collection_name=COLLECTION_NAME,
            schema=SCHEMA_NAME
        )
        return vectorstore
    except Exception as e:
        print(f"❌ Error connecting to PGVector: {e}")
        exit()

# Function to decode Base64 webpage link
def decode_base64_to_url(b64_string):
    """Decode a base64 string to a URL."""
    try:
        return base64.urlsafe_b64decode(b64_string.encode()).decode()
    except Exception:
        return "Unknown source"

# Function to perform similarity search using LangChain PGVector
def similarity_search(query, top_k=10):
    vectorstore = get_pgvector_store()
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": top_k})

    docs = retriever.get_relevant_documents(query)
    results = [(doc.page_content, doc.metadata.get("score", 0), doc.metadata.get("source", "")) for doc in docs]

    for i, (content, score, source) in enumerate(results, start=1):
        print(f"\n🔍 Result {i}: Webpage: {source}\nScore: {round(score, 4)}\nContext: {content[:500]}...")

    return results

# Function to perform relevance search using LangChain PGVector
def relevance_search(query, top_k=10):
    vectorstore = get_pgvector_store()
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": top_k})

    docs = retriever.get_relevant_documents(query)
    results = [(doc.page_content, doc.metadata.get("score", 0), doc.metadata.get("source", "")) for doc in docs]

    for i, (content, score, source) in enumerate(results, start=1):
        print(f"\n🔍 Result {i}: Webpage: {source}\nScore: {round(score, 4)}\nContext: {content[:500]}...")

    return results

if __name__ == "__main__":
    # Parameters
    query_text = "What are the key components of a toggle?"

    # Perform similarity search
    print("\n🔹 Running Similarity Search:")
    similarity_search(query_text)

    # Perform relevance search
    print("\n🔹 Running Relevance Search:")
    relevance_search(query_text)

    # Close SSH tunnel after execution
    server.stop()
    print("🔒 SSH Tunnel closed.")
