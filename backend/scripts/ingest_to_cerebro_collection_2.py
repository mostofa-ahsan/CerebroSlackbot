import chromadb
from chromadb.config import Settings
import os
import json

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "cerebro_collection_v2"
EMBEDDINGS_DIR = "../data/embeddings"
CHROMA_EMBEDDINGS_DIR = "../data/cerebro_chroma_db/chroma_embedding"

def ingest_to_cerebro_collection():
    print("### Starting Data Ingestion for Chroma DB Collection ###")

    # Initialize Chroma DB client
    client = chromadb.Client(
        Settings(
            persist_directory=CHROMA_DB_DIR,
            chroma_db_impl="duckdb+parquet"
        )
    )

    # Get or create the collection
    collection = client.get_or_create_collection(COLLECTION_NAME)
    print(f"✅ Collection '{COLLECTION_NAME}' initialized")

    # Iterate through embedding files
    for file_name in os.listdir(EMBEDDINGS_DIR):
        if file_name.endswith("_embeddings.json"):
            embedding_file_path = os.path.join(EMBEDDINGS_DIR, file_name)
            text_file_path = os.path.join("../data/chunked_text_files", file_name.replace("_embeddings.json", ".json"))

            try:
                # Load embedding file
                with open(embedding_file_path, "r") as f:
                    embedding_data = json.load(f)

                # Load text file for corresponding chunk
                with open(text_file_path, "r") as f:
                    text_data = {entry["chunk_id"]: entry["text"] for entry in json.load(f)}

                # Prepare data for ingestion
                ids = [entry["chunk_id"] for entry in embedding_data]
                embeddings = [entry["embedding"] for entry in embedding_data]
                metadatas = [{"chunk_id": entry["chunk_id"]} for entry in embedding_data]
                documents = [text_data[entry["chunk_id"]] for entry in embedding_data]

                # Add records to the collection
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents
                )

                # Save enriched embeddings to the new directory
                enriched_data = [
                    {
                        "chunk_id": entry["chunk_id"],
                        "embedding": entry["embedding"],
                        "text": text_data[entry["chunk_id"]]
                    }
                    for entry in embedding_data
                ]
                os.makedirs(CHROMA_EMBEDDINGS_DIR, exist_ok=True)
                enriched_file_path = os.path.join(CHROMA_EMBEDDINGS_DIR, file_name)
                with open(enriched_file_path, "w") as f:
                    json.dump(enriched_data, f, indent=4)

                print(f"✅ Successfully added data from {embedding_file_path}")
                print(f"✅ Enriched embeddings saved to {enriched_file_path}")

            except Exception as e:
                print(f"❌ Failed to add data from {embedding_file_path}: {e}")

    # Persist the collection
    client.persist()
    print(f"✅ Data persisted to directory: {CHROMA_DB_DIR}")
    print("### Data Ingestion Completed ###")


if __name__ == "__main__":
    ingest_to_cerebro_collection()
