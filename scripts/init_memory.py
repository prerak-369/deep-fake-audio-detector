"""
init_memory.py — One-shot setup script.
Run this once before starting the server:

    python scripts/init_memory.py

What it does:
  1. Creates memory_store/ directory
  2. Creates SQLite schema (audio_cases table)
  3. Loads all regulation documents into ChromaDB
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def main():
    print("=" * 60)
    print("VoiceGuard — Memory Initialisation")
    print("=" * 60)

    # Step 1: SQLite schema
    print("\n[1/2] Initialising SQLite database...")
    from api.database import models  # noqa: F401 — import triggers create_all()
    print("  ✓  SQLite schema created at ./memory_store/compliance.db")

    # Step 2: ChromaDB + knowledge base
    print("\n[2/2] Loading knowledge base into ChromaDB...")
    from knowledge_base.loader import load_knowledge_base
    load_knowledge_base(verbose=True)

    print("\n" + "=" * 60)
    print("✅  Memory initialisation complete. You can now start the server:")
    print("    uvicorn api.main:app --reload --port 8000")
    print("=" * 60)


if __name__ == "__main__":
    main()
