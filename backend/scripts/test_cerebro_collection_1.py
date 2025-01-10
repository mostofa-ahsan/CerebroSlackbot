import chromadb
from chromadb.config import Settings

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "cerebro_collection_v2"

def query_cerebro_collection():
    print("### Running Query Test for Chroma DB Collection ###")

    # Initialize Chroma DB client
    client = chromadb.Client(
        Settings(
            persist_directory=CHROMA_DB_DIR,
            chroma_db_impl="duckdb+parquet"
        )
    )

    # Get the collection
    try:
        collection = client.get_collection(COLLECTION_NAME)
        print(f"✅ Collection '{COLLECTION_NAME}' found")
    except Exception as e:
        print(f"❌ Failed to retrieve collection '{COLLECTION_NAME}': {e}")
        return

    # Define the query
    query_text = "What are the guidelines for digital advertising?"
    print(f"Query: {query_text}")

    # Perform the query
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=5
        )
        print(f"✅ Query successful. Retrieved {len(results['documents'][0])} results:")

        # Display the results
        for idx, (context, metadata, score) in enumerate(
                zip(results["documents"][0], results["metadatas"][0], results["distances"])):
            print(f"Result {idx + 1}:")
            print(f"  - Context: {context if context else 'None'}")
            print(f"  - Relevancy Score: {score}")
            print(f"  - Metadata: {metadata}")
    except Exception as e:
        print(f"❌ Query failed: {e}")

    print("### Query Test Completed ###")


if __name__ == "__main__":
    query_cerebro_collection()
