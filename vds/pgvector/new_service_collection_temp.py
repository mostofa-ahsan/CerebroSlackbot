import os
import sys
import psycopg2
import numpy as np
import base64
import logging
from dotenv import load_dotenv
from rich import print
from sshtunnel import SSHTunnelForwarder
from langchain.vectorstores import PGVector
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

# Add paths for local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../config")))

# Importing local LLM and prompt configuration
from local_llm import call_llm
from prompts import SYSTEM_PROMPT

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
MAX_CONTEXT_LEN = 750
MAX_LLM_CONTEXT = 1500
MAX_SHOW = 55

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

# Function to check if the collection exists
def check_collection():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host="127.0.0.1",
        port=DB_PORT
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT to_regclass('{SCHEMA_NAME}.{COLLECTION_NAME}');")
        result = cursor.fetchone()
        if result and result[0]:
            print(f"✅ Collection '{COLLECTION_NAME}' exists in schema '{SCHEMA_NAME}'.")
        else:
            print(f"⚠️ Collection '{COLLECTION_NAME}' does not exist.")
    except Exception as e:
        print(f"❌ Error checking collection: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to decode Base64 webpage link
def decode_base64_to_url(b64_string):
    """Decode a base64 string to a URL."""
    try:
        return base64.urlsafe_b64decode(b64_string.encode()).decode()
    except Exception:
        return "Unknown source"

# Function to perform a similarity search using LangChain PGVector
def similarity_search(query, top_k=10):
    vectorstore = get_pgvector_store()
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": top_k})

    docs = retriever.get_relevant_documents(query)
    results = [(doc.page_content, doc.metadata.get("score", 0), doc.metadata.get("source", "")) for doc in docs]

    for i, (content, score, source) in enumerate(results, start=1):
        print(f"\nResult {i}: Webpage: {source}\nScore: {round(score, 4)}\nContext: {content[:500]}...")

    return results

# Function to perform a relevance search using LangChain PGVector
def relevance_search(query, top_k=10):
    vectorstore = get_pgvector_store()
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": top_k})

    docs = retriever.get_relevant_documents(query)
    results = [(doc.page_content, doc.metadata.get("score", 0), doc.metadata.get("source", "")) for doc in docs]

    for i, (content, score, source) in enumerate(results, start=1):
        print(f"\nResult {i}: Webpage: {source}\nScore: {round(score, 4)}\nContext: {content[:500]}...")

    return results

# Function to process query using RAG and LLM
def answer_rag_question(question, search_type="similarity"):
    """Retrieve context from the vectorstore and answer the question using the local LLM."""
    if search_type == "similarity":
        retrieved_docs = similarity_search(question, top_k=3)
    else:
        retrieved_docs = relevance_search(question, top_k=3)

    if not retrieved_docs:
        return "No relevant information found."

    context = "\n".join([doc[0][:MAX_LLM_CONTEXT] for doc in retrieved_docs])
    instruction = f"Use the following context to answer the question: {context}\n\nQuestion: {question}"

    # Call local LLM
    prompt = f"SYSTEM: {SYSTEM_PROMPT}.\n\n{instruction}"
    response = call_llm(prompt)

    rag_info = "Website references:\n"
    for idx, doc in enumerate(retrieved_docs):
        context, score, source = doc
        rag_info += f"\n{idx + 1}. {context[:MAX_SHOW]} ... ({round(score, 2)})\n{source}"

    response = f"{response}\n\n{rag_info}"
    print(f"\n[bold]Full response:[/bold] {response}")
    return response

# AI Interface
def call_ai_service(user_input, search_type="similarity"):
    """Handles AI query processing using PGVector and LLM."""
    return answer_rag_question(user_input, search_type)

# Test function
def test_ai_service():
    TEST_QUESTION_1 = "What are the design principles for Verizon's UI components?"
    TEST_QUESTION_2 = "What are the elements a toggle contains?"

    print(f"\nTest question: {TEST_QUESTION_1}")
    print(f"Test response: {call_ai_service(TEST_QUESTION_1)}\n")

    print(f"\nTest question: {TEST_QUESTION_2}")
    print(f"Test response: {call_ai_service(TEST_QUESTION_2)}\n")

if __name__ == "__main__":
    test_ai_service()
    server.stop()
    print("🔒 SSH Tunnel closed.")
