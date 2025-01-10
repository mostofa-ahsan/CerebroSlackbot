import os
import json
import chromadb
from chromadb.config import Settings

# Configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "pages"
EMBEDDINGS_DIR = "../data/embeddings"

def validate_embedding(embedding):
    """
    Validate embedding to ensure it's a list of numbers.
    """
    if not isinstance(embedding, list):
        return False
    if not all(isinstance(value, (int, float)) for value in embedding):
        return False
    return True

def ingest_embeddings_to_chroma_db():
    print("### Starting Embedding Ingestion to Chroma DB ###")

    # Connect to Chroma DB
    client = chromadb.Client(
        Settings(
            persist_directory=CHROMA_DB_DIR,
            chroma_db_impl="duckdb+parquet"
        )
    )

    # Create or retrieve the collection
    try:
        collection = client.get_collection(COLLECTION_NAME)
        print(f"✅ Collection '{COLLECTION_NAME}' found")
    except Exception:
        collection = client.create_collection(COLLECTION_NAME)
        print(f"✅ Created new collection: '{COLLECTION_NAME}'")

    # Iterate through embedding files
    for embedding_file in os.listdir(EMBEDDINGS_DIR):
        if not embedding_file.endswith("_embeddings.json"):
            continue
        
        embedding_path = os.path.join(EMBEDDINGS_DIR, embedding_file)
        print(f"Processing file: {embedding_file}")

        try:
            # Load the embedding file
            with open(embedding_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Prepare data for ingestion
            ids = []
            embeddings = []
            metadatas = []
            documents = []

            for record in data:
                chunk_id = record["chunk_id"]
                embedding = record.get("embedding", None)

                # Validate the embedding
                if embedding is None or not validate_embedding(embedding):
                    print(f"⚠️ Invalid or missing embedding for chunk_id: {chunk_id}. Skipping.")
                    continue

                ids.append(chunk_id)
                embeddings.append(embedding)
                metadatas.append({"chunk_id": chunk_id})
                documents.append(None)  # Adjust if you have document text

            # Debug: Print the first record being added
            if ids:
                print(f"Adding {len(ids)} records from file: {embedding_file}")
                print(f"Sample ID: {ids[0]}, Sample Embedding: {embeddings[0][:5]}...")
            else:
                print(f"⚠️ No valid records to add from file: {embedding_file}. Skipping.")
                continue

            # Add to the Chroma collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            print(f"✅ Successfully added data from {embedding_file}")

        except Exception as e:
            print(f"❌ Error processing file {embedding_file}: {e}")

    print("### Embedding Ingestion Completed ###")


if __name__ == "__main__":
    ingest_embeddings_to_chroma_db()
