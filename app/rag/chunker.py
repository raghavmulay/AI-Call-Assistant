from pdf_loader import load_pdfs
from nltk.tokenize import sent_tokenize

def semantic_chunk(text, chunk_size=500):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def chunk_documents():
    docs = load_pdfs()
    all_chunks = []
    for doc in docs:
        for chunk in semantic_chunk(doc["text"]):
            all_chunks.append({"chunk": chunk, "source": doc["source"], "page": doc["page"]})
    return all_chunks




if __name__ == "__main__":
    chunks = chunk_documents()
    for c in chunks:
        print(c["chunk"][:100], "...", f"(Source: {c['source']}, Page: {c['page']})")