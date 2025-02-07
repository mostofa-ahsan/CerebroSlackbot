import psycopg2
import numpy as np
import base64
import logging
import getpass
from rich import print
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../config")))
# Importing local LLM and prompt configuration
from local_llm import call_llm
from prompts import SYSTEM_PROMPT

# Load environment variables
dotenv_path = os.path.abspath("../../../.env")
load_dotenv(dotenv_path=dotenv_path)


# Logging configuration
logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

# Constants
# whoami = getpass.getuser()
# SENTENCE_MODEL_PATH = f"/Users/{whoami}/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2"
# CACHE_FOLDER = f"/Users/{whoami}/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2"
# SENTENCE_MODEL_PATH = f"/Users/ahsamo6/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2"
SENTENCE_MODEL_PATH = os.getenv("SENTENCE_MODEL_PATH")
CACHE_FOLDER = f"/Users/ahsamo6/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2"

MAX_CONTEXT_LEN = 750
MAX_LLM_CONTEXT = 1500
MAX_SHOW = 55


PG_USER = os.getenv("PG_USER")
PG_HOST = os.getenv("PG_HOST")
PG_DB = os.getenv("PG_DB")
PG_PASSWORD = os.getenv("PG_PASSWORD")


PG_PORT = 5432
VECTOR_DIM = 768
TABLE_NAME = "vds_documents_3"

# Function to connect to PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT,
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        exit()

# Function to check if the database table exists
def check_database(table_name):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT to_regclass('{table_name}');")
        result = cursor.fetchone()
        if result[0]:
            print(f"✅ Table '{table_name}' exists.")
        else:
            print(f"⚠️ Table '{table_name}' does not exist.")
    except Exception as e:
        print(f"Error checking database: {e}")
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

# Function to perform similarity search using PGVector
def similarity_search(sentence, table_name, vector_dim=VECTOR_DIM, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query_embedding = np.random.rand(vector_dim).tolist()  # Dummy embedding, replace with real embedding function
        cursor.execute(f"""
            WITH similarity_scores AS (
                SELECT file_name, content,
                (embedding <=> %s::VECTOR) AS raw_score
                FROM {table_name}
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
        print(f"Error performing similarity search: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to perform relevance search using PGVector
def relevance_search(sentence, table_name, vector_dim=VECTOR_DIM, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query_embedding = np.random.rand(vector_dim).tolist()  # Dummy embedding, replace with real embedding function
        cursor.execute(f"""
            WITH relevance_scores AS (
                SELECT file_name, content,
                1 - (embedding <=> %s::VECTOR) AS raw_score
                FROM {table_name}
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
        print(f"Error performing relevance search: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to process query using RAG and LLM
def answer_rag_question(question, search_type="similarity"):
    """Retrieve context from the vectorstore and answer the question using the local LLM."""
    if search_type == "similarity":
        retrieved_docs = similarity_search(question, TABLE_NAME, top_k=3)
    else:
        retrieved_docs = relevance_search(question, TABLE_NAME, top_k=3)

    if not retrieved_docs:
        return "No relevant information found."

    context = "\n".join([doc[0][:MAX_LLM_CONTEXT] for doc in retrieved_docs])  # Truncate to context limit
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
