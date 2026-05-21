import fitz
import pdfplumber
import os
import re

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")


def clean_text(text):
    # Remove non-ASCII but keep common punctuation intact
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    # Remove box-drawing / decoration characters
    text = re.sub(r"[`~^|<>]+", " ", text)
    # Collapse 3+ repeated dashes/underscores/equals (decorative lines only)
    text = re.sub(r"[-_=]{3,}", " ", text)
    # Collapse whitespace (but preserve single newlines for chunker)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_tables(page):
    tables = page.extract_tables()
    rows = []
    for table in tables:
        for row in table:
            cleaned = [str(cell).strip() if cell else "" for cell in row]
            row_text = " | ".join(cleaned)
            if row_text.strip(" |"):   # skip blank rows
                rows.append(row_text)
    return "\n".join(rows)


def load_pdfs():
    documents = []

    for file in os.listdir(DATA_FOLDER):
        if not file.endswith(".pdf"):
            continue

        path = os.path.join(DATA_FOLDER, file)
        pdf_fitz = fitz.open(path)

        with pdfplumber.open(path) as pdf_plumber:
            for page_num in range(len(pdf_fitz)):
                text = pdf_fitz[page_num].get_text()
                table_text = extract_tables(pdf_plumber.pages[page_num])

                # Keep table text on its own lines so the chunker
                # doesn't merge it into surrounding prose
                if table_text:
                    full_text = text + "\n\n[TABLE]\n" + table_text + "\n[/TABLE]"
                else:
                    full_text = text

                full_text = clean_text(full_text)

                if len(full_text.strip()) < 50:
                    continue

                documents.append({
                    "text": full_text,
                    "source": file,
                    "page": page_num + 1,
                })

    return documents


if __name__ == "__main__":
    docs = load_pdfs()
    for doc in docs:
        print(doc["text"][:300])
        print(f"\n(Source: {doc['source']}, Page: {doc['page']})")
        print("\n" + "-" * 80 + "\n")
