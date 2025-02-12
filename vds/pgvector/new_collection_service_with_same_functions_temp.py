import os
import psycopg2
import numpy as np
import base64
import logging
from dotenv import load_dotenv
from rich import print
from sshtunnel import SSHTunnelForwarder
from sentence_transformers import SentenceTransformer
from langchain.vectorstores import PGVector
from langchain.embeddings import HuggingFaceEmbeddings
from local_llm import call_llm
from prompts import SYSTEM_PROMPT

# Load environment variables
dotenv_path = os.path.abspath("../../../.env")
load_dotenv(dotenv_path=dotenv_path)

# SSH and DB Configuration
SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
SSH_USER = os.getenv("SSH_USER")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

COLLECTION_NAME = "VDS_Collection"
VECTOR_DIM = 768
MAX_CONTEXT_LEN = 750
MAX_LLM_CONTEXT = 1500
MAX_SHOW = 55

# Logging Configuration
logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

# Load local embedding model
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

# Function to check if the database collection exists
def check_database():
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT to_regclass('{COLLECTION_NAME}');")
        result = cursor.fetchone()
        if result and result[0]:
            print(f"✅ Collection '{COLLECTION_NAME}' exists.")
        else:
            print(f"⚠️ Collection '{COLLECTION_NAME}' does not exist.")
    except Exception as e:
        print(f"❌ Error checking database: {e}")
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

# Function to get PGVector store using LangChain
def get_pgvector_store():
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{DB_PORT}/{DB_NAME}"
    return PGVector(connection_string=connection_string, embedding_function=embedding_model, collection_name=COLLECTION_NAME)

# Function to perform similarity search using LangChain
def similarity_search(sentence, top_k=10):
    vectorstore = get_pgvector_store()
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": top_k})
    retrieved_docs = retriever.get_relevant_documents(sentence)

    search_results = []
    for i, doc in enumerate(retrieved_docs, start=1):
        search_results.append((doc.page_content, 1.0, "Source Unknown"))  # No explicit scores available in LangChain
        print(f"\nResult {i}:\n  - Context: {doc.page_content[:500]}...")

    return search_results

# Function to perform relevance search using LangChain
def relevance_search(sentence, top_k=10):
    vectorstore = get_pgvector_store()
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": top_k})
    retrieved_docs = retriever.get_relevant_documents(sentence)

    search_results = []
    for i, doc in enumerate(retrieved_docs, start=1):
        search_results.append((doc.page_content, 1.0, "Source Unknown"))  
        print(f"\nResult {i}:\n  - Context: {doc.page_content[:500]}...")

    return search_results

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

    # Format output with retrieved sources
    rag_info = "Website references:\n"
    for idx, doc in enumerate(retrieved_docs):
        context, score, webpage = doc
        rag_info += f"\n{idx + 1}. {context[:MAX_SHOW]} ... ({round(score, 2)})\n{webpage}"

    response = f"{response}\n\n{rag_info}"
    print(f"\n[bold]Full response:[/bold] {response}")
    return response

# AI Interface
def call_ai_service(user_input, search_type="similarity"):
    """Handles AI query processing using PGVector and LLM."""
    return answer_rag_question(user_input, search_type)

# Test function
def test_ai_service():
    TEST_QUESTION_1 = "What is general advice for subtitle usage at Verizon?"
    TEST_QUESTION_2 = "What are the elements a toggle contains?"

    print(f"\nTest question: {TEST_QUESTION_1}")
    print(f"Test response: {call_ai_service(TEST_QUESTION_1)}\n")

    print(f"\nTest question: {TEST_QUESTION_2}")
    print(f"Test response: {call_ai_service(TEST_QUESTION_2)}\n")

if __name__ == "__main__":
    test_ai_service()
    server.stop()
    print("🔒 SSH Tunnel closed.")
