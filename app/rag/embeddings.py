from sentence_transformers import SentenceTransformer
from chunker import chunk_documents


model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embeddings():

    chunks = chunk_documents()
    texts = [c["chunk"] for c in chunks]
    embeddings = model.encode(texts)

    return chunks, embeddings


if __name__ == "__main__":

    chunks, embeddings = generate_embeddings()

    print("Total Chunks:", len(chunks))
    print("Embedding Shape:", embeddings.shape)
    print("\nFirst Chunk:\n")
    print(chunks[0]["chunk"])
    print("\nFirst Embedding:\n")
    print(embeddings[0][:10])