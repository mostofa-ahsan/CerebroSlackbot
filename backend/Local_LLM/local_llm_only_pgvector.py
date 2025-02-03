import os
import streamlit as st
from flask import Flask, request, jsonify
import psycopg2
import numpy as np
from langchain.embeddings import HuggingFaceEmbeddings
from langfuse import Langfuse  # Ensure you have LangFuse installed

# Configuration
MODEL_PATH = "../../models/all-mpnet-base-v2"
CACHE_FOLDER = "../../cache"

# PostgreSQL Config for PGVector
PG_USER = "ahsamo6"
PG_PASSWORD = "your_password"
PG_HOST = "localhost"
PG_PORT = 5432
PG_DB = "postgres"
PG_TABLE = "vds_documents"

# Initialize LangFuse for query tracking
LANGFUSE_SECRET = os.getenv("LANGFUSE_SECRET", "sk-lf-aef0630a-83ef-478a-a782-843783aa093a")
langfuse = Langfuse(api_key=LANGFUSE_SECRET)

# Initialize Flask App
app = Flask(__name__)

# Initialize embedding function
embedding_function = HuggingFaceEmbeddings(model_name=MODEL_PATH, cache_folder=CACHE_FOLDER)

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
        # Generate embedding for the input sentence (dummy embedding for now)
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

# Flask API for similarity search
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

# Streamlit UI
st.title("Local LLM Chat Interface")
st.subheader("Query the LLM using PGVector")

user_input = st.text_input("Enter your question:")
if st.button("Search"):
    if user_input:
        with st.spinner("Searching..."):
            response = query_llm().json
            st.subheader("Results")
            
            st.write("### PGVector Results:")
            for idx, result in enumerate(response.get("pgvector_results", [])):
                st.write(f"**Result {idx + 1}:**")
                st.write(f"**File:** {result['file']}")
                st.write(f"**Context:** {result['context'][:500]}...")
                st.write(f"**Score:** {round(result['score'], 4)}")
                st.write("---")
    else:
        st.error("Please enter a query.")

# Run Flask in the background
if __name__ == "__main__":
    app.run(port=5000, debug=True)
