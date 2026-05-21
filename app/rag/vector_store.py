import os
import chromadb
from embeddings import generate_embeddings

_CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
client = chromadb.PersistentClient(path=_CHROMA_PATH)


def store_embeddings(chunks, embeddings):
    # Always drop and recreate so re-indexing is clean with no duplicate IDs
    client.delete_collection(name="college_documents")
    collection = client.create_collection(name="college_documents")

    ids = [f"id_{i}" for i in range(len(chunks))]
    documents = [c["chunk"] for c in chunks]
    metadatas = [{"source": c["source"], "page": c["page"]} for c in chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=documents,
        metadatas=metadatas
    )
    print(f"\nStored {len(chunks)} chunks in ChromaDB")


if __name__ == "__main__":
    chunks, embeddings = generate_embeddings()
    store_embeddings(chunks, embeddings)