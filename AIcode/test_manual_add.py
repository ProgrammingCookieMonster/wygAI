# test adding document to the chromedb manually
import chromadb, os, uuid
from config import DB_DIR, CHROMA_COLLECTION_NAME

os.makedirs(DB_DIR, exist_ok=True)
client = chromadb.PersistentClient(path=DB_DIR)
col = client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)

# simple test on one doc
doc_id = str(uuid.uuid4())
doc = "Test to verity document Chroma add&persist"
meta= {"source":"manual_test"}

col.add(ids=[doc_id], documents=[doc], metadatas=[meta], embeddings=None)
# safety to write to the disk
if hasattr(client, "persist"):
    try:
        client.persist()
        print("client.persist() called")
    except Exception as e:
        print("persist() raised:", e)
else:
    # no persist method exposed by this Chroma version
    print("client.persist() not available; relying on automatic persistence")

print("Added id:", doc_id)
print("New count:", col.count())
print("Peek:", col.peek(1))