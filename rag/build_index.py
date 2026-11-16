import json
import re
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

RAG_DIR = Path(__file__).resolve().parent
CORPUS_DIR = RAG_DIR / "corpus"
INDEX_DIR = RAG_DIR / "faiss_index"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def parse_document(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    meta = {"titulo": path.stem, "fuentes": []}
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return meta, text
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("titulo:"):
            meta["titulo"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- "):
            meta["fuentes"].append(stripped[2:].strip())
    return meta, text[match.end():]


def split_sections(body: str) -> list[tuple[str, str]]:
    sections = []
    current_title = "Introducción"
    current_lines = []
    for line in body.splitlines():
        if line.startswith("## "):
            sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line[3:].strip()
            current_lines = []
        elif not line.startswith("# "):
            current_lines.append(line)
    sections.append((current_title, "\n".join(current_lines).strip()))
    return [(title, content) for title, content in sections if content]


def build_chunks() -> list[dict]:
    chunks = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        meta, body = parse_document(path)
        for section, content in split_sections(body):
            chunks.append({
                "id": len(chunks),
                "documento": path.name,
                "titulo": meta["titulo"],
                "seccion": section,
                "fuentes": meta["fuentes"],
                "texto": f"{meta['titulo']} - {section}\n{content}",
            })
    return chunks


def main() -> None:
    chunks = build_chunks()
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(
        [chunk["texto"] for chunk in chunks],
        normalize_embeddings=True,
        show_progress_bar=True,
    ).astype(np.float32)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    INDEX_DIR.mkdir(exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "index.faiss"))
    (INDEX_DIR / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    documentos = len({chunk["documento"] for chunk in chunks})
    print(f"{len(chunks)} fragmentos de {documentos} documentos indexados")


if __name__ == "__main__":
    main()
