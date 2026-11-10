import json
import re
import unicodedata
from functools import lru_cache

import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from rag.build_index import INDEX_DIR, MODEL_NAME

RRF_K = 60
CANDIDATES = 20
STOPWORDS = {
    "al", "como", "con", "cual", "cuales", "de", "del", "donde", "el", "en", "es",
    "esta", "hay", "la", "las", "lo", "los", "me", "mi", "para", "por", "que", "se",
    "su", "un", "una", "y",
}


def tokenize(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    plain = "".join(char for char in normalized if not unicodedata.combining(char))
    return [token for token in re.findall(r"\w+", plain) if token not in STOPWORDS]


@lru_cache(maxsize=1)
def _load():
    index = faiss.read_index(str(INDEX_DIR / "index.faiss"))
    chunks = json.loads((INDEX_DIR / "chunks.json").read_text(encoding="utf-8"))
    model = SentenceTransformer(MODEL_NAME)
    bm25 = BM25Okapi([tokenize(chunk["texto"]) for chunk in chunks])
    return index, chunks, model, bm25


def _dense_ranking(query: str, index, model, n: int) -> list[int]:
    vector = model.encode([query], normalize_embeddings=True).astype("float32")
    _, ids = index.search(vector, n)
    return [int(i) for i in ids[0] if i != -1]


def _bm25_ranking(query: str, bm25, n: int) -> list[int]:
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [i for i in ranked[:n] if scores[i] > 0]


def search(query: str, k: int = 4) -> list[dict]:
    index, chunks, model, bm25 = _load()
    n = min(CANDIDATES, len(chunks))
    fused = {}
    for ranking in (_dense_ranking(query, index, model, n), _bm25_ranking(query, bm25, n)):
        for position, chunk_id in enumerate(ranking, 1):
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1 / (RRF_K + position)
    best = sorted(fused, key=fused.get, reverse=True)[:k]
    return [{**chunks[i], "score": fused[i]} for i in best]
