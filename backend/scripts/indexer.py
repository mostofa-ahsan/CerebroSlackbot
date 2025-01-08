import os
import json
import faiss
import numpy as np

def create_index(embedding_dir, index_dir, index_file="vector_index.faiss"):
    """
    Create an index from embeddings.
    :param embedding_dir: Directory containing embeddings.
    :param index_dir: Directory to save the index.
    :param index_file: Name of the FAISS index file.
    """
    os.makedirs(index_dir, exist_ok=True)
    index = None
    id_mapping = {}

    for embedding_file in os.listdir(embedding_dir):
        if not embedding_file.endswith("_embeddings.json"):
            continue

        embedding_path = os.path.join(embedding_dir, embedding_file)

        try:
            # Load embeddings
            with open(embedding_path, "r", encoding="utf-8") as f:
                embedding_data = json.load(f)

            vectors = [np.array(record["embedding"], dtype=np.float32) for record in embedding_data]
            chunk_ids = [record["chunk_id"] for record in embedding_data]

            # Initialize index if not already done
            if index is None:
                index = faiss.IndexFlatL2(len(vectors[0]))

            # Add vectors to index
            index.add(np.stack(vectors))

            # Add chunk IDs to mapping
            id_mapping.update({i: chunk_id for i, chunk_id in enumerate(chunk_ids, start=index.ntotal - len(vectors))})

        except Exception as e:
            print(f"Error processing {embedding_file}: {e}")

    # Save index
    index_path = os.path.join(index_dir, index_file)
    faiss.write_index(index, index_path)

    # Save ID mapping
    id_mapping_path = os.path.join(index_dir, "id_mapping.json")
    with open(id_mapping_path, "w", encoding="utf-8") as f:
        json.dump(id_mapping, f, indent=4)

    print(f"Index saved to {index_path}")
    print(f"ID mapping saved to {id_mapping_path}")

if __name__ == "__main__":
    embedding_dir = "../data/embeddings"
    index_dir = "../data/indexes"
    create_index(embedding_dir, index_dir)
