import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from rich import print
import base64

# Configuration
CHROMA_DB_DIR = "../../data/cerebro_chroma_db_v1"
COLLECTION_NAME = "cerebro_vds_v1"
LOCAL_MODEL_PATH = "../../models/all-mpnet-base-v2"  # Path to the locally downloaded model

def decode_base64_to_url(b64_string):
    """Decode a base64 string to a URL."""
    try:
        return base64.urlsafe_b64decode(b64_string.encode()).decode()
    except Exception as e:
        return f"Error decoding URL: {e}"

def normalize_scores(distances):
    """Normalize distances to relevancy scores in the range [0, 1]."""
    if not distances or isinstance(distances, float):  # Ensure distances is a list
        distances = [distances]
    min_distance = min(distances)
    max_distance = max(distances)
    if max_distance == min_distance:
        return [1.0] * len(distances)  # Avoid division by zero
    return [1 - (d - min_distance) / (max_distance - min_distance) for d in distances]

def query_cerebro_v3():
    print("### Running Query Test for Chroma DB Collection ###")

    # Initialize embedding function using the local model
    embedding_function = SentenceTransformerEmbeddingFunction(model_name=LOCAL_MODEL_PATH)

    # Initialize Chroma DB client
    client = chromadb.Client(Settings(persist_directory=CHROMA_DB_DIR, chroma_db_impl="duckdb+parquet"))

    # List collections
    clist = client.list_collections()
    print(f'[cyan]Collections found: [blue]{clist}')

    # Load collection with the specified embedding function
    collection = client.get_collection(COLLECTION_NAME, embedding_function=embedding_function)
    print(f"✅ Collection '{COLLECTION_NAME}' found")

    # Define the query
    query_text = "how to design a button?"
    print("############################################")
    print("Search : ", query_text)
    print("############################################")

    try:
        # Execute the query
        results = collection.query(query_texts=[query_text], n_results=10)  # Retrieve top 10 results

        # Ensure results["distances"] is a list
        if not isinstance(results["distances"], list):
            results["distances"] = [results["distances"]]

        # Normalize the scores
        relevancy_scores = normalize_scores(results["distances"])

        print(f"✅ Query successful. Retrieved results:")

        # Print results field by field
        for i, (contexts, score, metadata) in enumerate(
            zip(results["documents"], relevancy_scores, results["metadatas"]), start=1
        ):
            for context, meta in zip(contexts, metadata):
                print(f"\nResult {i}:")
                print(f"  - Context: {context[:500] + '...' if len(context) > 500 else context}")
                print(f"  - Relevancy Score: {round(score, 4)}")
                print(f"  - Chunk ID: {meta.get('chunk_id', 'N/A')}")
                print(f"  - Embedding ID: {meta.get('embedding_id', 'N/A')}")
                print(f"  - Webpage: {meta.get('source', 'N/A')}")

                # Decode the base64 URL excluding the ".pdf" part
                webpage = meta.get('source', 'N/A')
                if webpage.endswith(".pdf"):
                    decoded_url = decode_base64_to_url(webpage[:-4])
                    print(f"  - RAW Webpage: {decoded_url}")
                else:
                    print(f"  - Decoded Webpage: {decode_base64_to_url(webpage)}")
                print(f"  - Saved Webpage: {meta.get('saved_webpage', 'N/A')}")

    except Exception as e:
        print(f"❌ Query failed: {e}")

    print("\n### Query Test Completed ###")

if __name__ == "__main__":
    query_cerebro_v3()
