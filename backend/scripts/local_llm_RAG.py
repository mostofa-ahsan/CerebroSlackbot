import os
from dotenv import load_dotenv
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load environment variables
load_dotenv()
mistral_model_path = os.getenv("MISTRAL_MODEL_PATH")
falcon_model_path = os.getenv("FALCON_MODEL_PATH")

# Load ChromaDB collection
def load_chromadb_collection():
    from chromadb import Client

    client = Client(Settings(
        persist_directory="./cerebro_vds",
        chroma_db_impl="duckdb+parquet"
    ))
    return client.get_or_create_collection(
        name="Cerebro_VDS",
        embedding_function=SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    )

# Load LLM model
def load_model(model_path):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", torch_dtype="float16")
    return model, tokenizer

# Generate a response from the model
def generate_response(model, tokenizer, prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(inputs["input_ids"], max_length=200, num_return_sequences=1)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Main function
def main():
    # Load models
    print("Loading Mistral 7B model...")
    mistral_model, mistral_tokenizer = load_model(mistral_model_path)

    print("Loading Falcon 7B model...")
    falcon_model, falcon_tokenizer = load_model(falcon_model_path)

    # Load ChromaDB collection
    print("Loading ChromaDB collection...")
    collection = load_chromadb_collection()

    # Query ChromaDB
    print("Querying ChromaDB...")
    query_results = collection.query(
        query_texts=["What is the purpose of this project?"],
        n_results=3
    )
    context = "\n".join([result["document"] for result in query_results["results"]])

    # Generate responses using the models
    prompt = f"The following context is retrieved from ChromaDB:\n{context}\n\nPlease respond to this query."

    print("\nGenerating response from Mistral 7B:")
    mistral_response = generate_response(mistral_model, mistral_tokenizer, prompt)
    print(mistral_response)

    print("\nGenerating response from Falcon 7B:")
    falcon_response = generate_response(falcon_model, falcon_tokenizer, prompt)
    print(falcon_response)

if __name__ == "__main__":
    main()
