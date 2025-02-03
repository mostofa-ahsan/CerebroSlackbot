import getpass
import logging
import base64
import psycopg2
import numpy as np
from transformers import pipeline

# Logging Configuration
logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

# Constants
whoami = getpass.getuser()
SENTENCE_MODEL_PATH = f"/Users/{whoami}/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2"
CACHE_FOLDER = f"/Users/{whoami}/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2"
BASE_URL = "https://designsystem.verizon.com/"
HUMAN_PROMPT = "Use the following context to answer the question: {context}.\n\nQuestion: {question}"
MAX_CONTEXT_LEN = 750
MAX_LLM_CONTEXT = 1500
MAX_SHOW = 55
PDF = ".pdf"
TABLE_NAME = "vds_documents"
DB_CONFIG = {
    "dbname": "postgres",
    "user": "ahsamo6",
    "password": "your_password",
    "host": "localhost",
    "port": 5432,
}

# Function to connect to PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        exit()

# Function to decode Base64 webpage links
def decode_base64_to_url(b64_string):
    try:
        if b64_string[-4:] == PDF:
            b64_string = b64_string[:-4]
            return base64.urlsafe_b64decode(b64_string.encode()).decode() + PDF
        return base64.urlsafe_b64decode(b64_string.encode()).decode()
    except:
        return "Unknown source"

# Function to perform similarity search using pgvector
def similarity_search(sentence, vector_dim=768, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query_embedding = np.random.rand(vector_dim).tolist()
        cursor.execute(f"""
            WITH similarity_scores AS (
                SELECT file_name, content, 
                    (embedding <=> %s::VECTOR) AS raw_score
                FROM {TABLE_NAME}
            ),
            normalized_scores AS (
                SELECT file_name, content, 
                    (1 - (raw_score - MIN(raw_score) OVER()) / 
                    (MAX(raw_score) OVER() - MIN(raw_score) OVER())) AS similarity_score
                FROM similarity_scores
            )
            SELECT file_name, content, similarity_score
            FROM normalized_scores
            ORDER BY similarity_score DESC
            LIMIT {top_k};
        """, (query_embedding,))
        results = cursor.fetchall()

        for i, (file_name, content, score) in enumerate(results, start=1):
            decoded_url = decode_base64_to_url(file_name) if file_name.endswith(".pdf") else decode_base64_to_url(file_name)
            print(f"\nResult {i}:\n  - Webpage: {decoded_url}\n  - Score: {round(score, 4)}\n  - Context: {content[:500]}{'...' if len(content) > 500 else ''}")
    except Exception as e:
        logger.error(f"Error performing similarity search: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to perform relevance search using pgvector
def relevance_search(sentence, vector_dim=768, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query_embedding = np.random.rand(vector_dim).tolist()
        cursor.execute(f"""
            WITH relevance_scores AS (
                SELECT file_name, content, 
                    (1 - (embedding <=> %s::VECTOR)) AS raw_score
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

        for i, (file_name, content, score) in enumerate(results, start=1):
            decoded_url = decode_base64_to_url(file_name) if file_name.endswith(".pdf") else decode_base64_to_url(file_name)
            print(f"\nResult {i}:\n  - Webpage: {decoded_url}\n  - Score: {round(score, 4)}\n  - Context: {content[:500]}{'...' if len(content) > 500 else ''}")
    except Exception as e:
        logger.error(f"Error performing relevance search: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to query RAG-based LLM
def answer_rag_question(question):
    retrieved_docs = similarity_search(question, top_k=3)
    if not retrieved_docs:
        return "No relevant information found."
    
    context = "\n".join([doc[1][:MAX_LLM_CONTEXT] for doc in retrieved_docs])
    instruction = HUMAN_PROMPT.format(context=context, question=question)
    llm = pipeline("text-generation", model=SENTENCE_MODEL_PATH)
    response = llm(instruction)[0]['generated_text']
    
    return response

if __name__ == "__main__":
    test_question = "What are the elements a toggle contains?"
    print(f"Test question: {test_question}")
    response = answer_rag_question(test_question)
    print(f"Response: {response}")
