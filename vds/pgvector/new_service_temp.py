import os
import sys
import psycopg2
import numpy as np
import base64
import logging
from dotenv import load_dotenv
from rich import print
from sshtunnel import SSHTunnelForwarder
from sentence_transformers import SentenceTransformer

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
SSH_HOST = os.getenv("SSH_HOST")  # e.g., "155.138.192.178"
SSH_PORT = int(os.getenv("SSH_PORT", 22))  # Default SSH port
SSH_USER = os.getenv("SSH_USER")  # e.g., "ahsamo6"
SSH_PASSWORD = os.getenv("SSH_PASSWORD")  # SSH password

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")  # Localhost for SSH tunnel
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER", "dbuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_db_password")
DB_NAME = os.getenv("DB_NAME", "vdsdata")
SCHEMA_NAME = "vds_v2"
TABLE_NAME = f"{SCHEMA_NAME}.vds_documents"  # Explicit schema
VECTOR_DIM = 768
MAX_CONTEXT_LEN = 750
MAX_LLM_CONTEXT = 1500
MAX_SHOW = 55

# Logging Configuration
logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

# Load embedding model
SENTENCE_MODEL_PATH = "../../models/all-mpnet-base-v2"
embedding_model = SentenceTransformer(SENTENCE_MODEL_PATH)

# Establish SSH tunnel
server = SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASSWORD,
    remote_bind_address=(DB_HOST, DB_PORT),
    local_bind_address=("127.0.0.1", 5433)  # Redirect to local port
)
server.start()

# Update DB_PORT to use local tunnel
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


# Function to check if the database table exists
def check_database():
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT to_regclass('{TABLE_NAME}');")
        result = cursor.fetchone()
        if result and result[0]:
            print(f"✅ Table '{TABLE_NAME}' exists.")
        else:
            print(f"⚠️ Table '{TABLE_NAME}' does not exist.")
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


# Function to generate embeddings using `all-mpnet-base-v2`
def generate_embedding(text):
    return embedding_model.encode(text).tolist()


# Function to perform similarity search using PGVector
def similarity_search(sentence, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query_embedding = generate_embedding(sentence)  # Use real embeddings

        cursor.execute(f"""
            WITH similarity_scores AS (
                SELECT file_name, content,
                (embedding <-> %s::VECTOR) AS raw_score
                FROM {TABLE_NAME}
            ),
            normalized_scores AS (
                SELECT file_name, content,
                1 - (raw_score - MIN(raw_score) OVER()) / 
                    (MAX(raw_score) OVER() - MIN(raw_score) OVER()) AS similarity_score
                FROM similarity_scores
            )
            SELECT file_name, content, similarity_score
            FROM normalized_scores
            ORDER BY similarity_score DESC
            LIMIT {top_k};
        """, (query_embedding,))
        results = cursor.fetchall()

        search_results = []
        for i, (file_name, content, score) in enumerate(results, start=1):
            decoded_url = decode_base64_to_url(file_name[:-4]) if file_name.endswith(".pdf") else decode_base64_to_url(file_name)
            search_results.append((content, score, decoded_url))
            print(f"\nResult {i}: Webpage: {decoded_url}\nScore: {round(score, 4)}\nContext: {content[:500]}...")

        return search_results

    except Exception as e:
        print(f"❌ Error performing similarity search: {e}")
    finally:
        cursor.close()
        conn.close()


# Function to perform relevance search using PGVector
def relevance_search(sentence, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query_embedding = generate_embedding(sentence)  # Use real embeddings

        cursor.execute(f"""
            WITH relevance_scores AS (
                SELECT file_name, content,
                1 - (embedding <-> %s::VECTOR) AS raw_score
                FROM {TABLE_NAME}
            ),
            normalized_scores AS (
                SELECT file_name, content,
                (raw_score - MIN(raw_score) OVER()) / 
                    (MAX(raw_score) OVER() - MIN(raw_score) OVER()) AS relevance_score
                FROM relevance_scores
            )
            SELECT file_name, content, relevance_score
            FROM normalized_scores
            ORDER BY relevance_score DESC
            LIMIT {top_k};
        """, (query_embedding,))
        results = cursor.fetchall()

        search_results = []
        for i, (file_name, content, score) in enumerate(results, start=1):
            decoded_url = decode_base64_to_url(file_name[:-4]) if file_name.endswith(".pdf") else decode_base64_to_url(file_name)
            search_results.append((content, score, decoded_url))
            print(f"\nResult {i}: Webpage: {decoded_url}\nScore: {round(score, 4)}\nContext: {content[:500]}...")

        return search_results

    except Exception as e:
        print(f"❌ Error performing relevance search: {e}")
    finally:
        cursor.close()
        conn.close()


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
    print(f"Test response: {call_ai_service('What are the elements of a toggle?')}")

if __name__ == "__main__":
    test_ai_service()
    server.stop()
    print("🔒 SSH Tunnel closed.")
