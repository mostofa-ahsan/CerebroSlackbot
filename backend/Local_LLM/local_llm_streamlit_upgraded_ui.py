import os
import streamlit as st
import requests

# Flask API URL (Running separately)
FLASK_API_URL = "http://localhost:5000/query"

st.title("Local LLM Chat Interface")
st.subheader("Query the LLM using PGVector")

user_input = st.text_input("Enter your question:")
if st.button("Search"):
    if user_input:
        with st.spinner("Searching..."):
            response = requests.post(FLASK_API_URL, json={"query": user_input})
            if response.status_code == 200:
                data = response.json()
                st.subheader("Results")

                st.write("### PGVector Results:")
                for idx, result in enumerate(data.get("pgvector_results", [])):
                    st.write(f"**Result {idx + 1}:**")
                    st.write(f"**File:** {result['file']}")
                    st.write(f"**Context:** {result['context'][:500]}...")
                    st.write(f"**Score:** {round(result['score'], 4)}")
                    st.write("---")
            else:
                st.error(f"Error: {response.json().get('error', 'Unknown error')}")
    else:
        st.error("Please enter a query.")
