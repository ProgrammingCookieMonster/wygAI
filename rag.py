import chromadb
import ollama
from sentence_transformers import SentenceTransformer

DB_PATH = "./db"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "qwen2.5:1.5b"

# load once, reuse
embedder = SentenceTransformer(EMBED_MODEL)
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_collection("union_docs")

SYSTEM_PROMPT = """Du är en assistent för studentkåren.
Du svarar på frågor baserat ENBART på de dokument som tillhandahålls.
Hänvisa alltid till positioner och roller, aldrig till specifika namn.
Om svaret inte finns i dokumenten, säg tydligt att du inte har den informationen
och föreslå att användaren kontaktar kårstyrelsen direkt.
Håll svaren kortfattade och praktiska.
Du svarar på svenska om frågan är på svenska, på engelska om frågan är på engelska.
"""

def answer_question(question):
    # embed the question
    query_embedding = embedder.encode(question).tolist()

    # retrieve relevant chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    # check if anything relevant was found
    if not results['documents'][0]:
        return "Jag hittade ingen relevant information i dokumentationen."

    # build context with source references
    context_parts = []
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        context_parts.append(f"[Källa: {meta['source']}]\n{doc}")
    context = "\n\n---\n\n".join(context_parts)

    # ask the LLM
    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"Relevanta dokument:\n{context}\n\nFråga: {question}"
            }
        ]
    )

    return response.message.content