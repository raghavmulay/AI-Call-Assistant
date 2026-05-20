import chromadb

from embeddings import generate_embeddings


client = chromadb.PersistentClient(
    path="chroma_db"
)


collection = client.get_or_create_collection(
    name="college_documents"
)


def store_embeddings(chunks, embeddings):

    ids = [f"id_{i}" for i in range(len(chunks))]

    documents = [c["chunk"] for c in chunks]

    metadatas = [

        {
            "source": c["source"],
            "page": c["page"]
        }

        for c in chunks
    ]

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