import fitz
import pdfplumber
import os
import re

DATA_FOLDER = "app/rag/data"


def clean_text(text):

    text = re.sub(r'[`~^|<>]+', ' ', text)

    text = re.sub(r'[-_,.=]{2,}', ' ', text)

    text = re.sub(r'\s+', ' ', text)

    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    return text.strip()


def extract_tables(page):

    tables = page.extract_tables()

    table_text = ""

    for table in tables:

        for row in table:

            cleaned_row = [

                str(cell).strip() if cell else ""

                for cell in row
            ]

            table_text += " | ".join(cleaned_row) + "\n"

    return table_text


def load_pdfs():

    documents = []

    for file in os.listdir(DATA_FOLDER):

        if file.endswith(".pdf"):

            path = os.path.join(DATA_FOLDER, file)

            # fitz for normal text
            pdf_fitz = fitz.open(path)

            # pdfplumber for tables
            with pdfplumber.open(path) as pdf_plumber:

                for page_num in range(len(pdf_fitz)):

                    # -------- FITZ TEXT EXTRACTION --------

                    page_fitz = pdf_fitz[page_num]

                    text = page_fitz.get_text()

                    # -------- PDFPLUMBER TABLE EXTRACTION --------

                    plumber_page = pdf_plumber.pages[page_num]

                    table_text = extract_tables(plumber_page)

                    # -------- MERGE BOTH --------

                    full_text = text + "\n" + table_text

                    # -------- CLEAN TEXT --------

                    full_text = clean_text(full_text)

                    # Skip empty pages
                    if len(full_text.strip()) < 50:
                        continue

                    documents.append({

                        "text": full_text,

                        "source": file,

                        "page": page_num + 1
                    })

    return documents


if __name__ == "__main__":

    docs = load_pdfs()

    for doc in docs:

        print(doc["text"])

        print(
            f"\n(Source: {doc['source']}, Page: {doc['page']})"
        )

        print("\n" + "-" * 80 + "\n")