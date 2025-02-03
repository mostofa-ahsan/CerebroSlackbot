import streamlit as st
import requests
import psycopg2
import numpy as np
from flask import Flask, request, jsonify
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langfuse import Langfuse
import os

# PGVector Configuration
PG_USER = "ahsamo6"
PG_PASSWORD = "your_password"
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "postgres"
TABLE_NAME = "vds_documents"
VECTOR_DIM = 768

# Initialize LangFuse
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "your_public_key")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "your_secret_key")
langfuse = Langfuse(public_key=LANGFUSE_PUBLIC_KEY, secret_key=LANGFUSE_SECRET_KEY)

# Flask API Setup
app = Flask(__name__)

def connect_to_db():
    """Connects to PGVector database."""
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
        return None

def perform_vector_search(query_embedding, top_k=10, search_type='similarity'):
    """Performs vector similarity or relevance search in PGVector."""
    conn = connect_to_db()
    if not conn:
        return []
    
    cursor = conn.cursor()
    try:
        sql_query = f"""
            WITH similarity_scores AS (
                SELECT file_name, content, 
                (embedding <-> %s::VECTOR) AS raw_score
                FROM {TABLE_NAME}
            ),
            normalized_scores AS (
                SELECT file_name, content, 
                (1 - (raw_score - MIN(raw_score) OVER()) / 
                (MAX(raw_score) OVER() - MIN(raw_score) OVER())) AS search_score
                FROM similarity_scores
            )
            SELECT file_name, content, search_score
            FROM normalized_scores
            ORDER BY search_score DESC
            LIMIT {top_k};
        """
        
        cursor.execute(sql_query, (query_embedding,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error performing vector search: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

@app.route("/query", methods=["POST"])
def query_llm():
    """Handles query requests from Streamlit UI."""
    data = request.json
    user_query = data.get("query", "")
    
    # Generate query embedding (dummy for now, replace with real model)
    query_embedding = np.random.rand(VECTOR_DIM).tolist()
    
    # Perform search
    search_results = perform_vector_search(query_embedding, search_type='similarity')
    
    langfuse.trace("user_query", user_query, "pg_results", len(search_results))
    
    return jsonify({"results": search_results})

# Streamlit UI
st.title("Local LLM Chat Interface")
st.subheader("Query the LLM using PGVector")

user_input = st.text_input("Enter your question:", "")

if st.button("Search"):
    response = requests.post("http://127.0.0.1:5000/query", json={"query": user_input})
    if response.status_code == 200:
        results = response.json()["results"]
        for i, (file_name, content, score) in enumerate(results, start=1):
            st.write(f"**Result {i}:**")
            st.write(f"- File: {file_name}")
            st.write(f"- Score: {round(score, 4)}")
            st.write(f"- Context: {content[:500]}{'...' if len(content) > 500 else ''}")
    else:
        st.error(f"Error: {response.json().get('error', 'Unknown error')}")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
