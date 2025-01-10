import chromadb
from chromadb.config import Settings

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "pages"

def test_embeddings_in_chroma_db():
    print("### Running Embedding Validation Test ###")

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

        # Count records with and without embeddings
        total_records = len(data["ids"])
        records_with_embeddings = sum(
            1 for embedding in data["embeddings"] if embedding is not None
        )
        records_without_embeddings = total_records - records_with_embeddings

        # Display results
        print(f"✅ Records with embeddings: {records_with_embeddings}")
        print(f"⚠️ Records without embeddings: {records_without_embeddings}")

        # Print a few sample records
        print("✅ Sample Records:")
        for i, (record_id, metadata, embedding) in enumerate(zip(data["ids"], data["metadatas"], data["embeddings"])):
            print(f"Record {i + 1}:")
            print(f"- ID: {record_id}")
            print(f"- Metadata: {metadata}")
            print(f"- Embedding (first 5 values): {embedding[:5] if embedding else None}")
            if i >= 4:  # Display only the first 5 records
                break

    except Exception as e:
        print(f"❌ Failed to analyze embeddings in collection '{COLLECTION_NAME}': {e}")

    print("### Embedding Validation Test Completed ###")


if __name__ == "__main__":
    test_embeddings_in_chroma_db()
