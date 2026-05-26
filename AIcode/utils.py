# utils --> utility functions used for documentation loadout and text chunks transformation for the ChromaDB

import fitz
import os
import re
from typing import List

def extract_text_from_pdf(path: str) -> str:
    doc = fitz.open(path)
    parts = []
    for page in doc:
        parts.append(page.get_text())
    return "\n".join(parts)

def simple_chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = re.sub(r'\s+', ' ', text).strip()
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = min(start + chunk_size, L)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == L:
            break
        start = max(end - overlap, start + 1)
    return chunks

def normalize_filename(path: str) -> str:
    return os.path.basename(path)