import chromadb
from chromadb.config import Settings

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "cerebro_collection_1"

def query_cerebro_collection():
    print("### Running Query Test for Chroma DB Collection ###")

    # Initialize Chroma DB client
    client = chromadb.Client(
        Settings(
            persist_directory=CHROMA_DB_DIR,
            chroma_db_impl="duckdb+parquet"
        )
    )

    # Load collection
    collection = client.get_collection(COLLECTION_NAME)
    print(f"✅ Collection '{COLLECTION_NAME}' found")

    # Run a test query
    query_text = "What is the primary function of this vehicle?"
    results = collection.query(
        query_texts=[query_text],
        n_results=5
    )

    print(f"Query: {query_text}")
    print(f"✅ Query successful. Retrieved {len(results['documents'][0])} results:")
    for i, (doc, score, meta) in enumerate(zip(results["documents"][0], results["distances"][0], results["metadatas"][0])):
        print(f"Result {i+1}:")
        print(f"  - Context: {doc}")
        print(f"  - Relevancy Score: {score}")
        print(f"  - Metadata: {meta}")

    print("### Query Test Completed ###")


if __name__ == "__main__":
    query_cerebro_collection()
