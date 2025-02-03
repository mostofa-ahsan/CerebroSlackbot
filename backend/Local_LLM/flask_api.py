from flask import Flask, request, jsonify
import psycopg2
import numpy as np
from langfuse import Langfuse

# PostgreSQL Configuration
PG_USER = "ahsamo6"
PG_PASSWORD = "your_password"
PG_HOST = "localhost"
PG_PORT = 5432
PG_DB = "postgres"
PG_TABLE = "vds_documents"

# Initialize LangFuse for tracking
LANGFUSE_SECRET = os.getenv("LANGFUSE_SECRET", "sk-lf-aef0630a-83ef-478a-a782-843783aa093a")
langfuse = Langfuse(api_key=LANGFUSE_SECRET)

# Initialize Flask App
app = Flask(__name__)

# Function to connect to PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        exit()

# Function to perform similarity search using PGVector
def similarity_search_pg(sentence, vector_dim=768, top_k=10):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query_embedding = np.random.rand(vector_dim).tolist()

        cursor.execute(f"""
            WITH similarity_scores AS (
                SELECT file_name, content,
                    (embedding <-> %s::VECTOR) AS raw_score
                FROM {PG_TABLE}
            ),
            normalized_scores AS (
                SELECT file_name, content,
                    (1 - (raw_score - MIN(raw_score) OVER ()) /
                    (MAX(raw_score) OVER () - MIN(raw_score) OVER ())) AS similarity_score
                FROM similarity_scores
            )
            SELECT file_name, content, similarity_score
            FROM normalized_scores
            ORDER BY similarity_score DESC
            LIMIT {top_k};
        """, (query_embedding,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error performing similarity search: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# Flask API for querying
@app.route("/query", methods=["POST"])
def query_llm():
    data = request.json
    user_query = data.get("query", "")

    if not user_query:
        return jsonify({"error": "Query cannot be empty"}), 400

    # Retrieve context from PGVector
    pg_results = similarity_search_pg(user_query, top_k=5)

    # Track query using LangFuse
    langfuse.track("user_query", {"query": user_query, "pg_results": len(pg_results)})

    response = {
        "query": user_query,
        "pgvector_results": [{"file": res[0], "context": res[1], "score": res[2]} for res in pg_results]
    }
    
    return jsonify(response)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
