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

# Function to decode Base64 webpage links
def decode_webpage(base64_string):
    try:
        return base64.b64decode(base64_string).decode('utf-8')
    except Exception as e:
        return f"Error decoding webpage: {e}"

# Function to perform similarity search
def similarity_search(sentence, table_name, vector_dim=768, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        # Generate embedding for the input sentence (dummy embedding for now)
        query_embedding = np.random.rand(vector_dim).tolist()

        # Perform similarity search using normalized cosine similarity
        cursor.execute(f"""
            SELECT file_name, content, 
                (1 - (embedding <-> %s::VECTOR)) AS similarity_score
            FROM {table_name}
            ORDER BY similarity_score DESC
            LIMIT {top_k};
        """, (query_embedding,))
        results = cursor.fetchall()

        print(f"Top {top_k} Similarity Search Results for: '{sentence}'")
        for i, (file_name, content, score) in enumerate(results, start=1):
            decoded_webpage = decode_webpage(file_name)
            print(f"\nResult {i}:\n  - Webpage: {decoded_webpage}\n  - Score: {round(score, 4)}\n  - Context: {content[:500]}{'...' if len(content) > 500 else ''}")
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

        # Perform relevance search using normalized scores
        cursor.execute(f"""
            SELECT file_name, content, 
                (1 - (embedding <-> %s::VECTOR)) AS relevance_score
            FROM {table_name}
            ORDER BY relevance_score DESC
            LIMIT {top_k};
        """, (query_embedding,))
        results = cursor.fetchall()

        print(f"Top {top_k} Relevance Search Results for: '{sentence}'")
        for i, (file_name, content, score) in enumerate(results, start=1):
            decoded_webpage = decode_webpage(file_name)
            print(f"\nResult {i}:\n  - Webpage: {decoded_webpage}\n  - Score: {round(score, 4)}\n  - Context: {content[:500]}{'...' if len(content) > 500 else ''}")
    except Exception as e:
        print(f"Error performing relevance search: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Parameters
    table_name = "vds_documents"
    sentence = "What are the key components of a toggle?"

    # Test database
    check_database(table_name)

    # Perform similarity search
    similarity_search(sentence, table_name)

    # Perform relevance search
    relevance_search(sentence, table_name)
