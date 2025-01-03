def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

def chunk_all(parsed_dir, chunked_dir, chunk_size=1000, overlap=200):
    os.makedirs(chunked_dir, exist_ok=True)
    for file in os.listdir(parsed_dir):
        if file.endswith(".txt"):
            file_path = os.path.join(parsed_dir, file)
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            chunks = chunk_text(text, chunk_size, overlap)
            with open(os.path.join(chunked_dir, file), "w", encoding="utf-8") as f:
                f.write("

".join(chunks))
    print(f"Chunking completed. Files saved in {chunked_dir}.")
