import json
from functools import lru_cache

import faiss
from sentence_transformers import SentenceTransformer

from rag.build_index import INDEX_DIR, MODEL_NAME


@lru_cache(maxsize=1)
def _load():
    index = faiss.read_index(str(INDEX_DIR / "index.faiss"))
    chunks = json.loads((INDEX_DIR / "chunks.json").read_text(encoding="utf-8"))
    model = SentenceTransformer(MODEL_NAME)
    return index, chunks, model


def search(query: str, k: int = 4) -> list[dict]:
    index, chunks, model = _load()
    vector = model.encode([query], normalize_embeddings=True).astype("float32")
    scores, ids = index.search(vector, k)
    return [
        {**chunks[i], "score": float(score)}
        for score, i in zip(scores[0], ids[0])
        if i != -1
    ]
