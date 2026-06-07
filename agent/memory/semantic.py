"""
Semantic memory — ChromaDB vector store of regulatory documents.
Supports natural-language queries: "SOX obligations for audio authorization failures"
"""

import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_DIR = os.getenv("CHROMA_DIR", "./memory_store/chroma_db")
COLLECTION  = "compliance_regulations"


class SemanticMemory:
    def __init__(self):
        os.makedirs(CHROMA_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        # Use the built-in sentence-transformers embedding function
        self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION,
            embedding_function=self._ef,
        )

    def query(self, text: str, n_results: int = 3) -> str:
        """Return the top-N most relevant regulation snippets as a single string."""
        try:
            count = self.collection.count()
            if count == 0:
                return "Regulatory knowledge base is empty. Run scripts/init_memory.py first."
            results = self.collection.query(
                query_texts=[text],
                n_results=min(n_results, count),
            )
            docs = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            if not docs:
                return "No relevant regulations found for this query."
            snippets = []
            for doc, meta in zip(docs, metadatas):
                source = meta.get("source", "regulation")
                snippets.append(f"[{source}]\n{doc}")
            return "\n\n".join(snippets)
        except Exception as e:
            return f"Semantic memory unavailable: {e}"

    def add_document(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        """Add a regulation document (called by knowledge_base/loader.py)."""
        try:
            self.collection.add(
                documents=[text],
                ids=[doc_id],
                metadatas=[metadata or {}],
            )
        except Exception:
            # Already exists — skip silently (idempotent)
            pass

    def count(self) -> int:
        return self.collection.count()
