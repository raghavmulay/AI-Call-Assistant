import os
import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

_CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
client = chromadb.PersistentClient(path=_CHROMA_PATH)
collection = client.get_collection(name="college_documents")


def retrieve(query: str, top_k: int = 5):
    """
    Returns top_k chunks most similar to query.
    Includes distances for debug logging.
    """
    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # ── Debug logging ──────────────────────────────────────────────
    docs      = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    print(f"\n[Retriever] Query: {query!r}")
    print(f"[Retriever] Top-{top_k} results:")
    for i, (doc, dist, meta) in enumerate(zip(docs, distances, metadatas)):
        print(f"  [{i+1}] score={1-dist:.4f}  src={meta.get('source')} p={meta.get('page')}")
        print(f"       {doc[:120].replace(chr(10), ' ')} ...")
    # ───────────────────────────────────────────────────────────────

    return results


if __name__ == "__main__":
    query = input("Enter Query: ")
    results = retrieve(query)
    print("\nRESULTS:\n")
    for doc in results["documents"][0]:
        print(doc)
        print("\n" + "-" * 50 + "\n")
