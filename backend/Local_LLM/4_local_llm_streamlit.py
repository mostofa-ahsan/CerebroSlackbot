import streamlit as st
import psycopg2
import numpy as np
import requests
import json
from services import call_ai_service
from query_pgvector import similarity_search, relevance_search

# Database connection function
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
        st.error(f"Error connecting to database: {e}")
        return None

# Streamlit UI
st.title("Local LLM Chat Interface")
st.subheader("Query the LLM using PGVector")

# User input
user_query = st.text_input("Enter your question:")
if st.button("Search") and user_query:
    st.write("Searching...")
    
    # Perform similarity search
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        table_name = "vds_documents"
        vector_dim = 768
        top_k = 10

        try:
            results = similarity_search(user_query, table_name, vector_dim, top_k)
            if results:
                st.write("### Top Similarity Search Results")
                for i, (file_name, content, score) in enumerate(results, start=1):
                    st.write(f"#### Result {i}:")
                    st.write(f"- **File:** {file_name}")
                    st.write(f"- **Score:** {round(score, 4)}")
                    st.write(f"- **Context:** {content[:500]}...")
            else:
                st.write("No relevant documents found.")
        except Exception as e:
            st.error(f"Error performing search: {e}")
        finally:
            cursor.close()
            conn.close()
    
    # Query LLM
    response = call_ai_service(user_query)
    if response:
        st.subheader("LLM Response")
        st.write(response)
    else:
        st.error("Failed to fetch response from LLM.")
