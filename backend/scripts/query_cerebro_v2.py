import os
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from rich import print
import base64

# Configuration
CHROMA_DB_DIR = "../../data/cerebro_chroma_db_test_2"
COLLECTION_NAME = "cerebro_vds_test_2"
SENTENCE_MODEL_PATH = "../../models/all-mpnet-base-v2"
CACHE_FOLDER = "../../cache"


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


def query_chroma_vds():
    print("### Running Query Test for Chroma DB Collection ###")

    # Initialize embedding model
    embedding_model = HuggingFaceEmbeddings(
        model_name=SENTENCE_MODEL_PATH,
        cache_folder=CACHE_FOLDER
    )

    # Load Chroma vector store
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embedding_model,
    )
    print(f"✅ Collection '{COLLECTION_NAME}' loaded from '{CHROMA_DB_DIR}'")

    # Define the query
    query_text = "What are the components of a toggle?"
    print(f"Search Query: {query_text}")

    try:
        # Execute the query
        results = vectorstore.similarity_search_with_score(query_text, k=10)  # Retrieve top 10 results

        # Extract distances and normalize to scores
        distances = [result[1] for result in results]
        normalized_scores = normalize_scores(distances)

        # Display the results
        print(f"✅ Query successful. Retrieved results:")
        for idx, ((document, metadata), score) in enumerate(zip(results, normalized_scores), start=1):
            print(f"\nResult {idx}:")
            print(f"  - Context: {document[:500]}{'...' if len(document) > 500 else ''}")
            print(f"  - Relevancy Score: {round(score, 4)}")
            print(f"  - Metadata: {metadata}")
            # Decode the base64 URL if available
            if "source" in metadata:
                webpage = metadata.get("source", "N/A")
                if webpage.endswith(".pdf"):
                    decoded_url = decode_base64_to_url(webpage[:-4])
                    print(f"  - RAW Webpage: {decoded_url}")
                else:
                    print(f"  - Decoded Webpage: {decode_base64_to_url(webpage)}")

    except Exception as e:
        print(f"❌ Query failed: {e}")

    print("\n### Query Test Completed ###")


if __name__ == "__main__":
    query_chroma_vds()
