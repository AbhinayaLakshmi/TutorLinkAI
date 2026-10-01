"""
Identity Similarity Evaluation Harness for TutorLinkAI.

This module provides an isolated, research-grade evaluation harness for measuring 
and analyzing SFace cosine similarity distributions across Genuine and Impostor 
certificate-to-live identity pairs.

Design & Research Principles:
1. Pure Empirical Measurement: Measures raw continuous cosine similarity [-1.0, 1.0].
   Does NOT apply any decision thresholds or verdict classifications (e.g., VERIFIED).
2. Privacy & Biometric Protection: Does NOT write biometric embeddings, vectors, 
   or raw face images to disk or evaluation report files.
3. Modular Reuse: Direct integration with CertificateFaceService, FaceEmbedder, 
   and BaseFaceDetector.
"""

import os
import csv
import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
import cv2

from backend.app.services.face import CertificateFaceService, BaseFaceDetector, HaarCascadeFaceDetector
from backend.app.services.face_embedder import FaceEmbedder

logger = logging.getLogger("identity_evaluator")


@dataclass
class PairEvaluationResult:
    """Stores the evaluation outcome for a single genuine or impostor pair."""
    pair_id: str
    pair_type: str  # "GENUINE" or "IMPOSTOR"
    status: str     # "SUCCESS", "EXTRACTION_FAILED", "INVALID_INPUT", "ERROR"
    similarity: Optional[float]
    cert_face_detected: bool
    cert_quality: Optional[str]
    live_face_detected: bool
    live_quality: Optional[str]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable dictionary representation."""
        return {
            "pair_id": str(self.pair_id),
            "pair_type": str(self.pair_type).upper(),
            "status": str(self.status),
            "similarity": float(self.similarity) if self.similarity is not None else None,
            "cert_face_detected": bool(self.cert_face_detected),
            "cert_quality": self.cert_quality,
            "live_face_detected": bool(self.live_face_detected),
            "live_quality": self.live_quality,
            "reason": str(self.reason)
        }


@dataclass
class EvaluationSummary:
    """Aggregates distribution statistics for an evaluation run."""
    total_pairs: int
    genuine_total: int
    genuine_valid: int
    genuine_failed: int
    genuine_stats: Optional[Dict[str, float]]
    impostor_total: int
    impostor_valid: int
    impostor_failed: int
    impostor_stats: Optional[Dict[str, float]]

    def to_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable summary dictionary."""
        return {
            "total_pairs": self.total_pairs,
            "genuine": {
                "total": self.genuine_total,
                "valid": self.genuine_valid,
                "failed": self.genuine_failed,
                "distribution": self.genuine_stats
            },
            "impostor": {
                "total": self.impostor_total,
                "valid": self.impostor_valid,
                "failed": self.impostor_failed,
                "distribution": self.impostor_stats
            }
        }


class IdentityEvaluator:
    """
    Evaluation harness for certificate-to-live face identity matching.
    """

    def __init__(
        self,
        cert_service: Optional[CertificateFaceService] = None,
        embedder: Optional[FaceEmbedder] = None,
        detector: Optional[BaseFaceDetector] = None
    ):
        self.detector = detector or HaarCascadeFaceDetector()
        self.cert_service = cert_service or CertificateFaceService(detector=self.detector)
        self.embedder = embedder or FaceEmbedder()

    def _extract_live_crop(self, live_input: Union[str, np.ndarray]) -> Tuple[Optional[np.ndarray], bool, Optional[str], str]:
        """
        Extracts face crop from live input (image filepath or pre-loaded numpy array).
        Returns: (crop, face_detected, quality, reason)
        """
        if live_input is None:
            return None, False, None, "Live input is None."

        if isinstance(live_input, np.ndarray):
            if live_input.size == 0 or len(live_input.shape) != 3:
                return None, False, None, "Invalid numpy array for live input."
            return live_input, True, "PRE_CROPPED", "Using pre-cropped live image."

        if isinstance(live_input, str):
            if not os.path.exists(live_input):
                return None, False, None, f"Live image file not found at: {live_input}"
            
            img = cv2.imread(live_input)
            if img is None:
                return None, False, None, f"Failed to decode live image file: {live_input}"

            bboxes = self.detector.detect(img)
            if len(bboxes) == 0:
                return None, False, "POOR", "No face detected in live capture frame."
            if len(bboxes) > 1:
                return None, True, "REQUIRES_REVIEW", f"Multiple faces ({len(bboxes)}) detected in live frame."

            x, y, w, h = bboxes[0]
            if w < 40 or h < 40:
                return None, True, "POOR", f"Live face region too small ({w}x{h} px)."

            img_h, img_w = img.shape[:2]
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(img_w, x + w), min(img_h, y + h)
            crop = img[y1:y2, x1:x2]

            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            quality = "GOOD" if blur_score >= 10.0 else "POOR"

            return crop, True, quality, "Single live face crop successfully extracted."

        return None, False, None, f"Unsupported live input type: {type(live_input)}"

    def _extract_certificate_crop(self, cert_input: Union[str, np.ndarray]) -> Tuple[Optional[np.ndarray], bool, Optional[str], str]:
        """
        Extracts face crop from certificate input (PDF/image filepath or numpy array).
        Returns: (crop, face_detected, quality, reason)
        """
        if cert_input is None:
            return None, False, None, "Certificate input is None."

        if isinstance(cert_input, np.ndarray):
            if cert_input.size == 0 or len(cert_input.shape) != 3:
                return None, False, None, "Invalid numpy array for certificate input."
            return cert_input, True, "PRE_CROPPED", "Using pre-cropped certificate image."

        if isinstance(cert_input, str):
            if not os.path.exists(cert_input):
                return None, False, None, f"Certificate file not found at: {cert_input}"

            res = self.cert_service.extract_certificate_face(cert_input)
            crop = res.get("face_crop")
            detected = res.get("face_detected", False)
            quality = res.get("quality")
            reason = res.get("reason", "")
            return crop, detected, quality, reason

        return None, False, None, f"Unsupported certificate input type: {type(cert_input)}"

    def evaluate_pair(
        self,
        pair_id: str,
        pair_type: str,
        cert_input: Union[str, np.ndarray],
        live_input: Union[str, np.ndarray]
    ) -> PairEvaluationResult:
        """
        Evaluates a single identity pair (genuine or impostor).
        Extracts crops, generates 128-D SFace embeddings, and calculates cosine similarity.
        """
        pair_type_norm = pair_type.upper().strip()
        if pair_type_norm not in ("GENUINE", "IMPOSTOR"):
            pair_type_norm = "UNKNOWN"

        # 1. Certificate face extraction
        try:
            cert_crop, cert_detected, cert_quality, cert_reason = self._extract_certificate_crop(cert_input)
        except Exception as e:
            return PairEvaluationResult(
                pair_id=pair_id,
                pair_type=pair_type_norm,
                status="ERROR",
                similarity=None,
                cert_face_detected=False,
                cert_quality="ERROR",
                live_face_detected=False,
                live_quality=None,
                reason=f"Certificate extraction error: {str(e)}"
            )

        # 2. Live face extraction
        try:
            live_crop, live_detected, live_quality, live_reason = self._extract_live_crop(live_input)
        except Exception as e:
            return PairEvaluationResult(
                pair_id=pair_id,
                pair_type=pair_type_norm,
                status="ERROR",
                similarity=None,
                cert_face_detected=cert_detected,
                cert_quality=cert_quality,
                live_face_detected=False,
                live_quality="ERROR",
                reason=f"Live extraction error: {str(e)}"
            )

        # 3. Check prerequisites for embedding comparison
        if cert_crop is None:
            return PairEvaluationResult(
                pair_id=pair_id,
                pair_type=pair_type_norm,
                status="EXTRACTION_FAILED",
                similarity=None,
                cert_face_detected=cert_detected,
                cert_quality=cert_quality,
                live_face_detected=live_detected,
                live_quality=live_quality,
                reason=f"Certificate face unavailable: {cert_reason}"
            )

        if live_crop is None:
            return PairEvaluationResult(
                pair_id=pair_id,
                pair_type=pair_type_norm,
                status="EXTRACTION_FAILED",
                similarity=None,
                cert_face_detected=cert_detected,
                cert_quality=cert_quality,
                live_face_detected=live_detected,
                live_quality=live_quality,
                reason=f"Live face unavailable: {live_reason}"
            )

        # 4. Feature embedding & Cosine similarity
        try:
            e_cert = self.embedder.extract_embedding(cert_crop)
            e_live = self.embedder.extract_embedding(live_crop)
            similarity = self.embedder.compute_cosine_similarity(e_cert, e_live)

            return PairEvaluationResult(
                pair_id=pair_id,
                pair_type=pair_type_norm,
                status="SUCCESS",
                similarity=float(similarity),
                cert_face_detected=True,
                cert_quality=cert_quality,
                live_face_detected=True,
                live_quality=live_quality,
                reason="Both faces successfully extracted and compared."
            )
        except Exception as e:
            return PairEvaluationResult(
                pair_id=pair_id,
                pair_type=pair_type_norm,
                status="ERROR",
                similarity=None,
                cert_face_detected=True,
                cert_quality=cert_quality,
                live_face_detected=True,
                live_quality=live_quality,
                reason=f"Embedding comparison failure: {str(e)}"
            )

    @staticmethod
    def calculate_distribution_statistics(similarities: List[float]) -> Optional[Dict[str, float]]:
        """Computes descriptive statistics for a list of valid cosine similarities."""
        if not similarities:
            return None

        arr = np.array(similarities, dtype=np.float64)
        return {
            "count": int(len(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "std": float(np.std(arr)),
            "p25": float(np.percentile(arr, 25)),
            "p75": float(np.percentile(arr, 75))
        }

    def summarize_results(self, results: List[PairEvaluationResult]) -> EvaluationSummary:
        """Aggregates individual evaluation results into an EvaluationSummary."""
        genuine_sims = [r.similarity for r in results if r.pair_type == "GENUINE" and r.similarity is not None]
        impostor_sims = [r.similarity for r in results if r.pair_type == "IMPOSTOR" and r.similarity is not None]

        genuine_total = sum(1 for r in results if r.pair_type == "GENUINE")
        impostor_total = sum(1 for r in results if r.pair_type == "IMPOSTOR")

        return EvaluationSummary(
            total_pairs=len(results),
            genuine_total=genuine_total,
            genuine_valid=len(genuine_sims),
            genuine_failed=genuine_total - len(genuine_sims),
            genuine_stats=self.calculate_distribution_statistics(genuine_sims),
            impostor_total=impostor_total,
            impostor_valid=len(impostor_sims),
            impostor_failed=impostor_total - len(impostor_sims),
            impostor_stats=self.calculate_distribution_statistics(impostor_sims)
        )

    def evaluate_manifest(self, pairs: List[Dict[str, Any]]) -> Tuple[List[PairEvaluationResult], EvaluationSummary]:
        """
        Evaluates a list of pair specifications.
        Each item in pairs must have: 'pair_id', 'pair_type', 'cert_input', 'live_input'.
        """
        results = []
        for item in pairs:
            res = self.evaluate_pair(
                pair_id=str(item.get("pair_id")),
                pair_type=str(item.get("pair_type", "GENUINE")),
                cert_input=item.get("cert_input"),
                live_input=item.get("live_input")
            )
            results.append(res)

        summary = self.summarize_results(results)
        return results, summary

    def evaluate_directory(self, base_dir: str) -> Tuple[List[PairEvaluationResult], EvaluationSummary]:
        """
        Evaluates pairs organized in standard dataset directory layout:
        base_dir/
            genuine/
                pair_001_cert.pdf / .png / .jpg
                pair_001_live.png / .jpg
            impostor/
                pair_001_cert.pdf / .png / .jpg
                pair_001_live.png / .jpg
        """
        pairs = []
        if not os.path.exists(base_dir):
            raise FileNotFoundError(f"Evaluation directory not found: {base_dir}")

        for pair_type in ["genuine", "impostor"]:
            type_dir = os.path.join(base_dir, pair_type)
            if not os.path.exists(type_dir):
                continue

            files = os.listdir(type_dir)
            cert_files = {}
            live_files = {}

            for f in sorted(files):
                full_path = os.path.join(type_dir, f)
                stem, _ = os.path.splitext(f)
                
                if "_cert" in stem or "_certificate" in stem:
                    prefix = stem.replace("_certificate", "").replace("_cert", "")
                    cert_files[prefix] = full_path
                elif "_live" in stem or "_camera" in stem:
                    prefix = stem.replace("_camera", "").replace("_live", "")
                    live_files[prefix] = full_path

            # Match by prefix
            all_prefixes = sorted(set(cert_files.keys()).union(set(live_files.keys())))
            for pfx in all_prefixes:
                pairs.append({
                    "pair_id": f"{pair_type}_{pfx}",
                    "pair_type": pair_type.upper(),
                    "cert_input": cert_files.get(pfx),
                    "live_input": live_files.get(pfx)
                })

        return self.evaluate_manifest(pairs)

    @staticmethod
    def export_results_csv(results: List[PairEvaluationResult], output_file: str) -> None:
        """Exports individual pair evaluation outcomes to CSV (metadata & similarity only)."""
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        with open(output_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "pair_id",
                "pair_type",
                "status",
                "similarity",
                "cert_face_detected",
                "cert_quality",
                "live_face_detected",
                "live_quality",
                "reason"
            ])
            for r in results:
                writer.writerow([
                    r.pair_id,
                    r.pair_type,
                    r.status,
                    f"{r.similarity:.6f}" if r.similarity is not None else "",
                    r.cert_face_detected,
                    r.cert_quality or "",
                    r.live_face_detected,
                    r.live_quality or "",
                    r.reason
                ])

    @staticmethod
    def export_results_json(
        results: List[PairEvaluationResult],
        summary: EvaluationSummary,
        output_file: str
    ) -> None:
        """Exports full evaluation run metadata and summary to JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        payload = {
            "summary": summary.to_dict(),
            "results": [r.to_dict() for r in results]
        }
        with open(output_file, mode="w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
