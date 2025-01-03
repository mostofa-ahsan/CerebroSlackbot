from transformers import pipeline

tagger = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")

def tag_chunks(chunks):
    tagged_data = []
    for chunk in chunks:
        tagged_data.append(tagger(chunk))
    return tagged_data

if __name__ == "__main__":
    sample_chunks = ["Your text chunk 1", "Your text chunk 2"]
    tags = tag_chunks(sample_chunks)
    print(tags)
