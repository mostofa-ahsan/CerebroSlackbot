import chromadb
from chromadb.config import Settings

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "pages"

def debug_embeddings():
    print("### Debugging Embeddings in Chroma DB ###")

    # Step 1: Connect to Chroma DB
    try:
        client = chromadb.Client(
            Settings(
                persist_directory=CHROMA_DB_DIR,
                chroma_db_impl="duckdb+parquet"
            )
        )
        print("✅ Successfully connected to Chroma DB")
    except Exception as e:
        print(f"❌ Failed to connect to Chroma DB: {e}")
        return

    # Step 2: Verify and Retrieve Collection
    try:
        collection = client.get_collection(COLLECTION_NAME)
        print(f"✅ Collection '{COLLECTION_NAME}' found")
    except Exception as e:
        print(f"❌ Collection '{COLLECTION_NAME}' not found: {e}")
        return

    # Step 3: Retrieve and Inspect Data
    try:
        collection_data = collection.get()

        # Debug the structure of the retrieved data
        print("✅ Retrieved data from collection. Inspecting structure:")
        for key, value in collection_data.items():
            print(f"- Key: {key}, Type: {type(value)}, Example: {value[:5] if isinstance(value, list) else value}")

    except Exception as e:
        print(f"❌ Failed to retrieve data from collection '{COLLECTION_NAME}': {e}")
        return

    print("### Debugging Completed ###")


if __name__ == "__main__":
    debug_embeddings()
