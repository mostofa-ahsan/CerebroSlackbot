import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from rich import print
import base64

# Configuration
CHROMA_DB_DIR = "../../data/cerebro_chroma_db_v1"
COLLECTION_NAME = "cerebro_vds_v1_2"
LOCAL_MODEL_PATH = "../../models/all-mpnet-base-v2"  # Path to the locally downloaded model


def decode_base64_to_url(b64_string):
    """Decode a base64 string to a URL."""
    try:
        return base64.urlsafe_b64decode(b64_string.encode()).decode()
    except Exception as e:
        return f"Error decoding URL: {e}"


def normalize_scores(distances):
    """Normalize distances to relevancy scores in the range [0, 1]."""
    if not distances:
        return []
    min_distance = min(distances)
    max_distance = max(distances)
    if max_distance == min_distance:
        # Assign uniform score of 1.0 if all distances are identical
        return [1.0] * len(distances)
    return [1 - (d - min_distance) / (max_distance - min_distance) for d in distances]


def query_cerebro_vds():
    print("### Running Query Test for Chroma DB Collection ###")

    # Initialize embedding function using the local model
    embedding_function = SentenceTransformerEmbeddingFunction(model_name=LOCAL_MODEL_PATH)

    # Initialize Chroma DB client
    client = chromadb.Client(Settings(persist_directory=CHROMA_DB_DIR, chroma_db_impl="duckdb+parquet"))

    # Load collection
    collection = client.get_collection(COLLECTION_NAME, embedding_function=embedding_function)
    print(f"✅ Collection '{COLLECTION_NAME}' found")

    # Define the query
    query_text = "how to design a button?"
    print(f"Search: {query_text}")

    try:
        # Execute the query
        results = collection.query(query_texts=[query_text], n_results=10)  # Retrieve top 10 results

        # Normalize scores
        normalized_scores = normalize_scores(results["distances"])

        print(f"✅ Query successful. Retrieved results:")

        # Print results field by field
        for idx, (context, score, metadata) in enumerate(
            zip(results["documents"][0], normalized_scores, results["metadatas"][0]), start=1
        ):
            print(f"\nResult {idx}:")
            print(f"  - Context: {context[:500]}{'...' if len(context) > 500 else ''}")
            print(f"  - Relevancy Score: {round(score, 4)}")
            print(f"  - Chunk ID: {metadata.get('chunk_id', 'N/A')}")
            print(f"  - Webpage: {metadata.get('source', 'N/A')}")
            # Decode the base64 URL
            webpage = metadata.get('source', 'N/A')
            if webpage.endswith(".pdf"):
                decoded_url = decode_base64_to_url(webpage[:-4])
                print(f"  - RAW Webpage: {decoded_url}")
            else:
                print(f"  - Decoded Webpage: {decode_base64_to_url(webpage)}")

    except Exception as e:
        print(f"❌ Query failed: {e}")

    print("\n### Query Test Completed ###")


if __name__ == "__main__":
    query_cerebro_vds()
