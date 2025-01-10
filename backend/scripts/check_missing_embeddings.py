import chromadb
from chromadb.config import Settings

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "cerebro_collection_1"

def check_missing_embeddings():
    print("### Checking Missing Embeddings in Chroma DB Collection ###")

    # Initialize Chroma DB client
    client = chromadb.Client(
        Settings(
            persist_directory=CHROMA_DB_DIR,
            chroma_db_impl="duckdb+parquet"
        )
    )

    # Retrieve collection
    collection = client.get_collection(COLLECTION_NAME)
    print(f"✅ Collection '{COLLECTION_NAME}' found")

    # Get all records
    data = collection.get()
    total_records = len(data["ids"])
    embeddings = data["embeddings"]

    # Check for missing embeddings
    missing_embeddings_count = 0
    if embeddings is not None:
        missing_embeddings_count = sum(1 for e in embeddings if e is None)

    print(f"✅ Total records in collection: {total_records}")
    print(f"❌ Missing embeddings: {missing_embeddings_count}")
    print(f"✅ Embeddings present: {total_records - missing_embeddings_count}")

    print("### Missing Embeddings Check Completed ###")


if __name__ == "__main__":
    check_missing_embeddings()
