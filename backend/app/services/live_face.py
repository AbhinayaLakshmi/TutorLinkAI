import base64
import cv2
import numpy as np
from typing import Dict, Any, Tuple, List
from pydantic import BaseModel
import logging

from backend.app.services.face import CertificateFaceService, HaarCascadeFaceDetector, BaseFaceDetector

logger = logging.getLogger("live_face_service")

class LiveFaceUpload(BaseModel):
    action: str  # "LEFT" or "RIGHT" (random challenge direction)
    frame_straight: str
    frame_action: str

class LiveFaceService:
    def __init__(self, detector: BaseFaceDetector = None, min_face_dim: int = 100, max_blur_threshold: float = 10.0):
        self.detector = detector or HaarCascadeFaceDetector(scale_factor=1.1, min_neighbors=4)
        self.min_face_dim = min_face_dim
        self.max_blur_threshold = max_blur_threshold

    def _decode_image(self, b64_str: str) -> np.ndarray:
        """
        Decodes base64 data URI (or raw base64) string into a BGR numpy image.
        """
        if "," in b64_str:
            b64_str = b64_str.split(",")[1]
        try:
            img_data = base64.b64decode(b64_str)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Image decoding yielded None")
            return img
        except Exception as e:
            raise ValueError(f"Failed to decode base64 image: {str(e)}")

    def _get_single_face(self, img: np.ndarray) -> Tuple[Tuple[int, int, int, int], np.ndarray, str]:
        """
        Detects exactly one face from the image, checks dimensions, and returns crop.
        """
        bboxes = self.detector.detect(img)
        if len(bboxes) == 0:
            return None, None, "No face detected in capture frame."
            
        first_bbox = bboxes[0]
        if len(bboxes) > 1:
            return first_bbox, None, f"Multiple faces ({len(bboxes)}) detected in capture frame."
            
        x, y, w, h = first_bbox
        if w < self.min_face_dim or h < self.min_face_dim:
            return first_bbox, None, f"Detected face is too far/small ({w}x{h} < {self.min_face_dim}px)."
            
        # Crop safely
        img_h, img_w = img.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(img_w, x + w), min(img_h, y + h)
        crop = img[y1:y2, x1:x2]
        
        return first_bbox, crop, ""

    def verify_live_face(self, frame_straight_b64: str, frame_action_b64: str, action: str) -> Dict[str, Any]:
        """
        Decodes frames, validates quality, and assesses liveness based on pixel/bbox changes.
        """
        # Normalize action/challenge direction
        challenge = action.upper().strip()
        if "LEFT" in challenge:
            target_direction = "LEFT"
        elif "RIGHT" in challenge:
            target_direction = "RIGHT"
        else:
            target_direction = "LEFT"

        try:
            img_straight = self._decode_image(frame_straight_b64)
            img_action = self._decode_image(frame_action_b64)
        except Exception as e:
            return {
                "face_detected": False,
                "face_count": 0,
                "face_quality": "POOR",
                "liveness_status": "FAILED",
                "suitable_for_matching": False,
                "reason": f"Invalid image frames: {str(e)}"
            }

        h_s, w_s = img_straight.shape[:2]

        # 1. Detect face in straight frame
        bbox_s, crop_s, err_s = self._get_single_face(img_straight)
        if err_s:
            is_no_face = "No face" in err_s
            is_multi = "Multiple faces" in err_s
            return {
                "face_detected": not is_no_face,
                "face_count": 0 if is_no_face else (2 if is_multi else 1),
                "face_quality": "POOR",
                "liveness_status": "FAILED",
                "suitable_for_matching": False,
                "reason": err_s
            }

        # 2. Detect face in action frame
        bbox_a, crop_a, err_a = self._get_single_face(img_action)
        if err_a:
            is_no_face = "No face" in err_a
            is_multi = "Multiple faces" in err_a
            return {
                "face_detected": not is_no_face,
                "face_count": 0 if is_no_face else (2 if is_multi else 1),
                "face_quality": "POOR",
                "liveness_status": "FAILED",
                "suitable_for_matching": False,
                "reason": err_a
            }

        # 3. Quality checks (blurriness check on straight frame)
        gray_s = cv2.cvtColor(crop_s, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray_s, cv2.CV_64F).var()
        
        if blur_score < self.max_blur_threshold:
            return {
                "face_detected": True,
                "face_count": 1,
                "face_quality": "POOR",
                "liveness_status": "FAILED",
                "suitable_for_matching": False,
                "reason": "Face image is too blurry."
            }

        # 4. Liveness Assessment: Verify head movement between crops
        # Compare crops by resizing both to 100x100 and computing mean absolute difference (MAD)
        crop_s_resize = cv2.resize(cv2.cvtColor(crop_s, cv2.COLOR_BGR2GRAY), (100, 100))
        crop_a_resize = cv2.resize(cv2.cvtColor(crop_a, cv2.COLOR_BGR2GRAY), (100, 100))
        
        pixel_diff = np.mean(cv2.absdiff(crop_s_resize, crop_a_resize))
        diff_left = np.mean(cv2.absdiff(crop_s_resize[:, :50], crop_a_resize[:, :50]))
        diff_right = np.mean(cv2.absdiff(crop_s_resize[:, 50:], crop_a_resize[:, 50:]))
        
        # Horizontal box center displacement
        center_s = bbox_s[0] + bbox_s[2] / 2
        center_a = bbox_a[0] + bbox_a[2] / 2
        shift = center_a - center_s
        center_diff = abs(shift)

        # Unified Rotation Score Heuristic:
        # Bbox Shift (supporting) + Asymmetry (supporting)
        # Left turn (user turns left) shifts sensor face right (shift > 0) and right side changes more (diff_right > diff_left)
        # Right turn (user turns right) shifts sensor face left (shift < 0) and left side changes more (diff_left > diff_right)
        rotation_score = (shift * 0.5) + (diff_right - diff_left) * 2.0

        # Diagnostics Logging
        logger.info(f"DIAGNOSTIC LOG - Challenge: {target_direction} | Face Count: 1 | Quality Score: {blur_score:.2f}")
        logger.info(f"DIAGNOSTIC LOG - Bbox Straight: {bbox_s} | Bbox Action: {bbox_a}")
        logger.info(f"DIAGNOSTIC LOG - Centroid Straight: {center_s:.1f} | Centroid Action: {center_a:.1f} | Shift: {shift:.2f}")
        logger.info(f"DIAGNOSTIC LOG - Total MAD: {pixel_diff:.2f} | MAD Left: {diff_left:.2f} | MAD Right: {diff_right:.2f} | Score: {rotation_score:.2f}")

        # Criteria matching:
        # 1. Bbox consistency (must stay within 80px to guarantee same region)
        # 2. Total temporal image change must be >= 3.0 to reject static spoof
        # 3. Liveness rotation score must match target challenge direction
        is_same_region = center_diff <= 80.0
        is_not_static = pixel_diff >= 3.0
        
        if not is_same_region:
            liveness_status = "FAILED"
            reason = "Face moved too far out of frame."
        elif not is_not_static:
            liveness_status = "MANUAL_REVIEW"
            reason = "No movement detected between frames."
        else:
            if target_direction == "LEFT":
                if rotation_score >= 1.5:
                    liveness_status = "PASSED"
                    reason = "One clear face detected and requested live movement completed."
                elif rotation_score <= -1.5:
                    liveness_status = "FAILED"
                    reason = "Unexpected movement detected. Please follow the requested direction."
                else:
                    liveness_status = "FAILED"
                    reason = "Insufficient head movement detected. Please turn your head slightly LEFT and try again."
            else:  # RIGHT
                if rotation_score <= -1.5:
                    liveness_status = "PASSED"
                    reason = "One clear face detected and requested live movement completed."
                elif rotation_score >= 1.5:
                    liveness_status = "FAILED"
                    reason = "Unexpected movement detected. Please follow the requested direction."
                else:
                    liveness_status = "FAILED"
                    reason = "Insufficient head movement detected. Please turn your head slightly RIGHT and try again."

        return {
            "face_detected": True,
            "face_count": 1,
            "face_quality": "GOOD",
            "image_width": int(w_s),
            "image_height": int(h_s),
            "face_width": int(bbox_s[2]),
            "face_height": int(bbox_s[3]),
            "liveness_status": liveness_status,
            "liveness_method": "HEAD_TURN",
            "suitable_for_matching": bool(liveness_status == "PASSED"),
            "reason": reason,
            "total_mad": float(pixel_diff),
            "left_mad": float(diff_left),
            "right_mad": float(diff_right),
            "center_shift": float(shift),
            "detected_direction": "LEFT" if rotation_score > 0 else "RIGHT" if rotation_score < 0 else "NONE",
            "requested_direction": target_direction,
            "quality_score": float(blur_score)
        }
