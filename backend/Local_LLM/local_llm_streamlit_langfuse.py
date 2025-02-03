import os
import streamlit as st
from flask import Flask, request, jsonify
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langfuse import Langfuse
import logging
import base64

# Configuration
CHROMA_DB_DIR = "../../data/cerebro_chroma_db_v2"
COLLECTION_NAME = "cerebro_vds_v2"
MODEL_PATH = "../../models/all-mpnet-base-v2"
CACHE_FOLDER = "../../cache"
LANGFUSE_SECRET = os.getenv("LANGFUSE_SECRET")

# Initialize LangFuse for context tracking
langfuse = Langfuse(secret=LANGFUSE_SECRET)

# Initialize Flask app
app = Flask(__name__)

# Initialize embedding model
embedding_function = HuggingFaceEmbeddings(model_name=MODEL_PATH, cache_folder=CACHE_FOLDER)

# Load ChromaDB collection
vectorstore = Chroma(
    persist_directory=CHROMA_DB_DIR,
    collection_name=COLLECTION_NAME,
    embedding_function=embedding_function
)

# Function to decode base64 encoded URLs
def decode_base64_to_url(b64_string):
    try:
        return base64.urlsafe_b64decode(b64_string.encode()).decode()
    except:
        return "Unknown Source"

# Function to query ChromaDB
def retrieve_docs(query_text, top_k=3):
    """
    Retrieve top_k relevant documents from ChromaDB
    """
    results = vectorstore.similarity_search_with_score(query_text, k=top_k)
    retrieved_data = []

    for idx, (doc, score) in enumerate(results, start=1):
        metadata = doc.metadata
        webpage = decode_base64_to_url(metadata.get("source", "N/A"))
        retrieved_data.append({"context": doc.page_content, "score": round(1 - score, 2), "webpage": webpage})

    return retrieved_data

# Function to process LLM response
def answer_question(query):
    """
    Retrieves context from ChromaDB and answers the question using LLM.
    """
    retrieved_docs = retrieve_docs(query, top_k=3)

    if not retrieved_docs:
        return "No relevant information found."

    # Combine retrieved contexts
    context = " ".join([doc["context"] for doc in retrieved_docs])

    # Track interaction with LangFuse
    langfuse.track("query", metadata={"query": query, "retrieved_docs": retrieved_docs})

    # Generate response using ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful AI assistant."),
            ("user", f"Use the following context to answer the question:\n\n{context}\n\nQuestion: {query}")
        ]
    )
    
    # Mock response (Replace with LLM call)
    response = f"Mock Response: The best answer for '{query}' based on retrieved context."

    return response, retrieved_docs

# Flask API Endpoint
@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    response, retrieved_docs = answer_question(query)
    return jsonify({"response": response, "retrieved_docs": retrieved_docs})

# Streamlit UI
def streamlit_ui():
    st.title("Local LLM Chatbot with ChromaDB & LangFuse")
    query = st.text_input("Enter your question:")
    
    if st.button("Ask"):
        if query:
            response, retrieved_docs = answer_question(query)
            st.subheader("LLM Response:")
            st.write(response)

            st.subheader("Retrieved Documents:")
            for idx, doc in enumerate(retrieved_docs, start=1):
                st.markdown(f"**{idx}. Score:** {doc['score']}")
                st.markdown(f"**Context:** {doc['context'][:500]}...")
                st.markdown(f"**Webpage:** [{doc['webpage']}]({doc['webpage']})")
        else:
            st.warning("Please enter a query.")

# Run Streamlit UI
if __name__ == "__main__":
    import threading

    flask_thread = threading.Thread(target=lambda: app.run(port=5001, debug=True, use_reloader=False))
    flask_thread.start()

    streamlit_ui()
