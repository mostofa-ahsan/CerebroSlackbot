import psycopg2
import numpy as np
import base64

# Function to connect to PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="ahsamo6",
            password="your_password",
            host="localhost",
            port=5432
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        exit()

# Function to test database connection and table existence
def check_database(table_name):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT to_regclass('{table_name}');")
        result = cursor.fetchone()
        if result[0]:
            print(f"Table '{table_name}' exists.")
        else:
            print(f"Table '{table_name}' does not exist.")
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to decode Base64 webpage link
def decode_base64_to_url(b64_string):
    """Decode a base64 string to a URL."""
    return base64.urlsafe_b64decode(b64_string.encode()).decode()

# Function to perform similarity search
def similarity_search(sentence, table_name, vector_dim=768, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        # Generate embedding for the input sentence (dummy embedding for now)
        query_embedding = np.random.rand(vector_dim).tolist()

        # Perform similarity search using min-max normalization
        cursor.execute(f"""
            WITH similarity_scores AS (
                SELECT file_name, content, 
                    (embedding <-> %s::VECTOR) AS raw_score
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

        print(f"Top {top_k} Similarity Search Results for: '{sentence}'")
        for i, (file_name, content, score) in enumerate(results, start=1):
            # decoded_webpage = decode_webpage(file_name)
            if file_name.endswith(".pdf"):
                decoded_url = decode_base64_to_url(file_name[:-4])
                print(f"  - RAW Webpage: {decoded_url}")
            else:
                print(f"  - Decoded Webpage: {decode_base64_to_url(file_name)}")
                print("  - Saved Webpage:", file_name)
            print(f"\nResult {i}:\n  - Webpage: {decoded_url}\n  - Score: {round(score, 4)}\n  - Context: {content[:500]}{'...' if len(content) > 500 else ''}")
    except Exception as e:
        print(f"Error performing similarity search: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to perform relevance search
def relevance_search(sentence, table_name, vector_dim=768, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        # Generate embedding for the input sentence (dummy embedding for now)
        query_embedding = np.random.rand(vector_dim).tolist()

        # Perform relevance search using min-max normalization
        cursor.execute(f"""
            WITH relevance_scores AS (
                SELECT file_name, content, 
                    1 - (embedding <-> %s::VECTOR) AS raw_score
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

        print(f"Top {top_k} Relevance Search Results for: '{sentence}'")
        for i, (file_name, content, score) in enumerate(results, start=1):
            # decoded_webpage = decode_webpage(file_name)
            if file_name.endswith(".pdf"):
                decoded_url = decode_base64_to_url(file_name[:-4])
                print(f"  - RAW Webpage: {decoded_url}")
            else:
                print(f"  - Decoded Webpage: {decode_base64_to_url(file_name)}")
                print("  - Saved Webpage:", file_name)
            print(f"\nResult {i}:\n  - Webpage: {decoded_url}\n  - Score: {round(score, 4)}\n  - Context: {content[:500]}{'...' if len(content) > 500 else ''}")
    except Exception as e:
        print(f"Error performing relevance search: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Parameters
    table_name = "vds_documents_3"
    sentence = "What are the key components of a toggle?"

    # Test database
    check_database(table_name)

    # Perform similarity search
    similarity_search(sentence, table_name)

    # Perform relevance search
    relevance_search(sentence, table_name)
