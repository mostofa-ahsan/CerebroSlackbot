import chromadb
from chromadb.config import Settings

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "cerebro_collection_1"

def debug_cerebro_collection():
    print("### Debugging Collection 'cerebro_collection_1' ###")

    # Connect to Chroma DB
    client = chromadb.Client(
        Settings(
            persist_directory=CHROMA_DB_DIR,
            chroma_db_impl="duckdb+parquet"
        )
    )

    # Retrieve the collection
    try:
        collection = client.get_collection(COLLECTION_NAME)
        print(f"✅ Collection '{COLLECTION_NAME}' found")
    except Exception as e:
        print(f"❌ Failed to retrieve collection '{COLLECTION_NAME}': {e}")
        return

    # Fetch all data from the collection
    try:
        data = collection.get()
        print(f"✅ Retrieved data from collection. Total records: {len(data['ids'])}")
        
        # Print structure of data
        print("✅ Inspecting data structure:")
        for key, value in data.items():
            print(f"- Key: {key}, Type: {type(value)}, Example: {value[:5] if isinstance(value, list) else value}")

        # Analyze embeddings
        embeddings = data.get("embeddings")
        if embeddings is None:
            print("⚠️ Embeddings key is None. Data ingestion might have skipped embeddings.")
        else:
            print(f"✅ Embeddings found. Total embeddings: {len(embeddings)}")
            print(f"✅ Example embedding (first 5 values): {embeddings[0][:5]}")

    except Exception as e:
        print(f"❌ Failed to debug data in collection '{COLLECTION_NAME}': {e}")

    print("### Debugging Completed ###")


if __name__ == "__main__":
    debug_cerebro_collection()
