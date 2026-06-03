import fitz  # pymupdf
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

DOCUMENTS_PATH = "./documents"
DB_PATH = "./db"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

def load_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def split_chunks(text, chunk_size=400, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def build_database():
    embedder = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=DB_PATH)

    # fresh start — delete old on rebuilds
    try:
        client.delete_collection("union_docs")
    except:
        pass

    collection = client.create_collection("union_docs")

    pdf_files = list(Path(DOCUMENTS_PATH).glob("*.pdf"))
    print(f"Found {len(pdf_files)} documents")

    chunk_id = 0
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")

        text = load_pdf(str(pdf_path))
        if not text.strip():
            print(f"  Warning: no text extracted from {pdf_path.name}")
            continue

        chunks = split_chunks(text)
        print(f"  {len(chunks)} chunks")

        for chunk in chunks:
            embedding = embedder.encode(chunk).tolist()
            collection.add(
                ids=[f"chunk_{chunk_id}"],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source": pdf_path.name}]
            )
            chunk_id += 1

    print(f"\nDatabase built. Total chunks: {chunk_id}")

if __name__ == "__main__":
    build_database()