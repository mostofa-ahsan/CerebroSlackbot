import chromadb
from chromadb.config import Settings

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "cerebro_collection_1"

def check_none_embeddings():
    print("### Checking Embeddings with None Values in Chroma DB Collection ###")

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

    # Check for None embeddings
    none_embeddings_count = 0
    none_embedding_indices = []
    if embeddings is not None:
        for idx, e in enumerate(embeddings):
            if e is None:
                none_embeddings_count += 1
                none_embedding_indices.append(idx)

    print(f"✅ Total records in collection: {total_records}")
    print(f"❌ Embeddings with None values: {none_embeddings_count}")

    # If there are any None embeddings, list their indices
    if none_embeddings_count > 0:
        print("Indices of records with None embeddings:")
        print(none_embedding_indices[:10])  # Show only the first 10 for brevity
    else:
        print("✅ No embeddings with None values detected.")

    print("### None Embeddings Check Completed ###")


if __name__ == "__main__":
    check_none_embeddings()
