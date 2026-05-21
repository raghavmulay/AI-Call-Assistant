import sys
import os

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_RAG_DIR = os.path.dirname(os.path.abspath(__file__))
if _RAG_DIR not in sys.path:
    sys.path.insert(0, _RAG_DIR)

from pdf_loader import load_pdfs
from chunker import chunk_documents
from embeddings import generate_embeddings
from vector_store import store_embeddings
from retriever import retrieve
from app.llm.ollama_llm import generate_rag_response

FALLBACK = "I could not find that in the syllabus."


def get_rag_answer(query: str) -> str:
    """
    Retrieves top-5 chunks from ChromaDB and passes them to the LLM.
    Never falls back to a plain (context-free) LLM call — that causes
    hallucinations. Returns FALLBACK string if retrieval is empty.
    """
    try:
        results = retrieve(query, top_k=2)
        docs = results.get("documents", [[]])[0]

        if not docs:
            print("[RAG] No chunks retrieved — returning fallback.")
            return FALLBACK

        context = "\n\n---\n\n".join(docs)

        # Debug: show exactly what context the LLM receives
        print(f"\n[RAG] Context sent to LLM ({len(context)} chars):\n{context[:600]} ...\n")

        return generate_rag_response(query, context)

    except Exception as e:
        print(f"[RAG Error]: {e}")
        return FALLBACK


def run_rag_pipeline():
    print("Loading PDFs...")
    docs = load_pdfs()
    print(f"Loaded {len(docs)} documents")

    print("Chunking documents...")
    chunks = chunk_documents()
    print(f"Created {len(chunks)} chunks")

    print("Generating embeddings...")
    chunks, embeddings = generate_embeddings()
    print("Embeddings generated")

    print("Storing embeddings...")
    store_embeddings(chunks, embeddings)
    print("Stored in ChromaDB")

    while True:
        query = input("\nEnter Query (or 'exit'): ")
        if query.lower() == "exit":
            break
        answer = get_rag_answer(query)
        print(f"\nAnswer: {answer}\n")


if __name__ == "__main__":
    run_rag_pipeline()
