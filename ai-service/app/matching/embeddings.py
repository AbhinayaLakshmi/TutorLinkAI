from typing import List, Union, Optional
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
from .config import MODEL_NAME


class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        if SentenceTransformer is not None:
            self.model = SentenceTransformer(model_name)
        else:
            self.model = None

    @classmethod
    def get_instance(cls, model_name: str = MODEL_NAME) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = cls(model_name=model_name)
        return cls._instance

    def _deterministic_fallback_encode(self, texts: List[str], dim: int = 384) -> np.ndarray:
        """
        Deterministic hash-based embedding fallback used when sentence_transformers is not installed.
        """
        import hashlib
        import re

        vectors = []
        for text in texts:
            vec = np.zeros(dim, dtype=np.float32)
            tokens = re.findall(r"\w+", text.lower())
            if not tokens:
                vec[0] = 1.0
            else:
                for token in tokens:
                    h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
                    idx = h % dim
                    sign = 1.0 if (h >> 1) & 1 else -1.0
                    vec[idx] += sign
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
        return np.array(vectors, dtype=np.float32)

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Encode a single string or list of strings into normalized embedding vectors.
        """
        if isinstance(texts, str):
            texts = [texts]
        if self.model is not None:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embeddings
        return self._deterministic_fallback_encode(texts)

    def compute_similarity(
        self, query_embedding: np.ndarray, candidate_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between 1D/2D query embedding and 2D candidate embeddings.
        Since embeddings are normalized, cosine similarity is simply the dot product.
        Values are clamped to [0.0, 1.0].
        """
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        if candidate_embeddings.ndim == 1:
            candidate_embeddings = candidate_embeddings.reshape(1, -1)

        sims = np.dot(candidate_embeddings, query_embedding.T).flatten()
        # Clamp negative similarities to 0.0 (and max to 1.0)
        return np.clip(sims, 0.0, 1.0)

    def compute_subject_score(
        self, student_subject_query: str, tutor_profiles: List[str]
    ) -> List[float]:
        """
        Calculates semantic similarity between student query and tutor profiles (subjects + bio).
        Returns a list of float scores in [0.0, 1.0].
        """
        if not tutor_profiles:
            return []
        query_vec = self.encode([student_subject_query])
        tutor_vecs = self.encode(tutor_profiles)
        similarities = self.compute_similarity(query_vec, tutor_vecs)
        return [float(round(s, 4)) for s in similarities]


def get_embedding_service() -> EmbeddingService:
    """Convenience getter for singleton EmbeddingService."""
    return EmbeddingService.get_instance()
