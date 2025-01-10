import chromadb
from chromadb.config import Settings

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "pages"

def validate_embeddings_after_ingestion():
    print("### Validating Embeddings in Chroma DB ###")
    
    # Connect to Chroma DB
    client = chromadb.Client(
        Settings(
            persist_directory=CHROMA_DB_DIR,
            chroma_db_impl="duckdb+parquet"
        )
    )

    # Get collection
    collection = client.get_collection(COLLECTION_NAME)
    print(f"✅ Collection '{COLLECTION_NAME}' found")

    # Fetch all data
    data = collection.get()
    print(f"✅ Total records in collection: {len(data['ids'])}")

    # Check embeddings
    if data["embeddings"] is None:
        print("❌ Embeddings are missing in the collection")
    else:
        print(f"✅ Embedding type: {type(data['embeddings'])}")
        print(f"✅ Example embedding: {data['embeddings'][0][:5]}")

if __name__ == "__main__":
    validate_embeddings_after_ingestion()
