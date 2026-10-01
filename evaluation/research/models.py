"""
Research Recommender Model Implementations.
Implements the 5 ablation configurations:
- Model A: Legacy Baseline
- Model B: Dense Semantic Only
- Model C: Topic Overlap Only
- Model D: Full Hybrid Matcher (Production Formula)
- Model E: Full Hybrid + Bayesian Feedback (Research Experiment)
"""
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure project root and ai-service are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AI_SERVICE_DIR = BASE_DIR / "ai-service"
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.matching.embeddings import EmbeddingService, get_embedding_service
from app.matching.taxonomy import evaluate_subject_gate
from app.matching.scoring import (
    calculate_location_score,
    calculate_fee_score,
    calculate_time_score,
    calculate_topic_overlap,
    calculate_learning_need_score,
    calculate_composite_score,
)
from app.matching.matcher import build_student_semantic_text, build_tutor_semantic_text
from backend.app.services.feedback_score import calculate_feedback_signal
from evaluation.research.config import (
    MODEL_LEGACY_BASELINE,
    MODEL_DENSE_SEMANTIC,
    MODEL_TOPIC_OVERLAP,
    MODEL_FULL_HYBRID,
    MODEL_FULL_HYBRID_FEEDBACK,
    DEFAULT_FEEDBACK_WEIGHT,
    DEFAULT_SMOOTHING_M,
    DEFAULT_GLOBAL_PRIOR,
)


class ResearchModelsEvaluator:
    """Evaluates candidates across all 5 benchmark model configurations."""

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or get_embedding_service()

    def run_legacy_baseline(
        self, query: Dict[str, Any], candidate_tutors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Configuration A: Legacy Baseline
        - Stage 1: Strict Subject Gate
        - Passing candidates receive subject_score = 1.0
        - Score: 0.40 * 1.0 + 0.20 * location + 0.20 * fee + 0.20 * time
        - NO dense semantic embeddings, NO topic overlap.
        """
        subject_needed = str(query.get("subjects_needed") or query.get("subject", "")).strip()
        student_lat = float(query.get("latitude", 13.0827))
        student_lon = float(query.get("longitude", 80.2707))
        budget_min = float(query.get("budget_min", 300.0))
        budget_max = float(query.get("budget_max", 1000.0))
        preferred_slots = query.get("preferred_slots", [])

        ranked = []
        for tutor in candidate_tutors:
            if tutor.get("is_verified") is False:
                continue

            tutor_subjects = tutor.get("subjects") or tutor.get("subjects_taught") or []
            is_eligible, _ = evaluate_subject_gate(subject_needed, tutor_subjects, self.embedding_service)
            if not is_eligible:
                continue

            # Fixed historical subject score = 1.0
            subject_score = 1.0

            t_lat = float(tutor.get("latitude", 0.0))
            t_lon = float(tutor.get("longitude", 0.0))
            loc_score, _ = calculate_location_score(student_lat, student_lon, t_lat, t_lon)

            rate = float(tutor.get("hourly_rate", 0.0))
            fee_sc = calculate_fee_score(rate, budget_min, budget_max)

            availability = tutor.get("availability", [])
            time_sc = calculate_time_score(preferred_slots, availability)

            # Historical baseline composite formula: 0.40 subject (1.0) + 0.20 loc + 0.20 fee + 0.20 time
            overall = (
                (0.40 * subject_score)
                + (0.20 * loc_score)
                + (0.20 * fee_sc)
                + (0.20 * time_sc)
            )

            ranked.append({
                "id": tutor.get("tutor_id") or tutor.get("id"),
                "name": tutor.get("name"),
                "overall_score": float(overall),
                "learning_need_score": 1.0,
                "location_score": loc_score,
                "fee_score": fee_sc,
                "time_score": time_sc,
                "rating": float(tutor.get("rating") or 4.5),
                "model_configuration": MODEL_LEGACY_BASELINE,
            })

        ranked.sort(key=lambda x: (round(x["overall_score"], 6), round(x["rating"], 2), x["id"]), reverse=True)
        return ranked

    def run_dense_semantic(
        self, query: Dict[str, Any], candidate_tutors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Configuration B: Dense Semantic Only
        - Stage 1: Strict Subject Gate
        - Score: 0.45 * semantic_score + 0.20 * location + 0.20 * fee + 0.15 * time
        - NO topic overlap.
        """
        subject_needed = str(query.get("subjects_needed") or query.get("subject", "")).strip()
        student_lat = float(query.get("latitude", 13.0827))
        student_lon = float(query.get("longitude", 80.2707))
        budget_min = float(query.get("budget_min", 300.0))
        budget_max = float(query.get("budget_max", 1000.0))
        preferred_slots = query.get("preferred_slots", [])

        # Stage 1 Gate
        qualified = []
        for tutor in candidate_tutors:
            if tutor.get("is_verified") is False:
                continue
            t_subs = tutor.get("subjects") or tutor.get("subjects_taught") or []
            is_eligible, _ = evaluate_subject_gate(subject_needed, t_subs, self.embedding_service)
            if is_eligible:
                qualified.append(tutor)

        if not qualified:
            return []

        # Encode query text
        s_text = build_student_semantic_text(query)
        s_emb = self.embedding_service.encode([s_text])

        # Encode tutor capability texts
        t_texts = [
            build_tutor_semantic_text(t, t.get("subjects") or t.get("subjects_taught") or [])
            for t in qualified
        ]
        t_embs = self.embedding_service.encode(t_texts)
        sims = self.embedding_service.compute_similarity(s_emb, t_embs)

        ranked = []
        for i, tutor in enumerate(qualified):
            sem_score = float(sims[i])
            t_lat = float(tutor.get("latitude", 0.0))
            t_lon = float(tutor.get("longitude", 0.0))
            loc_score, _ = calculate_location_score(student_lat, student_lon, t_lat, t_lon)
            rate = float(tutor.get("hourly_rate", 0.0))
            fee_sc = calculate_fee_score(rate, budget_min, budget_max)
            time_sc = calculate_time_score(preferred_slots, tutor.get("availability", []))

            overall = (
                (0.45 * sem_score)
                + (0.20 * loc_score)
                + (0.20 * fee_sc)
                + (0.15 * time_sc)
            )

            ranked.append({
                "id": tutor.get("tutor_id") or tutor.get("id"),
                "name": tutor.get("name"),
                "overall_score": float(overall),
                "learning_need_score": sem_score,
                "semantic_score": sem_score,
                "topic_score": 0.0,
                "location_score": loc_score,
                "fee_score": fee_sc,
                "time_score": time_sc,
                "rating": float(tutor.get("rating") or 4.5),
                "model_configuration": MODEL_DENSE_SEMANTIC,
            })

        ranked.sort(key=lambda x: (round(x["overall_score"], 6), round(x["rating"], 2), x["id"]), reverse=True)
        return ranked

    def run_topic_overlap(
        self, query: Dict[str, Any], candidate_tutors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Configuration C: Topic Overlap Only
        - Stage 1: Strict Subject Gate
        - Score: 0.45 * topic_score + 0.20 * location + 0.20 * fee + 0.15 * time
        - NO dense semantic embeddings.
        """
        subject_needed = str(query.get("subjects_needed") or query.get("subject", "")).strip()
        student_lat = float(query.get("latitude", 13.0827))
        student_lon = float(query.get("longitude", 80.2707))
        budget_min = float(query.get("budget_min", 300.0))
        budget_max = float(query.get("budget_max", 1000.0))
        preferred_slots = query.get("preferred_slots", [])
        student_topics = query.get("topics") or []

        ranked = []
        for tutor in candidate_tutors:
            if tutor.get("is_verified") is False:
                continue
            t_subs = tutor.get("subjects") or tutor.get("subjects_taught") or []
            is_eligible, _ = evaluate_subject_gate(subject_needed, t_subs, self.embedding_service)
            if not is_eligible:
                continue

            t_topics = tutor.get("topics_expertise") or []
            combined_t_topics = list(set(t_topics + t_subs))
            topic_score, _ = calculate_topic_overlap(student_topics, combined_t_topics)

            t_lat = float(tutor.get("latitude", 0.0))
            t_lon = float(tutor.get("longitude", 0.0))
            loc_score, _ = calculate_location_score(student_lat, student_lon, t_lat, t_lon)
            rate = float(tutor.get("hourly_rate", 0.0))
            fee_sc = calculate_fee_score(rate, budget_min, budget_max)
            time_sc = calculate_time_score(preferred_slots, tutor.get("availability", []))

            overall = (
                (0.45 * topic_score)
                + (0.20 * loc_score)
                + (0.20 * fee_sc)
                + (0.15 * time_sc)
            )

            ranked.append({
                "id": tutor.get("tutor_id") or tutor.get("id"),
                "name": tutor.get("name"),
                "overall_score": float(overall),
                "learning_need_score": topic_score,
                "semantic_score": 0.0,
                "topic_score": topic_score,
                "location_score": loc_score,
                "fee_score": fee_sc,
                "time_score": time_sc,
                "rating": float(tutor.get("rating") or 4.5),
                "model_configuration": MODEL_TOPIC_OVERLAP,
            })

        ranked.sort(key=lambda x: (round(x["overall_score"], 6), round(x["rating"], 2), x["id"]), reverse=True)
        return ranked

    def run_full_hybrid(
        self, query: Dict[str, Any], candidate_tutors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Configuration D: Full Hybrid Matcher (Production Step 3C Formulation)
        - Stage 1: Strict Subject Gate
        - learning_need_score = 0.60 * semantic_score + 0.40 * topic_score (or 1.0 * semantic_score if no topics)
        - Score: 0.45 * learning_need_score + 0.20 * location + 0.20 * fee + 0.15 * time
        """
        subject_needed = str(query.get("subjects_needed") or query.get("subject", "")).strip()
        student_lat = float(query.get("latitude", 13.0827))
        student_lon = float(query.get("longitude", 80.2707))
        budget_min = float(query.get("budget_min", 300.0))
        budget_max = float(query.get("budget_max", 1000.0))
        preferred_slots = query.get("preferred_slots", [])
        student_topics = query.get("topics") or []

        qualified = []
        for tutor in candidate_tutors:
            if tutor.get("is_verified") is False:
                continue
            t_subs = tutor.get("subjects") or tutor.get("subjects_taught") or []
            is_eligible, _ = evaluate_subject_gate(subject_needed, t_subs, self.embedding_service)
            if is_eligible:
                qualified.append(tutor)

        if not qualified:
            return []

        s_text = build_student_semantic_text(query)
        s_emb = self.embedding_service.encode([s_text])

        t_texts = [
            build_tutor_semantic_text(t, t.get("subjects") or t.get("subjects_taught") or [])
            for t in qualified
        ]
        t_embs = self.embedding_service.encode(t_texts)
        sims = self.embedding_service.compute_similarity(s_emb, t_embs)

        ranked = []
        for i, tutor in enumerate(qualified):
            sem_score = float(sims[i])
            t_subs = tutor.get("subjects") or tutor.get("subjects_taught") or []
            t_topics = tutor.get("topics_expertise") or []
            combined_t_topics = list(set(t_topics + t_subs))
            topic_score, _ = calculate_topic_overlap(student_topics, combined_t_topics)

            has_topics = bool(student_topics)
            ln_score = calculate_learning_need_score(sem_score, topic_score, has_topics)

            t_lat = float(tutor.get("latitude", 0.0))
            t_lon = float(tutor.get("longitude", 0.0))
            loc_score, _ = calculate_location_score(student_lat, student_lon, t_lat, t_lon)
            rate = float(tutor.get("hourly_rate", 0.0))
            fee_sc = calculate_fee_score(rate, budget_min, budget_max)
            time_sc = calculate_time_score(preferred_slots, tutor.get("availability", []))

            overall = (
                (0.45 * ln_score)
                + (0.20 * loc_score)
                + (0.20 * fee_sc)
                + (0.15 * time_sc)
            )

            ranked.append({
                "id": tutor.get("tutor_id") or tutor.get("id"),
                "name": tutor.get("name"),
                "overall_score": float(overall),
                "learning_need_score": ln_score,
                "semantic_score": sem_score,
                "topic_score": topic_score,
                "location_score": loc_score,
                "fee_score": fee_sc,
                "time_score": time_sc,
                "rating": float(tutor.get("rating") or 4.5),
                "model_configuration": MODEL_FULL_HYBRID,
            })

        ranked.sort(key=lambda x: (round(x["overall_score"], 6), round(x["rating"], 2), x["id"]), reverse=True)
        return ranked

    def run_full_hybrid_feedback(
        self,
        query: Dict[str, Any],
        candidate_tutors: List[Dict[str, Any]],
        feedback_weight: float = DEFAULT_FEEDBACK_WEIGHT,
        smoothing_m: float = DEFAULT_SMOOTHING_M,
        global_prior: float = DEFAULT_GLOBAL_PRIOR,
    ) -> List[Dict[str, Any]]:
        """
        Configuration E: Full Hybrid + Feedback Signal (Offline Research Experiment)
        - Base Hybrid Score (Configuration D)
        - Bayesian feedback signal calculated via calculate_feedback_signal()
        - Experimental Composite: (1 - feedback_weight) * base_score + feedback_weight * feedback_score
        """
        hybrid_results = self.run_full_hybrid(query, candidate_tutors)
        tutor_map = {t.get("tutor_id") or t.get("id"): t for t in candidate_tutors}

        ranked = []
        for item in hybrid_results:
            tid = item["id"]
            tutor_profile = tutor_map.get(tid, {})
            t_rating = tutor_profile.get("rating")
            t_rev_count = tutor_profile.get("review_count", 0)

            fb_sig = calculate_feedback_signal(
                average_rating=t_rating,
                review_count=t_rev_count,
                smoothing_m=smoothing_m,
                global_prior=global_prior,
            )
            feedback_score = fb_sig["feedback_score"]
            base_overall = item["overall_score"]

            w_fb = max(0.0, min(1.0, float(feedback_weight)))
            experimental_overall = ((1.0 - w_fb) * base_overall) + (w_fb * feedback_score)

            item_copy = dict(item)
            item_copy["hybrid_base_score"] = base_overall
            item_copy["overall_score"] = float(experimental_overall)
            item_copy["feedback_score"] = feedback_score
            item_copy["adjusted_rating"] = fb_sig["adjusted_rating"]
            item_copy["feedback_confidence"] = fb_sig["confidence"]
            item_copy["feedback_weight"] = w_fb
            item_copy["model_configuration"] = MODEL_FULL_HYBRID_FEEDBACK
            ranked.append(item_copy)

        ranked.sort(key=lambda x: (round(x["overall_score"], 6), round(x["rating"], 2), x["id"]), reverse=True)
        return ranked

    def evaluate_model(
        self,
        model_name: str,
        query: Dict[str, Any],
        candidate_tutors: List[Dict[str, Any]],
        feedback_weight: float = DEFAULT_FEEDBACK_WEIGHT,
        smoothing_m: float = DEFAULT_SMOOTHING_M,
        global_prior: float = DEFAULT_GLOBAL_PRIOR,
    ) -> List[Dict[str, Any]]:
        """Dispatch evaluator by model name string."""
        if model_name == MODEL_LEGACY_BASELINE:
            return self.run_legacy_baseline(query, candidate_tutors)
        elif model_name == MODEL_DENSE_SEMANTIC:
            return self.run_dense_semantic(query, candidate_tutors)
        elif model_name == MODEL_TOPIC_OVERLAP:
            return self.run_topic_overlap(query, candidate_tutors)
        elif model_name == MODEL_FULL_HYBRID:
            return self.run_full_hybrid(query, candidate_tutors)
        elif model_name == MODEL_FULL_HYBRID_FEEDBACK:
            return self.run_full_hybrid_feedback(
                query, candidate_tutors, feedback_weight, smoothing_m, global_prior
            )
        else:
            raise ValueError(f"Unknown model configuration: '{model_name}'")
