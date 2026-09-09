"""
Vector Store using FAISS with NumPy cosine fallback.
Indexes canonical fact representations for high-speed candidate retrieval.
Supports incremental updates and disk persistence.
"""

import os
import json
import logging
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import numpy as np

from core.config import settings
from retrieval.embeddings import EmbeddingGenerator
from models.fact import Fact

logger = logging.getLogger(__name__)

class VectorStore:
    """FAISS vector index managing dense fact embeddings with persistence and incremental addition."""

    def __init__(self, index_path: Optional[str] = None):
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.meta_path = self.index_path + ".meta.json"
        self.dim = settings.EMBEDDING_DIM
        self.embedder = EmbeddingGenerator()
        self.fact_ids: List[str] = []
        self.vectors: Optional[np.ndarray] = None
        self.index = None
        self.use_faiss = False

        self._init_index()
        self.load()

    def _init_index(self):
        try:
            import faiss
            self.index = faiss.IndexFlatIP(self.dim)
            self.use_faiss = True
            logger.info("Initialized FAISS IndexFlatIP.")
        except Exception as e:
            logger.warning(f"FAISS not available ({e}). Using NumPy vector store.")
            self.use_faiss = False

    def add_facts(self, facts: List[Fact]):
        """Incrementally encode and index facts."""
        if not facts:
            return

        texts = [f.to_canonical_representation() for f in facts]
        embs = self.embedder.encode(texts)

        if self.use_faiss and self.index is not None:
            self.index.add(embs)
        
        # Keep vectors in numpy array for fallback and persistence
        if self.vectors is None or len(self.vectors) == 0:
            self.vectors = embs
        else:
            self.vectors = np.vstack([self.vectors, embs])

        for f in facts:
            self.fact_ids.append(f.fact_id)

        self.save()
        logger.info(f"Indexed {len(facts)} facts. Total in index: {len(self.fact_ids)}.")

    def search(self, query: str, top_k: int = 10, threshold: float = 0.50) -> List[Tuple[str, float]]:
        """
        Query index and return (fact_id, similarity_score).
        """
        if not self.fact_ids or self.vectors is None or len(self.vectors) == 0:
            return []

        query_emb = self.embedder.encode(query)

        if self.use_faiss and self.index is not None and self.index.ntotal > 0:
            scores, indices = self.index.search(query_emb, min(top_k, self.index.ntotal))
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.fact_ids) and score >= threshold:
                    results.append((self.fact_ids[idx], float(score)))
            return results
        else:
            # NumPy cosine similarity search
            sims = np.dot(self.vectors, query_emb.T).flatten()
            top_indices = np.argsort(-sims)[:top_k]
            results = []
            for idx in top_indices:
                score = float(sims[idx])
                if score >= threshold and idx < len(self.fact_ids):
                    results.append((self.fact_ids[idx], score))
            return results

    def save(self):
        """Save index and metadata to disk."""
        try:
            p = Path(self.index_path)
            p.parent.mkdir(parents=True, exist_ok=True)

            if self.use_faiss and self.index is not None:
                import faiss
                faiss.write_index(self.index, self.index_path)

            meta = {"fact_ids": self.fact_ids}
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f)
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def load(self):
        """Load index and metadata from disk if present."""
        try:
            if os.path.exists(self.meta_path):
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    self.fact_ids = meta.get("fact_ids", [])

            if self.use_faiss and os.path.exists(self.index_path):
                import faiss
                self.index = faiss.read_index(self.index_path)
                logger.info(f"Loaded FAISS index from {self.index_path} with {self.index.ntotal} vectors.")
        except Exception as e:
            logger.warning(f"Could not load existing vector store: {e}. Starting fresh.")
