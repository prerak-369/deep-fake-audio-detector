"""
Knowledge base loader — chunks regulation documents and loads them into ChromaDB.
Idempotent: already-loaded documents are skipped by ID.

Usage:
    python knowledge_base/loader.py
Or imported by scripts/init_memory.py
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

REGULATIONS_DIR = Path(__file__).parent / "regulations"
CHUNK_SIZE      = 500   # characters per chunk
CHUNK_OVERLAP   = 50    # overlap between consecutive chunks


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start  = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start = end - overlap
    return [c for c in chunks if c]


def load_knowledge_base(verbose: bool = True) -> int:
    """
    Load all .txt files from knowledge_base/regulations/ into ChromaDB.
    Returns the number of new chunks added.
    """
    from agent.memory.semantic import SemanticMemory
    memory = SemanticMemory()

    added = 0
    for txt_file in sorted(REGULATIONS_DIR.glob("*.txt")):
        source   = txt_file.stem
        raw_text = txt_file.read_text(encoding="utf-8")
        chunks   = chunk_text(raw_text)

        for i, chunk in enumerate(chunks):
            doc_id = f"{source}_chunk_{i:03d}"
            memory.add_document(doc_id, chunk, metadata={"source": source, "chunk": i})
            added += 1

        if verbose:
            print(f"  ✓  {txt_file.name}  →  {len(chunks)} chunks loaded")

    if verbose:
        print(f"\nKnowledge base: {added} total chunks in ChromaDB "
              f"(collection count: {memory.count()})")
    return added


if __name__ == "__main__":
    print("Loading VoiceGuard knowledge base into ChromaDB...")
    load_knowledge_base()
