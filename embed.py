import fitz  # pymupdf
import chromadb
import re
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

def split_chunks(text, chunk_size=500, overlap=100):
    # Split into sentences using punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current = ""

    for sentence in sentences:
        # If adding this sentence keeps us under chunk_size → append
        if len(current) + len(sentence) < chunk_size:
            current += " " + sentence
        else:
            # Save the current chunk
            chunks.append(current.strip())
            # Start a new chunk with this sentence
            current = sentence

    # Add the last chunk
    if current.strip():
        chunks.append(current.strip())

    # Add overlap: each chunk includes the previous one
    final_chunks = []
    for i in range(len(chunks)):
        start = max(0, i - 1)
        combined = " ".join(chunks[start:i+1])
        final_chunks.append(combined)

    return final_chunks

def build_database():
    embedder = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=DB_PATH)

    # fresh start — delete old on rebuilds
    try:
        client.delete_collection("union_docs")
    except:
        pass

    collection = client.create_collection("union_docs", metadata={"hnsw:space": "cosine"}) # the distance in cosine space becomes way more interpretable for threshold

    pdf_files = list(Path(DOCUMENTS_PATH).rglob("*.pdf"))
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
                metadatas=[{"source": str(pdf_path.relative_to(DOCUMENTS_PATH))}]
            )
            chunk_id += 1

    print(f"\nDatabase built. Total chunks: {chunk_id}")

if __name__ == "__main__":
    build_database()