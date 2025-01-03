import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def create_index(chunks):
    embeddings = model.encode(chunks)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    return index

if __name__ == "__main__":
    sample_chunks = ["Chunk 1", "Chunk 2"]
    index = create_index(sample_chunks)
    faiss.write_index(index, "../data/faiss_index/index.faiss")
