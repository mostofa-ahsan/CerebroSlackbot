import streamlit as st
import requests
import json
from services import call_ai_service

# Streamlit UI Config
st.set_page_config(page_title="Local LLM Chat Interface", layout="wide")

# App Title
st.markdown("<h1 style='text-align: center;'>📖 Local LLM Chat Interface</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Query the LLM using PGVector</h3>", unsafe_allow_html=True)

# User Input Field
user_query = st.text_input("Enter your question:", "")

# Search Type Selection (Similarity or Relevance)
search_type = st.radio("Choose Search Type:", ["similarity", "relevance"])

# Button to trigger search
if st.button("🔍 Search"):
    if user_query.strip():
        st.info("⏳ Processing your query...")

        try:
            # Call the AI service from services.py
            response = call_ai_service(user_query, search_type=search_type)

            # Display Response
            st.success("✅ Query successful!")
            st.markdown(f"### 🤖 LLM Response:")
            st.write(response)

        except requests.exceptions.ConnectionError:
            st.error("❌ Error: Unable to connect to the LLM server. Make sure it's running.")
        except json.JSONDecodeError:
            st.error("❌ Error: Invalid JSON response from server.")
        except Exception as e:
            st.error(f"⚠️ Unexpected error: {str(e)}")
    else:
        st.warning("⚠️ Please enter a valid query.")

# Run with: `streamlit run local_llm_streamlit.py`
