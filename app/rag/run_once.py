"""
Run this once to (re)build the ChromaDB index from scratch.
Safe to re-run — vector_store.py drops and recreates the collection.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chunker import chunk_documents
from embeddings import generate_embeddings
from vector_store import store_embeddings

if __name__ == "__main__":
    print("Chunking documents...")
    chunks = chunk_documents()
    print(f"Created {len(chunks)} chunks")

    print("Generating embeddings...")
    chunks, embeddings = generate_embeddings()
    print("Embeddings generated")

    print("Storing in ChromaDB...")
    store_embeddings(chunks, embeddings)
    print("Done — index rebuilt cleanly.")
