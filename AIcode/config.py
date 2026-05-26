# config.py -- general configuration for directories, database, ollama
# In case you implement this on the server, have an .env file on the main folder of the project

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
DB_DIR = os.path.join(BASE_DIR, "db")
CHROMA_COLLECTION_NAME = "union_documents"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
#giving a fair size for chunks, overlap & threshold, so model will be ok at fair level // should not hallucinate answers
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
SIMILARITY_THRESHOLD = 0.65

TOP_K = 5
OLLAMA_URL = os.environ.get("OLLAMA_URL")
OLLAMA_MODEL = "qwen2.5:1.5b"
FALLBACK_CONTACT = "The bot is not frequently updated and can be wrong. Please be cautious with sensible/important information and contact the Union Board if you want to be sure."
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

# can help with easy access to slash commands directly on the server
GUILD_ID = os.environ.get("GUILD_ID")
if GUILD_ID:
    try:
        GUILD_ID = int(GUILD_ID)
    except ValueError:
        GUILD_ID = None