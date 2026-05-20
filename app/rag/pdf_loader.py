import fitz
import os

DATA_FOLDER = "app/rag/data"


def load_pdfs():

    documents = []

    for file in os.listdir(DATA_FOLDER):

        if file.endswith(".pdf"):

            path = os.path.join(DATA_FOLDER, file)

            pdf = fitz.open(path)

            for page_num in range(len(pdf)):

                page = pdf[page_num]

                text = page.get_text()

                documents.append({
                    "text": text,
                    "source": file,
                    "page": page_num + 1
                })

    return documents
load_pdfs()