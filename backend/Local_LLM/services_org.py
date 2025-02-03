import getpass
import logging
import base64

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
# from langchain.vectorstores import Chroma
# from langchain.embeddings import HuggingFaceEmbeddings
# from langchain.document_loaders import WebBaseLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_core.prompts import ChatPromptTemplate
from rich import print
from transformers import pipeline

if __name__ == '__main__':
    from local_llm import call_llm
    from prompts import SYSTEM_PROMPT
else:
    from .local_llm import call_llm
    from config.prompts import SYSTEM_PROMPT


# Logging

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)


# Constants

whoami = getpass.getuser()

SENTENCE_MODEL_PATH = f'/Users/{whoami}/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/fa97f6e7cb1a59073dff9e6b13e2715cf7475ac9'
CACHE_FOLDER = f'/Users/{whoami}/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/fa97f6e7cb1a59073dff9e6b13e2715cf7475ac9'
BASE_URL = "https://brandcentral.verizonwireless.com/guidelines/"  # "https://www.verizon.com/"

#SYSTEM_PROMPT = "You are a helpful, friendly, empathetic and conversational chatbot assistant called Verizon Brand Central Chatbot trained to answer questions about https://brandcentral.verizonwireless.com/guidelines/. "

HUMAN_PROMPT = "Use the following context to answer the question: {context}.\n\nQuestion: {question}"
BASE_URL = "https://designsystem.verizon.com/"

MAX_CONTEXT_LEN = 750
MAX_LLM_CONTEXT = 1500
MAX_SHOW = 55
PDF = '.pdf'


# From /data_ingestion
# -----------------------------------------------------------------------------
# NOTE: this is not the way to do this.. won't work from different directory levels
# The paths here are correct for when this is run from 1-higher level, like called by 'slack_bot.py'

# ChromaDB 0.3.29 --> 0.6.3 (soon)

CHROMA_DB_VER = "cerebro_chroma_db_old"    # "cerebro_chroma_db"
COLLECTION_NAME = "cerebro_vds_2"         # "cerebro_vds"

if __name__ == "__main__":
    CHROMA_DB_PATH = f"../../data_ingestion/data/{CHROMA_DB_VER}"
    EMBED_MODEL_PATH = "../../data_ingestion/models/all-mpnet-base-v2"
else:
    CHROMA_DB_PATH = f"./data_ingestion/data/{CHROMA_DB_VER}"
    EMBED_MODEL_PATH = "./data_ingestion/models/all-mpnet-base-v2"
# -----------------------------------------------------------------------------


# Global initalizations
# -----------------------------------------------------------------------------

# Initialize embedding function using the local model
embedding_function  = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL_PATH)

# Initialize Chroma DB client
client = chromadb.Client(Settings(persist_directory=CHROMA_DB_PATH,
                                  chroma_db_impl="duckdb+parquet"))

# LIST COLLECTIONS
clist = client.list_collections()
print(f'[cyan]Collections found: [blue]{clist}')

# Load collection with the specified embedding function
collection = client.get_collection(
    COLLECTION_NAME,
    embedding_function=embedding_function
)
print(f"✅ Collection '{COLLECTION_NAME}' found")


# Functions
# -----------------------------------------------------------------------------

def decode_base64_to_url(b64_string):
    """Decode a base64 string to a URL."""
    try:
        if b64_string[-4:] == PDF:
            b64_string = b64_string[:-4]
            return base64.urlsafe_b64decode(b64_string.encode()).decode() # + PDF
        return base64.urlsafe_b64decode(b64_string.encode()).decode()
    except:
        return "Unknown source"

def retrieve_docs(query_text: str, collection, k=3):
    # Execute the query
    results = collection.query(
        query_texts=[query_text],
        n_results=k,  # Retrieve top 10 results
    )
    print(f"✅ Query successful. Retrieved results:")

    # Print results field by field
    rag_data = []
    db_data = list(zip(results["documents"], results["distances"], results["metadatas"]))
    for i, (contexts, scores, metadatas) in enumerate(db_data, start=1):
        for context, score, metadata in zip(contexts, scores, metadatas):
            rag_context = context[:MAX_CONTEXT_LEN] + '...' if len(context) > MAX_CONTEXT_LEN else context
            b64_webpage = metadata.get('source', 'N/A')
            print(f'[magenta]b64_webpage: {b64_webpage}')
            webpage = decode_base64_to_url(b64_webpage)
            print(f"\nResult {i}:")
            print(f"  - Context: {rag_context}")
            print(f"  - Relevancy Score: {score}")
            print(f"  - Chunk ID: {metadata.get('chunk_id', 'N/A')}")
            print(f"  - Embedding ID: {metadata.get('embedding_id', 'N/A')}")
            print(f"  - Webpage: {webpage}")
            print(f"  - Saved Webpage: {metadata.get('saved_webpage', 'N/A')}")
            rag_data += [[rag_context, score, webpage]]
    print('rag_data')
    print(rag_data)
    print('-----------dbdone-----')
    return rag_data


def answer_rag_question(question, collection, llm_fn):
    """
    Retrieve context from the vectorstore and answer the question using Gemini 1.5 with a custom prompt template.
    """
    retrieved_docs = retrieve_docs(question, collection, k=3)  # Get top 3 relevant docs

    print(); print()
    print(retrieved_docs)
    print(); print()

    print(rag_data := retrieved_docs[0][0])
    print(); print()

    # A 'doc' is (context, score, metadata)
    context = " ".join([context for context, *_ in rag_data])  # Combine all retrieved docs

    if len(context.strip()) == 0:
        return "No relevant information found."

    # Define the prompt template for answering questions about Verizon
    # prompt = ChatPromptTemplate.from_messages(
    #     [("system", SYSTEM_PROMPT),
    #      ("human", ),])
    instruction = HUMAN_PROMPT.format(context=context[:MAX_LLM_CONTEXT], question=question)
    prompt = f"SYSTEM: {SYSTEM_PROMPT}.\n\n{instruction}"

    # Combine context and question in the prompt
    input_data = {"context": context, "question": question}

    # Generate response
    llm_response = llm_fn(prompt)
    print(f'response = [yellow]{llm_response}')

    # Ask LLM which docs were useful and give back list of numbers, few-shot it
    if retrieved_docs:
        rag_info = 'Website references:'
        for idx, doc in enumerate(retrieved_docs):
            context, score, webpage = doc
            rag_info += f'\n\n{idx + 1}. "{context[:MAX_SHOW]} ..." ({score:0.2f})\n{webpage}'
    else:
        rag_info = "  No documents found.  See: "
    rag_info += f"\n\nVDS Design Guide: {BASE_URL}"

    response = f'{llm_response}\n\n{rag_info}'
    print(f'[bold]Full response = [yellow]{llm_response}')
    return response


# AI interface
def call_ai_service(user_input):
    # try:
    #     response = answer_rag_question(user_input, collection, call_llm)
    #     print(f"**Answer:** [yellow]{response}")
    # except Exception as e:
    #     msg = f"Error in call_ai_service(): {e}"
    #     print(f"[red]{msg}")
    #     logger.error(msg)
    #     return msg
    response = answer_rag_question(user_input, collection, call_llm)
    print(f"**Answer:** [yellow]{response}")
    return response


def test_ai_service():
    TEST_QUESTION_1 = "What is general advice for subtitle usage at Verizon?"
    TEST_QUESTION_2 = "What are the elements a toggle contains?"
    print("Search : ", TEST_QUESTION_2)
    response = call_ai_service(TEST_QUESTION_2)
    print(f'Test question: [green]{TEST_QUESTION_2}')
    print(f'Test response: [blue]{response}')

if __name__ == "__main__":
    test_ai_service()
