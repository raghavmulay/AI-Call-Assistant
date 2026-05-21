from pdf_loader import load_pdfs


def chunk_documents(chunk_size=1000, chunk_overlap=200):
    """
    Sliding-window character chunker.
    - chunk_size=1000 keeps full unit descriptions together.
    - chunk_overlap=200 ensures subject names at chunk boundaries
      appear in both adjacent chunks, so retrieval never misses them.
    - Splits on newlines first (preserves table rows), then falls back
      to spaces — never mid-word.
    """
    docs = load_pdfs()
    all_chunks = []

    for doc in docs:
        text = doc["text"]
        start = 0
        length = len(text)

        while start < length:
            end = min(start + chunk_size, length)

            # Prefer splitting at a newline boundary within the window
            if end < length:
                split = text.rfind("\n", start, end)
                if split == -1:
                    split = text.rfind(" ", start, end)
                if split != -1 and split > start:
                    end = split

            chunk = text[start:end].strip()
            if len(chunk) > 50:          # skip near-empty chunks
                all_chunks.append({
                    "chunk": chunk,
                    "source": doc["source"],
                    "page": doc["page"],
                })

            # Move forward by (chunk_size - overlap) so chunks overlap
            step = chunk_size - chunk_overlap
            start += step

    return all_chunks


if __name__ == "__main__":
    chunks = chunk_documents()
    print(f"Total chunks: {len(chunks)}")
    for c in chunks[:3]:
        print(c["chunk"][:120], "...")
        print(f"  (Source: {c['source']}, Page: {c['page']})\n")
