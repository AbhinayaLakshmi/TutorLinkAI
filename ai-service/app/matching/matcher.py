"""
TutorMatcher: Coordinates two-stage matching pipeline:
- Stage 1: Subject Eligibility Gate (Pass/Fail via taxonomy and explicit subject tags)
- Stage 2: Multi-criteria Ranking (Location, Fee, Time, and Subject refinement among qualified candidates)
"""
from typing import List, Dict, Any, Optional
import json
import numpy as np
from .config import (
    DEFAULT_WEIGHT_SUBJECT,
    DEFAULT_WEIGHT_LOCATION,
    DEFAULT_WEIGHT_FEE,
    DEFAULT_WEIGHT_TIME,
    DEFAULT_MAX_RADIUS_KM,
    DEFAULT_FEE_TOLERANCE_RATIO,
    MIN_OVERALL_SCORE_THRESHOLD,
    SUBJECT_GATE_SIMILARITY_THRESHOLD,
)
from .embeddings import get_embedding_service, EmbeddingService
from .taxonomy import evaluate_subject_gate
from .scoring import (
    calculate_location_score,
    calculate_fee_score,
    calculate_time_score,
    calculate_composite_score,
    normalize_scores_minmax,
)


class TutorMatcher:
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or get_embedding_service()

    def rank_tutors(
        self,
        student_query: Dict[str, Any],
        candidate_tutors: List[Dict[str, Any]],
        weight_subject: float = DEFAULT_WEIGHT_SUBJECT,
        weight_location: float = DEFAULT_WEIGHT_LOCATION,
        weight_fee: float = DEFAULT_WEIGHT_FEE,
        weight_time: float = DEFAULT_WEIGHT_TIME,
        max_radius_km: float = DEFAULT_MAX_RADIUS_KM,
        fee_tolerance_ratio: float = DEFAULT_FEE_TOLERANCE_RATIO,
        min_threshold: float = MIN_OVERALL_SCORE_THRESHOLD,
        use_minmax_normalization: bool = False,
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Two-stage matching pipeline:
        Stage 1: Subject Eligibility Gate (Pass / Fail)
        Stage 2: Ranking among qualified tutors (Location, Fee, Time, Subject scores)
        """
        if not candidate_tutors:
            return []

        subjects_needed = str(student_query.get("subjects_needed", "")).strip()
        if not subjects_needed:
            return []

        student_lat = float(student_query.get("latitude", 13.0827))
        student_lon = float(student_query.get("longitude", 80.2707))
        budget_min = float(student_query.get("budget_min", 300.0))
        budget_max = float(student_query.get("budget_max", 1000.0))
        preferred_slots = student_query.get("preferred_slots", [])

        # =========================================================================
        # Stage 1: Subject Eligibility Gate (Pass / Fail)
        # =========================================================================
        stage1_qualified = []

        for tutor in candidate_tutors:
            raw_subjects = tutor.get("subjects", [])
            if isinstance(raw_subjects, str):
                try:
                    tutor_subjects_list = json.loads(raw_subjects)
                except Exception:
                    tutor_subjects_list = [s.strip() for s in raw_subjects.split(",") if s.strip()]
            elif isinstance(raw_subjects, list):
                tutor_subjects_list = raw_subjects
            else:
                tutor_subjects_list = []

            # Evaluate subject gate strictly on explicit subject tags & taxonomy
            is_eligible, base_subject_score = evaluate_subject_gate(
                requested_subject=subjects_needed,
                tutor_subjects=tutor_subjects_list,
                embedding_service=self.embedding_service,
                similarity_threshold=SUBJECT_GATE_SIMILARITY_THRESHOLD,
            )

            # Tutors who fail Stage 1 are completely excluded from recommendations
            if is_eligible:
                stage1_qualified.append(
                    {
                        "tutor": tutor,
                        "tutor_subjects_list": tutor_subjects_list,
                        "subject_score": max(0.5, float(base_subject_score)),
                    }
                )

        # If zero tutors passed Stage 1, return empty results (never backfill off-subject tutors)
        if not stage1_qualified:
            return []

        # =========================================================================
        # Stage 2: Ranking Among Subject-Qualified Candidates
        # =========================================================================
        raw_results = []
        sub_scores_list = []

        for item in stage1_qualified:
            tutor = item["tutor"]
            subj_score = item["subject_score"]

            tutor_lat = float(tutor.get("latitude", 0.0))
            tutor_lon = float(tutor.get("longitude", 0.0))
            loc_score, distance_km = calculate_location_score(
                student_lat, student_lon, tutor_lat, tutor_lon, max_radius_km
            )

            hourly_rate = float(tutor.get("hourly_rate", 0.0))
            fee_sc = calculate_fee_score(
                hourly_rate, budget_min, budget_max, fee_tolerance_ratio
            )

            availability = tutor.get("availability", [])
            if not isinstance(availability, list):
                availability = []
            time_sc = calculate_time_score(preferred_slots, availability)

            sub_scores_list.append([subj_score, loc_score, fee_sc, time_sc])

            raw_results.append(
                {
                    "tutor": tutor,
                    "tutor_subjects_list": item["tutor_subjects_list"],
                    "distance_km": distance_km,
                    "subject_score": round(subj_score, 4),
                    "location_score": round(loc_score, 4),
                    "fee_score": round(fee_sc, 4),
                    "time_score": round(time_sc, 4),
                }
            )

        # Optional MinMaxScaler normalization across qualified candidates
        sub_scores_mat = np.array(sub_scores_list, dtype=float)
        if use_minmax_normalization and len(stage1_qualified) > 1:
            norm_matrix = normalize_scores_minmax(sub_scores_mat)
        else:
            norm_matrix = sub_scores_mat

        # Calculate composite score for each qualified candidate
        ranked_tutors = []
        for i, item in enumerate(raw_results):
            s_subj, s_loc, s_fee, s_time = norm_matrix[i]
            overall = calculate_composite_score(
                subject_score=float(s_subj),
                location_score=float(s_loc),
                fee_score=float(s_fee),
                time_score=float(s_time),
                weight_subject=weight_subject,
                weight_location=weight_location,
                weight_fee=weight_fee,
                weight_time=weight_time,
            )

            if overall >= min_threshold:
                tutor_data = item["tutor"]
                ranked_tutors.append(
                    {
                        "id": tutor_data.get("id"),
                        "user_id": tutor_data.get("user_id"),
                        "name": tutor_data.get("name"),
                        "subjects": item["tutor_subjects_list"],
                        "bio": tutor_data.get("bio"),
                        "hourly_rate": float(tutor_data.get("hourly_rate", 0.0)),
                        "latitude": float(tutor_data.get("latitude", 0.0)),
                        "longitude": float(tutor_data.get("longitude", 0.0)),
                        "area_name": tutor_data.get("area_name"),
                        "availability": tutor_data.get("availability", []),
                        "rating": float(tutor_data.get("rating", 4.5))
                        if tutor_data.get("rating") is not None
                        else 4.5,
                        "overall_score": round(overall, 4),
                        "overall_percentage": int(round(overall * 100)),
                        "breakdown": {
                            "subject_score": item["subject_score"],
                            "location_score": item["location_score"],
                            "fee_score": item["fee_score"],
                            "time_score": item["time_score"],
                            "distance_km": item["distance_km"],
                        },
                    }
                )

        # Sort descending by overall_score, tie-breaking by rating
        ranked_tutors.sort(
            key=lambda x: (x["overall_score"], x.get("rating", 0.0)),
            reverse=True,
        )

        return ranked_tutors[:top_n]
