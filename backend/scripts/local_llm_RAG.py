import os
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Load environment variables
load_dotenv()
mistral_model_path = os.getenv("MISTRAL_MODEL_PATH")
falcon_model_path = os.getenv("FALCON_MODEL_PATH")

# ChromaDB configuration
CHROMA_DB_DIR = "../data/cerebro_chroma_db"
COLLECTION_NAME = "cerebro_v3"
LOCAL_MODEL_PATH = "../models/all-mpnet-base-v2"  # Path to the locally downloaded embedding model

# Function to query ChromaDB
def query_cerebro_v3(query_text, n_results=10):
    print("### Running Query Test for Chroma DB Collection ###")

    # Set up embedding function using the local model
    embedding_function = SentenceTransformerEmbeddingFunction(model_name=LOCAL_MODEL_PATH)

    # Initialize ChromaDB client
    client = chromadb.Client(Settings(persist_directory=CHROMA_DB_DIR, chroma_db_impl="duckdb+parquet"))
    
    # Load collection with the specified embedding function
    collection = client.get_collection(
        COLLECTION_NAME,
        embedding_function=embedding_function
    )
    print(f"✅ Collection '{COLLECTION_NAME}' found")

    try:
        # Execute the query
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
        )
        print(f"✅ Query successful. Retrieved results:")

        # Collect and return context
        contexts = []
        for i, (contexts_list, scores, metadatas) in enumerate(
            zip(results["documents"], results["distances"], results["metadatas"]), start=1
        ):
            for context, score, metadata in zip(contexts_list, scores, metadatas):
                contexts.append(context)
        return "\n".join(contexts)

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return ""

# Function to load a local LLM model
def load_model(model_path):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", torch_dtype="float16")
    return model, tokenizer

# Function to generate a response using the model
def generate_response(model, tokenizer, prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(inputs["input_ids"], max_length=200, num_return_sequences=1)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Main function
def main():
    # Query text
    query_text = "What is Verizon BrandCentral used for?"

    # Query ChromaDB for context
    print("Querying ChromaDB...")
    context = query_cerebro_v3(query_text, n_results=10)

    if not context:
        print("❌ No context retrieved. Exiting...")
        return

    print("\nRetrieved Context:")
    print(context[:1000] + "..." if len(context) > 1000 else context)

    # Create the prompt
    prompt = f"The following context is retrieved from ChromaDB:\n{context}\n\nQuery: {query_text}\n\nResponse:"

    # Load and generate response with Mistral 7B
    print("\nLoading Mistral 7B model...")
    mistral_model, mistral_tokenizer = load_model(mistral_model_path)
    print("\nGenerating response from Mistral 7B:")
    mistral_response = generate_response(mistral_model, mistral_tokenizer, prompt)
    print(mistral_response)

    # Load and generate response with Falcon 7B
    print("\nLoading Falcon 7B model...")
    falcon_model, falcon_tokenizer = load_model(falcon_model_path)
    print("\nGenerating response from Falcon 7B:")
    falcon_response = generate_response(falcon_model, falcon_tokenizer, prompt)
    print(falcon_response)

if __name__ == "__main__":
    main()
