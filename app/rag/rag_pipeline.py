from pdf_loader import load_pdfs
from chunker import chunk_documents
from embeddings import generate_embeddings
from vector_store import store_embeddings
from retriever import retrieve

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
    print("Embeddings stored successfully!")

    query = input("Enter Query: ")
    results = retrieve(query)
    print("\nRESULTS:\n")

    for doc in results["documents"][0]:
        print(doc)
        print("\n" + "-" * 50 + "\n")
        
        
if __name__ == "__main__":
    run_rag_pipeline()