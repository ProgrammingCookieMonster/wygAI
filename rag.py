import chromadb
import ollama
from sentence_transformers import SentenceTransformer

DB_PATH = "./db"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "qwen2.5:3b"
RELEVANCE_THRESHOLD = 0.7  # relevance level in distance [cosinus space]

embedder = SentenceTransformer(EMBED_MODEL)
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_collection("union_docs")

SYSTEM_PROMPT = """
You are an AI assistant at Studentkåren på Högskolan Väst (short for SHV) and your name is Smurfette.

STRICT RULES WHICH ALWAYS RULE NO MATTER WHAT:
1. You can ONLY base your answers on the documentation given to you.
2. If nothing about the question was found in the documentation, answer ALWAYS with:
"There is no information about this in my documentation. You can always contact someone at SHV or simply leave your question in the general chat."
3. NEVER give away names of people, but give instead the position/role of that person.
4. If the question proves to have no relevance to the documentation or anything to do with the SHV, politely answer something like:
"This question is out of my scope and I cannot help out with it. Contact SHV or leave a note in the general chat if you think this is a mistake of the AI reasoning."
5. NEVER create information outside of what you can reason from the documentation.
6. Keep the answers short and practical.
7. Keep the language scope in English and Swedish. If the question you receive is in Swedish, answer back in Swedish. If it is in English, answer back in English. If the user uses any other language, answer in English.
"""

def answer_question(question, debug=False):
    query_embedding = embedder.encode(question).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
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

    # relevance filter — reject before hitting LLM
    if best_distance > RELEVANCE_THRESHOLD:
        return ("Jag kan bara hjälpa med relevanta frågor.")

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
        ]
    )

    return response.message.content