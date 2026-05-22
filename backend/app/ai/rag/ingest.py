import os
import sys
from backend.app.ai.rag.pdf_loader import load_pdfs
from backend.app.ai.rag.chunker import chunk_documents
from backend.app.ai.rag.embeddings import generate_embeddings
from backend.app.ai.rag.vector_store import store_embeddings

def run_ingestion():
    print("?? Starting RAG Ingestion Pipeline...")
    
    print("1. Loading PDFs...")
    docs = load_pdfs()
    print(f"   Loaded {len(docs)} documents.")

    print("2. Chunking documents...")
    chunks = chunk_documents()
    print(f"   Created {len(chunks)} chunks.")

    print("3. Generating embeddings...")
    chunks, embeddings = generate_embeddings()
    print("   Embeddings generated.")

    print("4. Storing embeddings in ChromaDB...")
    store_embeddings(chunks, embeddings)
    print("? Ingestion Complete!")

if __name__ == '__main__':
    run_ingestion()
