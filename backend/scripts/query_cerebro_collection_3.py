import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "cerebro_v3"
LOCAL_MODEL_PATH = "../models/all-mpnet-base-v2"  # Path to the locally downloaded model

def query_cerebro_v3():
    print("### Running Query Test for Chroma DB Collection ###")

    ## Set up embedding function
    # embedding_function = SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")


    # Initialize embedding function using the local model
    embedding_function  = SentenceTransformerEmbeddingFunction(model_name=LOCAL_MODEL_PATH)

    # Initialize Chroma DB client
    client = chromadb.Client(Settings(persist_directory=CHROMA_DB_DIR, chroma_db_impl="duckdb+parquet"))
    
    # Load collection with the specified embedding function
    collection = client.get_collection(
        COLLECTION_NAME,
        embedding_function=embedding_function
    )
    print(f"✅ Collection '{COLLECTION_NAME}' found")

    # Define the query
    query_text = "What is verizon brandcentral is used for"

    try:
        # Execute the query
        results = collection.query(
            query_texts=[query_text],
            n_results=10,  # Retrieve top 10 results
        )
        print(f"✅ Query successful. Retrieved results:")

        # Print results field by field
        for i, (contexts, scores, metadatas) in enumerate(
            zip(results["documents"], results["distances"], results["metadatas"]), start=1
        ):
            for context, score, metadata in zip(contexts, scores, metadatas):
                print(f"\nResult {i}:")
                print(f"  - Context: {context[:500] + '...' if len(context) > 500 else context}")
                print(f"  - Relevancy Score: {score}")
                print(f"  - Chunk ID: {metadata.get('chunk_id', 'N/A')}")
                print(f"  - Embedding ID: {metadata.get('embedding_id', 'N/A')}")
                print(f"  - Webpage: {metadata.get('source', 'N/A')}")
                print(f"  - Saved Webpage: {metadata.get('saved_webpage', 'N/A')}")

    except Exception as e:
        print(f"❌ Query failed: {e}")

    print("\n### Query Test Completed ###")

if __name__ == "__main__":
    query_cerebro_v3()
