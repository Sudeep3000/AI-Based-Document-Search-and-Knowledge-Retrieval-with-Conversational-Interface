import os
import pickle
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

DOCUMENTS_DIR = "data/documents"
VECTOR_STORE_DIR = "vector_store"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def load_documents(directory):
    documents = []

    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)

        if filename.endswith(".txt"):
            with open(path, "r", encoding="utf-8") as file:
                text = file.read()
                documents.append((filename, text))

        elif filename.endswith(".pdf"):
            reader = PdfReader(path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            documents.append((filename, text))

    return documents


def split_text(text, chunk_size, overlap):
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

        if start < 0:
            start = 0

    return chunks


def split_documents(documents):
    all_chunks = []
    metadata = []

    for doc_name, text in documents:
        chunks = split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        for chunk in chunks:
            all_chunks.append(chunk)
            metadata.append({"source": doc_name})

    return all_chunks, metadata


def generate_embeddings(chunks):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(chunks)
    return embeddings


def store_embeddings(embeddings, chunks, metadata):
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, os.path.join(VECTOR_STORE_DIR, "faiss.index"))

    with open(os.path.join(VECTOR_STORE_DIR, "data.pkl"), "wb") as file:
        pickle.dump(
            {"chunks": chunks, "metadata": metadata},
            file
        )


def main():
    documents = load_documents(DOCUMENTS_DIR)
    chunks, metadata = split_documents(documents)
    embeddings = generate_embeddings(chunks)
    store_embeddings(embeddings, chunks, metadata)

    print("Documents loaded:", len(documents))
    print("Chunks created:", len(chunks))
    print("Embeddings stored successfully")


if __name__ == "__main__":
    main()
