# query_readable.py
# tester for the semantic query to verify retrieval quality

import chromadb
from sentence_transformers import SentenceTransformer
from config import DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL

client = chromadb.PersistentClient(path=DB_DIR)
col =client.get_collection(CHROMA_COLLECTION_NAME)

model= SentenceTransformer(EMBEDDING_MODEL, device="cpu")

def pretty_print_results(results):
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0] if "documents" in results else []
    metas = results.get("metadatas", [[]])[0] if "metadatas" in results else []
    dists = results.get("distances", [[]])[0] if "distances" in results else []
    for i in range(len(ids)):
        print(f"\nResult {i+1}")
        print("  id:     ", ids[i])
        print("  dist:   ", dists[i] if dists else None)
        meta = metas[i] if i < len(metas) else {}
        print("  source: ", meta.get("source") if isinstance(meta, dict) else meta)
        print("  path:   ", meta.get("path") if isinstance(meta, dict) else meta)
        snippet = docs[i] if i < len(docs) else "<no doc>"
        print("  snippet:", (snippet[:300] + "...") if isinstance(snippet, str) and len(snippet) > 300 else snippet)

def query_text(q, n_results=5):
    vec = model.encode([q])[0]
    if hasattr(vec, "tolist"):
        vec = vec.tolist()
    results = col.query(query_embeddings=[vec], n_results=n_results, include=["documents", "metadatas", "distances"])
    print("\n=== QUERY ===")
    print(q)
    pretty_print_results(results)

    if __name__ == "__main__":
        # replace or add your own test queries here
        queries = [
            "How do I reset the device to factory settings?",
            "What are the safety instructions for installation?",
        ]
        for q in queries:
            query_text(q, n_results=5)