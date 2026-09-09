"""
Embedding Generator using local sentence-transformers.
Encodes normalized canonical fact representations into 384-dimensional dense vectors.
"""

import logging
from typing import List, Union
import numpy as np
from core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Wrapper around SentenceTransformer with L2 normalization for cosine similarity search."""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingGenerator, cls).__new__(cls)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer: {e}")
            self._model = None

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Encode text or list of texts into L2-normalized numpy vectors.
        """
        if isinstance(texts, str):
            texts = [texts]

        if self._model is not None:
            embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            # L2 normalize
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return (embeddings / norms).astype(np.float32)
        else:
            # Deterministic fallback pseudo-embeddings for testing if model cannot load
            logger.warning("Using fallback deterministic pseudo-embeddings.")
            dim = settings.EMBEDDING_DIM
            res = np.zeros((len(texts), dim), dtype=np.float32)
            for i, t in enumerate(texts):
                for char_idx, char in enumerate(t[:dim]):
                    res[i, char_idx % dim] += ord(char)
                norm = np.linalg.norm(res[i])
                if norm > 0:
                    res[i] /= norm
            return res
