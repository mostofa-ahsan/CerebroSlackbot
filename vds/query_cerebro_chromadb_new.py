from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
# from langchain.config import Settings

# Configuration
CHROMA_DB_DIR = "../../data/cerebro_chroma_db"
COLLECTION_NAME = "verizon_docs"
SENTENCE_MODEL_PATH = "../../models/all-mpnet-base-v2"

def query_cerebro_v3():
    """
    Query the ChromaDB collection and print the results.
    """
    print("### Running Query Test for Chroma DB Collection ###")

    # Initialize embedding function
    embedding_function = HuggingFaceEmbeddings(model_name=SENTENCE_MODEL_PATH)

    # Initialize Chroma vector store
    # client = Chroma(
    #     persist_directory=CHROMA_DB_DIR,
    #     # COLLECTION_NAME=COLLECTION_NAME,
    #     embedding_function=embedding_function,
    #     # persist_directory=CHROMA_DB_DIR,
    # )
    # vectorstore = client.get_collection(COLLECTION_NAME)

    vectorstore = Chroma(collection_name=COLLECTION_NAME, persist_directory=CHROMA_DB_DIR, embedding_function=embedding_function)
    print(f"✅ Collection '{COLLECTION_NAME}' initialized")

    # Define the query
    query_text = "what are the components of a toggle?"

    try:
        # Execute the query
        results = vectorstore.similarity_search(query_text, k=10)  # Retrieve top 10 results
        print(f"✅ Query successful. Retrieved results:")

        # Print results field by field
        for i, doc in enumerate(results, start=1):
            print(f"\nResult {i}:")
            print(f"  - Context: {doc.page_content[:500] + '...' if len(doc.page_content) > 500 else doc.page_content}")
            print(f"  - Metadata: {doc.metadata}")

    except Exception as e:
        print(f"❌ Query failed: {e}")

    print("\n### Query Test Completed ###")

if __name__ == "__main__":
    query_cerebro_v3()