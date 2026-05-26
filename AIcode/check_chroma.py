# test file for the chroma database
# check if collection exists and has items

import chromadb
from config import DB_DIR, CHROMA_COLLECTION_NAME

client = chromadb.PersistentClient(path=DB_DIR)

cols = client.list_collections()
print("Collections: ", [getattr(c, "name", str(c)) for c in cols])

# get collection object
col = client.get_collection(CHROMA_COLLECTION_NAME)
print("Collection object type: ", type(col))
try:
    print("Collection name: ", getattr(col, "name", CHROMA_COLLECTION_NAME))
except Exception:
    pass

# count documents/vectors
try:
    print("Count: ", col.count())
except Exception as e:
    print("count() failed: ", e)

# peek a document sample
try:
    sample = col.peek(1)
    print("Sample peek: ", sample)
except Exception as e:
    print("Peek failed: ", e)