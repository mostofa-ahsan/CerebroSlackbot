import os
import json
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "cerebro_collection_1"
EMBEDDINGS_DIR = "../data/embeddings"
TEXT_FILES_DIR = "../data/chunked_text_files"
NEW_EMBEDDINGS_DIR = "../data/embeddings_new"

def ingest_to_cerebro_collection():
    print("### Starting Data Ingestion for Chroma DB Collection ###")

    # Ensure the new embeddings directory exists
    os.makedirs(NEW_EMBEDDINGS_DIR, exist_ok=True)

    # Set up the embedding function
    embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    # Initialize Chroma DB client
    client = chromadb.Client(
        Settings(
            persist_directory=CHROMA_DB_DIR,
            chroma_db_impl="duckdb+parquet"
        )
    )

    # Get or create collection with embedding function
    collection = client.get_or_create_collection(COLLECTION_NAME, embedding_function=embeddings)
    print(f"✅ Collection '{COLLECTION_NAME}' initialized")

    # Map text files to their respective embedding files
    text_files = {file_name.replace(".json", ""): os.path.join(TEXT_FILES_DIR, file_name)
                  for file_name in os.listdir(TEXT_FILES_DIR) if file_name.endswith(".json")}
    embedding_files = {file_name.replace("_embeddings.json", ""): os.path.join(EMBEDDINGS_DIR, file_name)
                       for file_name in os.listdir(EMBEDDINGS_DIR) if file_name.endswith("_embeddings.json")}

    for key, embedding_file_path in embedding_files.items():
        try:
            # Ensure the corresponding text file exists
            if key not in text_files:
                print(f"⚠️ No matching text file found for {embedding_file_path}. Skipping.")
                continue

            # Load embeddings data
            with open(embedding_file_path, "r") as embedding_file:
                embedding_data = json.load(embedding_file)

            # Load text data
            with open(text_files[key], "r") as text_file:
                text_data = json.load(text_file)
                text_map = {entry["chunk_id"]: entry["text"] for entry in text_data}

            # Add text field to embeddings
            enriched_data = []
            for entry in embedding_data:
                chunk_id = entry["chunk_id"]
                entry["text"] = text_map.get(chunk_id, "")  # Add text or use empty string if not found
                enriched_data.append(entry)

            # Add enriched data to the collection
            ids = [entry["chunk_id"] for entry in enriched_data]
            embeddings_data = [entry["embedding"] for entry in enriched_data]
            texts = [entry["text"] for entry in enriched_data]
            metadata = [{"chunk_id": entry["chunk_id"]} for entry in enriched_data]

            # Ensure `documents` are indexed
            collection.add(
                ids=ids,
                embeddings=embeddings_data,
                documents=texts,  # Add text field as documents
                metadatas=metadata
            )
            print(f"✅ Successfully added data from {embedding_file_path}")

            # Save enriched embeddings to the new folder
            new_file_path = os.path.join(NEW_EMBEDDINGS_DIR, os.path.basename(embedding_file_path))
            with open(new_file_path, "w") as new_file:
                json.dump(enriched_data, new_file, indent=4)
            print(f"✅ Enriched embeddings saved to {new_file_path}")

        except Exception as e:
            print(f"❌ Failed to process {embedding_file_path}: {e}")

    # Persist the database and clean up
    try:
        client.persist()
        print(f"✅ Data persisted to directory: {CHROMA_DB_DIR}")
        del client
        del collection
    except Exception as e:
        print(f"⚠️ Warning: Failed to persist the client: {e}")

    print("### Data Ingestion Completed ###")


if __name__ == "__main__":
    ingest_to_cerebro_collection()
