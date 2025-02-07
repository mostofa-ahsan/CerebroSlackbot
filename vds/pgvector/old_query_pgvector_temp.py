import os
import psycopg2
import numpy as np
import base64
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.abspath("../../../.env")
load_dotenv(dotenv_path=dotenv_path)

# Retrieve database credentials from environment variables
SSH_HOST = os.getenv("SSH_HOST")  # e.g., 155.xxx.xxx.xx8
SSH_PORT = int(os.getenv("SSH_PORT", 22))  # Default SSH port
SSH_USER = os.getenv("SSH_USER")  # e.g., "xxxxx"
SSH_PASSWORD = os.getenv("SSH_PASSWORD")  # Your SSH password

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")  # Localhost since we use SSH tunnel
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER", "dbuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_db_password")
DB_NAME = os.getenv("DB_NAME", "vdsdata")
SCHEMA_NAME = "vds_v2"
TABLE_NAME = f"{SCHEMA_NAME}.vds_documents"  # Specify schema explicitly
VECTOR_DIM = 768

# Establish SSH tunnel
server = SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASSWORD,
    remote_bind_address=(DB_HOST, DB_PORT),
    local_bind_address=("127.0.0.1", 5433)  # Redirect to local port
)
server.start()

# Update DB_PORT to the tunneled local port
DB_PORT = 5433

# Function to connect to PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host="127.0.0.1",
            port=DB_PORT  # Use the local port from SSH tunnel
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
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

# Function to perform similarity search
def similarity_search(sentence, vector_dim=VECTOR_DIM, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query_embedding = np.random.rand(vector_dim).tolist()  # Dummy embedding, replace with real embeddings

        # Perform similarity search
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

        print(f"🔍 Top {top_k} Similarity Search Results for: '{sentence}'")
        for i, (file_name, content, score) in enumerate(results, start=1):
            decoded_url = decode_base64_to_url(file_name[:-4]) if file_name.endswith(".pdf") else decode_base64_to_url(file_name)
            print(f"\nResult {i}:\n  - Webpage: {decoded_url}\n  - Score: {round(score, 4)}\n  - Context: {content[:500]}...")

    except Exception as e:
        print(f"❌ Error performing similarity search: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to perform relevance search
def relevance_search(sentence, vector_dim=VECTOR_DIM, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query_embedding = np.random.rand(vector_dim).tolist()  # Dummy embedding, replace with real embeddings

        # Perform relevance search
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

        print(f"🔍 Top {top_k} Relevance Search Results for: '{sentence}'")
        for i, (file_name, content, score) in enumerate(results, start=1):
            decoded_url = decode_base64_to_url(file_name[:-4]) if file_name.endswith(".pdf") else decode_base64_to_url(file_name)
            print(f"\nResult {i}:\n  - Webpage: {decoded_url}\n  - Score: {round(score, 4)}\n  - Context: {content[:500]}...")

    except Exception as e:
        print(f"❌ Error performing relevance search: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Parameters
    sentence = "What are the key components of a toggle?"

    # Test database connection
    check_database()

    # Perform similarity search
    similarity_search(sentence)

    # Perform relevance search
    relevance_search(sentence)

    # Close SSH tunnel after execution
    server.stop()
    print("🔒 SSH Tunnel closed.")
