import os
import psycopg2
import numpy as np
import base64
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
from langchain.vectorstores import PGVector
from langchain.embeddings import HuggingFaceEmbeddings
from local_llm import call_llm
from prompts import SYSTEM_PROMPT

# Load environment variables
dotenv_path = os.path.abspath("../../../.env")
load_dotenv(dotenv_path=dotenv_path)

# SSH and DB Configuration
SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
SSH_USER = os.getenv("SSH_USER")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

COLLECTION_NAME = "VDS_Collection"

# Load embedding model
SENTENCE_MODEL_PATH = "../../models/all-mpnet-base-v2"
embedding_model = HuggingFaceEmbeddings(model_name=SENTENCE_MODEL_PATH)

# Establish SSH tunnel
server = SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASSWORD,
    remote_bind_address=(DB_HOST, DB_PORT),
    local_bind_address=("127.0.0.1", 5433)
)
server.start()
DB_PORT = 5433  

# Connect to PGVector
def get_pgvector_store():
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{DB_PORT}/{DB_NAME}"
    return PGVector(connection_string=connection_string, embedding_function=embedding_model, collection_name=COLLECTION_NAME)

# Process query and retrieve context
def process_query(query):
    vectorstore = get_pgvector_store()
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    retrieved_docs = retriever.get_relevant_documents(query)

    context = "\n".join([doc.page_content for doc in retrieved_docs])
    prompt = f"SYSTEM: {SYSTEM_PROMPT}\n\nUse the following context to answer:\n{context}\n\nQuestion: {query}"

    response = call_llm(prompt)
    return response

if __name__ == "__main__":
    user_query = "What are the key components of a toggle?"
    response = process_query(user_query)
    print(f"\n🤖 Response:\n{response}")
    server.stop()
    print("🔒 SSH Tunnel closed.")
