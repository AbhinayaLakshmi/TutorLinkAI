"""
Face Embedding Service for TutorLinkAI.

This service utilizes the official OpenCV Zoo SFace deep learning model 
(face_recognition_sface_2021dec.onnx) to generate 128-dimensional L2-normalized 
facial identity embeddings from pre-cropped certificate and live face images.

Architecture Notes:
- Model: SFace (SphereFace/CosFace angular margin loss architecture).
- Embedding Dimension: 128-D float32 vector (L2-normalized).
- Identity Comparison: Provides pure cosine similarity calculation.
- Research Notice: No hardcoded identity matching threshold is applied in this module.
  Optimal operational decision thresholds (e.g. FAR/FRR trade-off calibration) 
  will be established experimentally during dataset evaluation.
"""

import os
import cv2
import numpy as np
from typing import Optional


DEFAULT_MODEL_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "models",
        "face_recognition_sface_2021dec.onnx"
    )
)


class FaceEmbedder:
    """
    Extracts L2-normalized 128-D face embeddings and computes cosine similarity
    using OpenCV SFace (cv2.FaceRecognizerSF).
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initializes the SFace FaceRecognizerSF model.

        Args:
            model_path: Optional absolute or relative path to the SFace ONNX model file.
                        Defaults to backend/models/face_recognition_sface_2021dec.onnx.

        Raises:
            FileNotFoundError: If the model weight file cannot be located on disk.
            RuntimeError: If OpenCV fails to initialize the SFace neural network.
        """
        self.model_path = model_path or DEFAULT_MODEL_PATH
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"SFace model file not found at: {self.model_path}. "
                "Please ensure the model weights are downloaded to the backend/models directory."
            )

        try:
            self.recognizer = cv2.FaceRecognizerSF.create(self.model_path, "")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize cv2.FaceRecognizerSF from {self.model_path}: {str(e)}")

    def extract_embedding(
        self,
        face_crop: np.ndarray,
        landmarks: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Extracts an L2-normalized 128-dimensional float32 feature embedding vector.

        Args:
            face_crop: 3-channel BGR image array containing the face region.
            landmarks: Optional 15-element array or 5-point landmark matrix for alignCrop.

        Returns:
            np.ndarray of shape (1, 128) and dtype float32 with L2 norm == 1.0.

        Raises:
            ValueError: If face_crop is None, empty, has invalid dimensions, or invalid channels.
        """
        if face_crop is None:
            raise ValueError("Input face_crop cannot be None.")

        if not isinstance(face_crop, np.ndarray):
            raise ValueError(f"Input face_crop must be a numpy.ndarray, got {type(face_crop)}.")

        if face_crop.size == 0:
            raise ValueError("Input face_crop array is empty (size == 0).")

        if len(face_crop.shape) != 3:
            raise ValueError(
                f"Input face_crop must have 3 dimensions (H, W, C), got shape {face_crop.shape}."
            )

        h, w, c = face_crop.shape
        if c != 3:
            raise ValueError(f"Input face_crop must have 3 color channels (BGR), got {c} channels.")

        if h < 20 or w < 20:
            raise ValueError(f"Input face_crop resolution ({w}x{h}) is too small for feature extraction.")

        # Preprocessing & alignment
        if landmarks is not None:
            try:
                preprocessed = self.recognizer.alignCrop(face_crop, landmarks)
            except Exception:
                # Fallback to standard aspect resize if landmarks array formatting mismatches
                preprocessed = cv2.resize(face_crop, (112, 112), interpolation=cv2.INTER_LINEAR)
        else:
            if (h, w) == (112, 112):
                preprocessed = face_crop
            else:
                preprocessed = cv2.resize(face_crop, (112, 112), interpolation=cv2.INTER_LINEAR)

        # Ensure correct memory layout and uint8 type for OpenCV DNN
        if preprocessed.dtype != np.uint8:
            preprocessed = np.clip(preprocessed, 0, 255).astype(np.uint8)

        # Forward pass through SFace network
        raw_feature = self.recognizer.feature(preprocessed)

        if raw_feature is None or raw_feature.size == 0:
            raise RuntimeError("SFace model returned an empty feature vector.")

        # Verify numerical sanity (no NaN or Inf)
        if not np.all(np.isfinite(raw_feature)):
            raise ValueError("SFace feature extraction produced non-finite values (NaN/Inf).")

        # L2-normalization to ensure unit sphere representation
        norm = np.linalg.norm(raw_feature)
        if norm == 0 or np.isnan(norm):
            raise ValueError("SFace feature vector has a zero or undefined L2 norm.")

        normalized_embedding = (raw_feature / norm).astype(np.float32)
        return normalized_embedding

    def compute_cosine_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Computes the Cosine Similarity between two L2-normalized face embeddings.

        Args:
            embedding1: (1, 128) or (128,) float32 embedding vector.
            embedding2: (1, 128) or (128,) float32 embedding vector.

        Returns:
            Cosine similarity score as a float in the range [-1.0, 1.0].
            (Note: No identity decision threshold is applied at this stage).

        Raises:
            ValueError: If either embedding is None, empty, non-finite, or has mismatched shape.
        """
        if embedding1 is None or embedding2 is None:
            raise ValueError("Embeddings cannot be None.")

        if not isinstance(embedding1, np.ndarray) or not isinstance(embedding2, np.ndarray):
            raise ValueError("Both embeddings must be numpy arrays.")

        if embedding1.size == 0 or embedding2.size == 0:
            raise ValueError("Embedding arrays cannot be empty.")

        if not np.all(np.isfinite(embedding1)) or not np.all(np.isfinite(embedding2)):
            raise ValueError("Embeddings contain non-finite numbers (NaN/Inf).")

        vec1 = embedding1.flatten()
        vec2 = embedding2.flatten()

        if vec1.shape != vec2.shape:
            raise ValueError(f"Embedding shape mismatch: {vec1.shape} vs {vec2.shape}.")

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            raise ValueError("Cannot compute similarity with a zero-length embedding vector.")

        cosine_sim = float(np.dot(vec1, vec2) / (norm1 * norm2))
        # Clamp to [-1.0, 1.0] to guard against minor float precision leakage
        return float(np.clip(cosine_sim, -1.0, 1.0))

    def compare_face_crops(
        self,
        face_crop1: np.ndarray,
        face_crop2: np.ndarray,
        landmarks1: Optional[np.ndarray] = None,
        landmarks2: Optional[np.ndarray] = None
    ) -> float:
        """
        Convenience method to extract embeddings from two face crops and compute their cosine similarity.

        Args:
            face_crop1: 3-channel BGR image array of the first face.
            face_crop2: 3-channel BGR image array of the second face.
            landmarks1: Optional landmarks for face_crop1.
            landmarks2: Optional landmarks for face_crop2.

        Returns:
            Cosine similarity as a float in [-1.0, 1.0].
        """
        emb1 = self.extract_embedding(face_crop1, landmarks=landmarks1)
        emb2 = self.extract_embedding(face_crop2, landmarks=landmarks2)
        return self.compute_cosine_similarity(emb1, emb2)

