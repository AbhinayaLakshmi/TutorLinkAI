"""
Embeddings generation and semantic similarity computation using Sentence Transformers.
"""
from typing import List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from .config import MODEL_NAME


class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.model: SentenceTransformer = SentenceTransformer(model_name)

    @classmethod
    def get_instance(cls, model_name: str = MODEL_NAME) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = cls(model_name=model_name)
        return cls._instance

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Encode a single string or list of strings into normalized embedding vectors.
        """
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings

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
