import chromadb

from sentence_transformers import SentenceTransformer


model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


client = chromadb.PersistentClient(
    path="chroma_db"
)


collection = client.get_collection(
    name="college_documents"
)


def retrieve(query, top_k=3):

    query_embedding = model.encode(query).tolist()

    results = collection.query(

        query_embeddings=[query_embedding],

        n_results=top_k
    )

    return results


if __name__ == "__main__":

    query = input("Enter Query: ")

    results = retrieve(query)

    print("\nRESULTS:\n")

    for doc in results["documents"][0]:

        print(doc)

        print("\n" + "-" * 50 + "\n")