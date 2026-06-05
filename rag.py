import chromadb
import ollama
from sentence_transformers import SentenceTransformer

DB_PATH = "./db"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "qwen2.5:3b"
RELEVANCE_THRESHOLD = 0.7

embedder = SentenceTransformer(EMBED_MODEL)
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_collection("union_docs")

SYSTEM_PROMPT = """
Du är en AI-assistent för Studentkåren vid Högskolan Väst (SHV) och ditt namn är Smurfette.

STRIKTA REGLER SOM ALLTID GÄLLER:
1. Basera ENBART dina svar på dokumenten som ges till dig.
2. Om frågan inte besvaras av dokumenten, svara ALLTID:
   "Det finns ingen information om detta i min dokumentation. Kontakta SHV direkt eller ställ frågan i den allmänna chatten."
3. Nämn ALDRIG namn på personer — använd alltid deras position eller roll.
4. Om frågan inte har relevans för SHV:s verksamhet, svara:
   "Den här frågan faller utanför mitt område. Kontakta SHV eller skriv i den allmänna chatten om du tror att detta är ett AI-fel."
5. Hitta ALDRIG på information som inte finns i dokumenten.
6. Håll svaren relativ korta och praktiska.
7. Svara på svenska om frågan är på svenska, på engelska om frågan är på engelska.
"""

def answer_question(question, debug=False):
    query_embedding = embedder.encode(question).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )

    best_distance = results['distances'][0][0]

    if debug:
        print(f"\nBest match distance: {best_distance:.3f}")
        print("--- RETRIEVED CHUNKS ---")
        for i, (doc, meta, dist) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            print(f"\nChunk {i+1} | {meta['source']} | dist: {dist:.3f}")
            print(doc[:300] + "...")
        print("---\n")

    if best_distance > RELEVANCE_THRESHOLD:
        return ("Den här frågan faller utanför mitt område. "
                "Kontakta SHV eller skriv i den allmänna chatten.")

    context_parts = []
    for doc, meta in zip(
        results['documents'][0],
        results['metadatas'][0]
    ):
        context_parts.append(f"[Källa: {meta['source']}]\n{doc}")
    context = "\n\n---\n\n".join(context_parts)

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content":
             f"Relevanta dokument:\n{context}\n\nFråga: {question}"}
        ],
        options={"temperature": 0}
    )

    return response.message.content