import os
import json
from sentence_transformers import SentenceTransformer

def embed_chunks(chunked_dir, embedding_dir, model_name="all-MiniLM-L6-v2"):
    """
    Generate embeddings for chunked data.
    :param chunked_dir: Directory containing chunked text files.
    :param embedding_dir: Directory to save the embeddings.
    :param model_name: Hugging Face model to use for embeddings.
    """
    os.makedirs(embedding_dir, exist_ok=True)
    model = SentenceTransformer(model_name)
    print(f"Using embedding model: {model_name}")

    for chunk_file in os.listdir(chunked_dir):
        if not chunk_file.endswith(".json"):
            continue

        chunk_path = os.path.join(chunked_dir, chunk_file)
        embedding_path = os.path.join(embedding_dir, f"{os.path.splitext(chunk_file)[0]}_embeddings.json")

        try:
            # Load chunks
            with open(chunk_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            # Generate embeddings
            embeddings = model.encode([chunk["text"] for chunk in chunks], show_progress_bar=True)

            # Save embeddings
            embedding_data = [
                {"chunk_id": chunk["chunk_id"], "embedding": embedding.tolist()}
                for chunk, embedding in zip(chunks, embeddings)
            ]

            with open(embedding_path, "w", encoding="utf-8") as f:
                json.dump(embedding_data, f, indent=4)

            print(f"Embeddings saved to {embedding_path}")
        except Exception as e:
            print(f"Error processing {chunk_file}: {e}")

if __name__ == "__main__":
    chunked_dir = "../data/chunked_text_files"
    embedding_dir = "../data/embeddings"
    embed_chunks(chunked_dir, embedding_dir)
