import os
import json

PARSED_DIR = "../data/parsed_text_plain"
CHUNKED_DIR = "../data/chunked_text_files"
CHUNK_SIZE = 300  # Number of words per chunk

# Ensure the output directory exists
os.makedirs(CHUNKED_DIR, exist_ok=True)

def chunk_text_file(file_path, chunk_size=CHUNK_SIZE):
    """
    Chunk the content of a plain text file into smaller parts.

    Args:
        file_path (str): Path to the plain text file.
        chunk_size (int): Number of words per chunk.

    Returns:
        list: A list of chunk dictionaries containing chunked text.
    """
    chunks = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        words = content.split()
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append({
                "chunk_id": f"{os.path.basename(file_path).replace('.txt', '')}_{i // chunk_size}",
                "text": chunk,
            })
        return chunks
    except Exception as e:
        print(f"Error chunking file {file_path}: {e}")
        return []

def chunk_parsed_data(parsed_dir, output_dir):
    """
    Chunk all plain text files in the parsed directory.

    Args:
        parsed_dir (str): Directory containing plain text files.
        output_dir (str): Directory to save chunked output files.
    """
    for parsed_file in os.listdir(parsed_dir):
        if parsed_file.endswith(".txt"):
            parsed_path = os.path.join(parsed_dir, parsed_file)
            print(f"Chunking {parsed_path}...")
            
            chunks = chunk_text_file(parsed_path)
            if chunks:
                output_file = os.path.join(output_dir, f"chunked_{os.path.splitext(parsed_file)[0]}.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(chunks, f, indent=4)
                print(f"Chunks saved to {output_file}")
            else:
                print(f"No chunks generated for {parsed_path}")

if __name__ == "__main__":
    chunk_parsed_data(PARSED_DIR, CHUNKED_DIR)
