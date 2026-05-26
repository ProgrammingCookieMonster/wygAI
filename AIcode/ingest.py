# ingest.py --> creates ChromaDB collection for the RAG bot
# basically every PDF file from SHV needed here is turned into searchable vectors
# the vectors are stored by the level of relevance to each other, so that information that belongs together will be stored in the same area
# that allows the RAG to retrieve relevant information chunks when returning to build the LLM answer

# should only be run for the first loadout and when the documentation used is changing or settings need adjustment

import os
import uuid
import traceback
from sentence_transformers import SentenceTransformer
import chromadb
# utility and helpers homemade
from config import DOCS_DIR, DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
from utils import extract_text_from_pdf, simple_chunk_text, normalize_filename

BATCH_SIZE = 256

def find_pdfs(root_dir):
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                yield os.path.join(root, f)

def safe_persist(client):
    if hasattr(client, "persist"):
        try: # version of chromadb sometimes do/dont have it and its needed for writing to the disk
            client.persist()
            print("Persisted client to disk")
        except Exception as e:
            print("client.persist() raised: ", e)
    else:
        print("client.persist() not available, probably its automatic")

def add_batch_to_collection(col, ids, docs, metadatas, embeddings):
    assert len(ids) == len(docs) == len(metadatas), "ids/docs/metadatas length mismatch"
    if embeddings is not None:
        assert len(embeddings) == len(docs), "embeddings/docs length mismatch"

    try:
        col.add(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeddings)
    except Exception:
        print("Failed to add batch to collection. Traceback: ")
        traceback.print_exc()


def main():
    # DB dir had initial problems, check:
    os.makedirs(DB_DIR, exist_ok=True)
    if not os.access(DB_DIR, os.W_OK):
        raise RuntimeError(f"DB_DIR not writable: {DB_DIR}")

    # create persistent client & collection
    client = chromadb.PersistentClient(path=DB_DIR)
    col = client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
    print("Using collection: ", CHROMA_COLLECTION_NAME)

    # load embedder on CPU only, no GPU present on the board
    embedder = SentenceTransformer(EMBEDDING_MODEL, device="cpu")

    # iterate and act through each PDF
    for pdf_path in find_pdfs(DOCS_DIR):
        # check if we actually index anything
        print("\Indexing: ", pdf_path)
        try:
            text = extract_text_from_pdf(pdf_path)
        except Exception:
            print("Failed to extract text from PDF: ", pdf_path)
            traceback.print_exc()
            continue

        chunks= simple_chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        if not chunks:
            print("No chunks extracted, skipping file at ", pdf_path)
            continue

        # ids/metadatas
        all_ids = [str(uuid.uuid4()) for _ in chunks]
        all_metas =[
            {"source": normalize_filename(pdf_path), "path": pdf_path, "chunk_index": i}
            for i in range(len(chunks))
        ]

        # process in batches -- limit memory usage
        total = len(chunks)
        print(f" {total} chunks found. Processing in batches of {BATCH_SIZE}")

        start = 0
        while start < total:
            end = min(start + BATCH_SIZE, total)
            batch_docs = chunks[start:end]
            batch_ids = all_ids[start:end]
            batch_meta = all_metas[start:end]

            # encode the batch
            try:
                batch_embeddings = embedder.enconde(batch_docs, show_progress_bar=True)
                if hasattr(batch_embeddings, "tolist"):
                    batch_embeddings = batch_embeddings.tolist()
            except Exception:
                print(f"Embedding failed for batch {start}:{end} of {pdf_path}")
                traceback.print_exc()
                # skips batch, goes next
                start = end
                continue

            if batch_embeddings is not None and len(batch_embeddings) != len(batch_docs):
                print(f"Embedding length mismatch for batch {start}:{end}. Skipping it.")
                start = end
                continue

            # add to collection
            print(f"Adding chunks {start}:{end} to collection ...")
            add_batch_to_collection(col, client, batch_ids, batch_docs, batch_meta, batch_embeddings)

            start = end

        # persist after each file to be sure??
        safe_persist(client)
        print(f"Finished indexing file: {pdf_path}")

    print("\nIndexing completed.")


if __name__ == "__main__":
    main()