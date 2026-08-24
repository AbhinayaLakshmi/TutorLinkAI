import os
import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Tuple
import pypdfium2 as pdfium
import logging

logger = logging.getLogger("face_service")

class BaseFaceDetector:
    """
    Interface/Base class for face detection algorithms to ensure modularity.
    """
    def detect(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        raise NotImplementedError("Detect method must be implemented by subclasses.")


class HaarCascadeFaceDetector(BaseFaceDetector):
    """
    Haar Cascade implementation of face detection.
    Highly lightweight and uses built-in OpenCV resources.
    """
    def __init__(self, scale_factor: float = 1.05, min_neighbors: int = 3, min_size: Tuple[int, int] = (30, 30)):
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size = min_size
        
        # Load multiple cascades to increase robustness
        self.cascades = [
            cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"),
            cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt.xml"),
            cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml")
        ]

    def detect(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        detected_boxes = []
        
        # Run all cascades and merge/group overlapping detections
        for cascade in self.cascades:
            if cascade.empty():
                continue
            boxes = cascade.detectMultiScale(
                gray,
                scaleFactor=self.scale_factor,
                minNeighbors=self.min_neighbors,
                minSize=self.min_size
            )
            for (x, y, w, h) in boxes:
                detected_boxes.append([x, y, w, h])
                
        if not detected_boxes:
            return []
            
        # Group rectangles to merge multiple detections of the same face
        grouped_boxes, weights = cv2.groupRectangles(detected_boxes, groupThreshold=1, eps=0.2)
        return [tuple(box) for box in grouped_boxes]


class CertificateFaceService:
    """
    Phase 1 Face Verification Service: Face Extraction and Quality Assessment.
    """
    def __init__(self, detector: BaseFaceDetector = None, max_laplacian_var: float = 70.0, min_face_dim: int = 100):
        self.detector = detector or HaarCascadeFaceDetector()
        self.max_laplacian_var = max_laplacian_var
        self.min_face_dim = min_face_dim

    def render_pdf_page(self, file_path: str, page_idx: int = 0, scale: int = 4) -> np.ndarray:
        """
        Renders a PDF page to a BGR numpy array using pypdfium2.
        """
        doc = pdfium.PdfDocument(file_path)
        if page_idx >= len(doc):
            raise IndexError(f"Page index {page_idx} out of range (total pages: {len(doc)}).")
        
        page = doc[page_idx]
        bitmap = page.render(scale=scale)
        pil_img = bitmap.to_pil()
        # Convert PIL (RGB) to OpenCV (BGR)
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def extract_face_crop(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Crops face region safely from the source image.
        """
        x, y, w, h = bbox
        img_h, img_w = image.shape[:2]
        
        # Clamp coordinates to image boundaries
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(img_w, x + w)
        y2 = min(img_h, y + h)
        
        return image[y1:y2, x1:x2]

    def _is_emblem_or_seal(self, crop: np.ndarray) -> Tuple[bool, str, float]:
        """
        Filters out circular emblems, high-contrast text stamps, and decorative logos
        using Variance of Laplacian (texture sharpness/high-frequency edge ratio).
        """
        if crop.size == 0:
            return True, "Empty crop", 0.0
            
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
        # 1. Laplacian Variance Check
        # Human faces contain smooth gradients and skin regions (low variance).
        # Line-art, seals, and text borders have extremely sharp edges (high variance).
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if laplacian_var >= self.max_laplacian_var:
            return True, f"High texture variance ({laplacian_var:.2f} >= {self.max_laplacian_var}) indicating seal/stamp/emblem line-art.", laplacian_var
            
        return False, "Genuine face texture candidate", laplacian_var

    def analyze_face_quality(self, crop: np.ndarray, bbox: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """
        Assesses face size, sharpness, and quality suitability for embedding extraction.
        """
        x, y, w, h = bbox
        crop_h, crop_w = crop.shape[:2]
        
        # Blurriness metric
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Embedder suitability (ArcFace/FaceNet typically need at least 112x112 inputs)
        is_large_enough = crop_w >= 112 and crop_h >= 112
        
        # Overall quality classification
        if is_large_enough and blur_score >= 10.0:
            quality = "GOOD"
            reason = "Student portrait detected successfully."
        else:
            quality = "POOR"
            reason = f"Face resolution ({crop_w}x{crop_h}) is too low or image is too blurry."
            
        return {
            "bounding_box": [int(x), int(y), int(w), int(h)],
            "face_width": int(crop_w),
            "face_height": int(crop_h),
            "quality": quality,
            "quality_score": float(blur_score),
            "suitable_for_matching": is_large_enough,
            "reason": reason
        }

    def process_certificate(self, file_path: str, original_filename: str = None) -> Dict[str, Any]:
        """
        High-level entrypoint that loads document, runs face detection, filters candidates,
        and returns face extraction result data.
        """
        is_pdf = file_path.lower().endswith(".pdf") or (original_filename and original_filename.lower().endswith(".pdf"))
        
        pages_to_scan = []
        try:
            if is_pdf:
                doc = pdfium.PdfDocument(file_path)
                for page_idx in range(len(doc)):
                    img = self.render_pdf_page(file_path, page_idx=page_idx, scale=4)
                    pages_to_scan.append((page_idx, img))
            else:
                img = cv2.imread(file_path)
                if img is not None:
                    pages_to_scan.append((0, img))
                else:
                    raise ValueError(f"Could not load image file: {file_path}")
        except Exception as e:
            logger.error(f"Error loading certificate file: {str(e)}")
            return {
                "face_detected": False,
                "face_count": 0,
                "quality": "NOT_AVAILABLE",
                "reason": f"Failed to load certificate file: {str(e)}"
            }

        all_valid_faces = []
        
        for page_idx, page_img in pages_to_scan:
            bboxes = self.detector.detect(page_img)
            
            for bbox in bboxes:
                x, y, w, h = bbox
                
                # Size Filter: Skip tiny logo artifacts
                if w < self.min_face_dim or h < self.min_face_dim:
                    continue
                    
                crop = self.extract_face_crop(page_img, bbox)
                
                # False-Positive Filter: Seal/Logo rejection
                is_seal, reason_filter, var_val = self._is_emblem_or_seal(crop)
                if is_seal:
                    logger.info(f"Rejected candidate at page {page_idx} bbox {bbox} as seal: {reason_filter}")
                    continue
                    
                # Quality Assessment
                quality_info = self.analyze_face_quality(crop, bbox)
                quality_info["source_page"] = page_idx
                all_valid_faces.append(quality_info)

        # Handle findings
        if not all_valid_faces:
            return {
                "face_detected": False,
                "face_count": 0,
                "quality": "NOT_AVAILABLE",
                "reason": "No reliable human face detected in certificate."
            }
            
        if len(all_valid_faces) > 1:
            # Ambiguous/Multiple faces case
            return {
                "face_detected": True,
                "face_count": len(all_valid_faces),
                "quality": "REQUIRES_REVIEW",
                "reason": f"Multiple human face candidates ({len(all_valid_faces)}) detected on certificate. Visual review required.",
                "candidates": all_valid_faces
            }
            
        # Single verified face case
        face = all_valid_faces[0]
        return {
            "face_detected": True,
            "face_count": 1,
            "source_page": face["source_page"],
            "bounding_box": face["bounding_box"],
            "face_width": face["face_width"],
            "face_height": face["face_height"],
            "quality": face["quality"],
            "quality_score": face["quality_score"],
            "suitable_for_matching": face["suitable_for_matching"],
            "reason": face["reason"]
        }
