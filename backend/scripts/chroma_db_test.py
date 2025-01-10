import chromadb
from chromadb.config import Settings

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "pages"

def test_chroma_db():
    print("### Running Chroma DB Ingestion Tests ###")

    # Step 1: Initialize Chroma DB Client
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

        # Check if data exists
        if not collection_data or not collection_data.get("ids"):
            print(f"❌ No data found in collection '{COLLECTION_NAME}'")
            return

        total_records = len(collection_data["ids"])
        print(f"✅ Total records in collection: {total_records}")

        # Inspect first 5 records
        print("✅ Inspecting the first 5 records:")
        for i in range(min(5, total_records)):
            record = {
                "id": collection_data["ids"][i],
                "metadata": collection_data["metadatas"][i] if collection_data["metadatas"] else None,
                "embedding": collection_data["embeddings"][i] if collection_data["embeddings"] else None
            }
            print(f"Record {i + 1}: {record}")
            if record["embedding"] is None:
                print(f"⚠️ Warning: Record {i + 1} has no embedding")

        # Check for records with missing embeddings
        missing_embeddings_count = sum(1 for emb in collection_data["embeddings"] if emb is None)
        if missing_embeddings_count > 0:
            print(f"⚠️ Warning: {missing_embeddings_count}/{total_records} records have missing embeddings")
        else:
            print("✅ All records have embeddings")

    except Exception as e:
        print(f"❌ Failed to inspect data in collection '{COLLECTION_NAME}': {e}")
        return

    print("### Chroma DB Ingestion Tests Completed ###")


if __name__ == "__main__":
    test_chroma_db()
