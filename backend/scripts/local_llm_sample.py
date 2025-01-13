import os
from rich import print
from mlx_lm import load, generate
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import chromadb

FALCON_PATH = os.environ['FALCON_PATH']
CHROMA_DB_DIR = "../data_ingestion/data/cerebro_chroma_db"
COLLECTION_NAME = "cerebro_vds"
LOCAL_MODEL_PATH = "./models/all-mpnet-base-v2"

# Load the local model
model, tokenizer = load(FALCON_PATH)

# Initialize ChromaDB client
embedding_function = SentenceTransformerEmbeddingFunction(model_name=LOCAL_MODEL_PATH)
client = chromadb.Client(Settings(persist_directory=CHROMA_DB_DIR, chroma_db_impl="duckdb+parquet"))

# Load the collection
collection = client.get_collection(COLLECTION_NAME, embedding_function=embedding_function)

def query_chromadb(query_text: str, n_results: int = 10):
    """
    Query ChromaDB and retrieve the most relevant context for the given query.
    """
    try:
        results = collection.query(query_texts=[query_text], n_results=n_results)
        contexts = [result[:500] + "..." if len(result) > 500 else result for result in results["documents"]]
        return contexts
    except Exception as e:
        print(f"[red]Error querying ChromaDB: {e}[/red]")
        return []

def call_llm(user_query: str) -> str:
    """
    Calls the local LLM with the user query and context from ChromaDB.
    """
    # Retrieve context from ChromaDB
    chromadb_contexts = query_chromadb(user_query)
    combined_context = " ".join(chromadb_contexts)

    # Create a meta-prompt with the retrieved context
    meta_prompt = (
        "You are a virtual design assistant working for the Verizon company. "
        "Please answer the following question about the brand design style guide: {}\n\n"
        "Context from database:\n{}"
    )
    prompt = meta_prompt.format(user_query, combined_context)

    print(f"[blue]Prompt:[/blue] [yellow]{prompt}[/yellow]")

    # Generate response
    response = generate(model, tokenizer, prompt=prompt, verbose=True)

    print(f"[blue]Response:[/blue] [yellow][bold]{response}[/bold][/yellow]")
    return response
