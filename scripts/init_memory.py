# -*- coding: utf-8 -*-
"""
init_memory.py - One-shot setup script.
Run this once before starting the server:

    python scripts/init_memory.py

What it does:
  1. Creates memory_store/ directory
  2. Creates SQLite schema (audio_cases table)
  3. Loads all regulation documents into ChromaDB
"""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Force UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    print("=" * 60)
    print("VoiceGuard - Memory Initialisation")
    print("=" * 60)

    # Step 1: Ensure directories exist
    os.makedirs("./memory_store", exist_ok=True)
    os.makedirs("./reports", exist_ok=True)
    os.makedirs("./data/uploads", exist_ok=True)

    # Step 2: SQLite schema
    print("\n[1/2] Initialising SQLite database...")
    from api.database import models  # noqa: F401 — import triggers create_all()
    print("  [OK] SQLite schema created at ./memory_store/compliance.db")

    # Step 3: ChromaDB + knowledge base
    print("\n[2/2] Loading knowledge base into ChromaDB...")
    try:
        from knowledge_base.loader import load_knowledge_base
        load_knowledge_base(verbose=True)
        print("  [OK] Knowledge base loaded into ChromaDB")
    except ImportError as e:
        print("  [SKIP] ChromaDB not yet installed:", e)
        print("         Run: pip install chromadb sentence-transformers")
        print("         Then re-run this script to load the knowledge base.")

    print("\n" + "=" * 60)
    print("[OK] Memory initialisation complete. Start the server with:")
    print("     uvicorn api.main:app --reload --port 8000")
    print("=" * 60)


if __name__ == "__main__":
    main()
