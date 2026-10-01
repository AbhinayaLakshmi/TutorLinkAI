"""
TutorMatcher: Coordinates two-stage matching pipeline:
- Stage 1: Subject Eligibility Gate (Pass/Fail via taxonomy and explicit subject tags)
- Stage 2: Multi-criteria Semantic Learning-Need Ranking & Explainability
  (Dense S-BERT semantic similarity, deterministic topic overlap, pedagogy compatibility,
  location, fee, and time score fusion)
"""
from typing import List, Dict, Any, Optional, Tuple
import json
import numpy as np
from .config import (
    DEFAULT_WEIGHT_LEARNING_NEED,
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
    calculate_topic_overlap,
    calculate_learning_need_score,
    calculate_composite_score,
    normalize_scores_minmax,
)


def build_student_semantic_text(query: Dict[str, Any]) -> str:
    """
    Constructs a deterministic, structured textual representation of the student's learning need.
    Uses deterministic templates (no generative LLM).
    """
    lines = []

    # Subject
    subj = str(query.get("subjects_needed", "")).strip()
    if subj:
        lines.append(f"Subject: {subj}.")

    # Topics needed
    topics = query.get("topics") or query.get("topics_needed") or []
    if isinstance(topics, str):
        try:
            topics = json.loads(topics)
        except Exception:
            topics = [t.strip() for t in topics.split(",") if t.strip()]
    if isinstance(topics, list) and topics:
        lines.append(f"Topics needed: {', '.join(str(t) for t in topics)}.")

    # Learning goals
    goals = str(query.get("learning_goals") or "").strip()
    if goals:
        lines.append(f"Learning goals: {goals}.")

    # Student level
    level = str(query.get("student_level") or "").strip()
    if level:
        lines.append(f"Student level: {level}.")

    # Preferred tutor characteristics / style
    pref_style = str(
        query.get("preferred_tutor_characteristics")
        or query.get("preferred_style")
        or ""
    ).strip()
    if pref_style:
        lines.append(f"Preferred tutor characteristics: {pref_style}.")

    # Preferred learning mode
    mode = str(
        query.get("preferred_learning_mode") or query.get("preferred_mode") or ""
    ).strip()
    if mode:
        lines.append(f"Preferred learning mode: {mode}.")

    # Preferred languages
    langs = query.get("preferred_tutor_languages") or query.get("languages") or []
    if isinstance(langs, str):
        try:
            langs = json.loads(langs)
        except Exception:
            langs = [l.strip() for l in langs.split(",") if l.strip()]
    if isinstance(langs, list) and langs:
        lines.append(f"Languages: {', '.join(str(l) for l in langs)}.")

    return "\n".join(lines) if lines else (subj or "General Learning Need")


def build_tutor_semantic_text(
    tutor: Dict[str, Any], tutor_subjects_list: List[str]
) -> str:
    """
    Constructs a deterministic, structured textual representation of the tutor's capabilities.
    Uses deterministic templates (no generative LLM).
    """
    lines = []

    # Subjects taught
    if tutor_subjects_list:
        lines.append(f"Subjects taught: {', '.join(tutor_subjects_list)}.")

    # Topics expertise
    topics_exp = tutor.get("topics_expertise") or []
    if isinstance(topics_exp, str):
        try:
            topics_exp = json.loads(topics_exp)
        except Exception:
            topics_exp = [t.strip() for t in topics_exp.split(",") if t.strip()]
    if isinstance(topics_exp, list) and topics_exp:
        lines.append(f"Topics expertise: {', '.join(str(t) for t in topics_exp)}.")

    # Skills / pedagogy
    skills = tutor.get("skills") or []
    if isinstance(skills, str):
        try:
            skills = json.loads(skills)
        except Exception:
            skills = [s.strip() for s in skills.split(",") if s.strip()]
    if isinstance(skills, list) and skills:
        lines.append(f"Skills: {', '.join(str(s) for s in skills)}.")

    # Student levels
    levels = tutor.get("student_levels") or []
    if isinstance(levels, str):
        try:
            levels = json.loads(levels)
        except Exception:
            levels = [l.strip() for l in levels.split(",") if l.strip()]
    if isinstance(levels, list) and levels:
        lines.append(f"Student levels: {', '.join(str(l) for l in levels)}.")

    # Teaching mode
    mode = str(
        tutor.get("preferred_teaching_mode") or tutor.get("teaching_mode") or ""
    ).strip()
    if mode:
        lines.append(f"Teaching mode: {mode}.")

    # Languages
    langs = tutor.get("languages_can_teach_in") or tutor.get("languages") or []
    if isinstance(langs, str):
        try:
            langs = json.loads(langs)
        except Exception:
            langs = [l.strip() for l in langs.split(",") if l.strip()]
    if isinstance(langs, list) and langs:
        lines.append(f"Languages: {', '.join(str(l) for l in langs)}.")

    return (
        "\n".join(lines)
        if lines
        else (", ".join(tutor_subjects_list) or "Tutor Capability")
    )


def calculate_pedagogy_compatibility(
    student_style: Optional[str],
    tutor_skills: Optional[List[str]],
    embedding_service: EmbeddingService,
) -> Optional[float]:
    """
    Calculates specific pedagogy / teaching-style compatibility score ONLY when both
    student and tutor provide relevant pedagogical / learning-style information.
    Returns None if sufficient evidence is not available on both sides.
    """
    s_style = (student_style or "").strip()
    if not s_style:
        return None

    t_skills_list = tutor_skills or []
    if isinstance(t_skills_list, str):
        try:
            t_skills_list = json.loads(t_skills_list)
        except Exception:
            t_skills_list = [s.strip() for s in t_skills_list.split(",") if s.strip()]

    if not isinstance(t_skills_list, list) or not t_skills_list:
        return None

    t_skills_text = ", ".join(str(s) for s in t_skills_list if str(s).strip())
    if not t_skills_text:
        return None

    # Compute cosine similarity between student's desired teaching characteristics and tutor's pedagogical skills
    emb_s = embedding_service.encode([s_style])
    emb_t = embedding_service.encode([t_skills_text])
    ped_sim = float(embedding_service.compute_similarity(emb_s, emb_t)[0])

    return float(round(np.clip(ped_sim, 0.0, 1.0), 4))


class TutorMatcher:
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or get_embedding_service()

    def rank_tutors(
        self,
        student_query: Dict[str, Any],
        candidate_tutors: List[Dict[str, Any]],
        weight_learning_need: float = DEFAULT_WEIGHT_LEARNING_NEED,
        weight_subject: Optional[float] = None,
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
        Stage 1: Subject Eligibility Gate (Pass / Fail) & Verified Tutor Filtering
        Stage 2: Semantic Learning-Need Ranking & Explainable Recommendations
        """
        if not candidate_tutors:
            return []

        subjects_needed = str(student_query.get("subjects_needed", "")).strip()
        if not subjects_needed:
            return []

        # Parse student parameters
        student_lat = float(student_query.get("latitude", 13.0827))
        student_lon = float(student_query.get("longitude", 80.2707))
        budget_min = float(student_query.get("budget_min", 300.0))
        budget_max = float(student_query.get("budget_max", 1000.0))
        preferred_slots = student_query.get("preferred_slots", [])

        # Parse student topic requirements
        raw_student_topics = (
            student_query.get("topics") or student_query.get("topics_needed") or []
        )
        if isinstance(raw_student_topics, str):
            try:
                student_topics = json.loads(raw_student_topics)
            except Exception:
                student_topics = [
                    t.strip() for t in raw_student_topics.split(",") if t.strip()
                ]
        elif isinstance(raw_student_topics, list):
            student_topics = [str(t).strip() for t in raw_student_topics if str(t).strip()]
        else:
            student_topics = []

        learning_goals = str(student_query.get("learning_goals") or "").strip()
        student_level = str(student_query.get("student_level") or "").strip()
        pref_tutor_style = str(
            student_query.get("preferred_tutor_characteristics")
            or student_query.get("preferred_style")
            or ""
        ).strip()
        pref_learning_mode = str(
            student_query.get("preferred_learning_mode")
            or student_query.get("preferred_mode")
            or ""
        ).strip()

        raw_student_langs = (
            student_query.get("preferred_tutor_languages")
            or student_query.get("languages")
            or []
        )
        if isinstance(raw_student_langs, str):
            try:
                student_langs = json.loads(raw_student_langs)
            except Exception:
                student_langs = [
                    l.strip() for l in raw_student_langs.split(",") if l.strip()
                ]
        elif isinstance(raw_student_langs, list):
            student_langs = [str(l).strip() for l in raw_student_langs if str(l).strip()]
        else:
            student_langs = []

        # =========================================================================
        # Stage 1: Subject Eligibility Gate (Pass / Fail) & Verified Tutor Filtering
        # =========================================================================
        stage1_qualified = []

        for tutor in candidate_tutors:
            # Verified filter check (if explicitly set to False, tutor is excluded)
            if tutor.get("is_verified") is False:
                continue

            raw_subjects = tutor.get("subjects", [])
            if isinstance(raw_subjects, str):
                try:
                    tutor_subjects_list = json.loads(raw_subjects)
                except Exception:
                    tutor_subjects_list = [
                        s.strip() for s in raw_subjects.split(",") if s.strip()
                    ]
            elif isinstance(raw_subjects, list):
                tutor_subjects_list = [str(s).strip() for s in raw_subjects if str(s).strip()]
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
                        "base_subject_score": max(0.5, float(base_subject_score)),
                    }
                )

        # If zero tutors passed Stage 1, return empty results (never backfill off-subject tutors)
        if not stage1_qualified:
            return []

        # =========================================================================
        # Stage 2: Semantic Learning-Need Ranking & Explainability Generation
        # =========================================================================
        # 1. Build deterministic student representation and encode embedding
        student_semantic_text = build_student_semantic_text(student_query)
        student_embedding = self.embedding_service.encode([student_semantic_text])

        # 2. Build deterministic tutor representations and batch encode
        tutor_semantic_texts = [
            build_tutor_semantic_text(item["tutor"], item["tutor_subjects_list"])
            for item in stage1_qualified
        ]
        tutor_embeddings = self.embedding_service.encode(tutor_semantic_texts)

        # 3. Dense cosine similarities
        semantic_sims = self.embedding_service.compute_similarity(
            student_embedding, tutor_embeddings
        )

        raw_results = []
        sub_scores_list = []

        for i, item in enumerate(stage1_qualified):
            tutor = item["tutor"]
            tutor_subjects_list = item["tutor_subjects_list"]
            semantic_score = float(semantic_sims[i])

            # Extract tutor topics & skills
            raw_t_topics = tutor.get("topics_expertise") or []
            if isinstance(raw_t_topics, str):
                try:
                    t_topics = json.loads(raw_t_topics)
                except Exception:
                    t_topics = [t.strip() for t in raw_t_topics.split(",") if t.strip()]
            elif isinstance(raw_t_topics, list):
                t_topics = [str(t).strip() for t in raw_t_topics if str(t).strip()]
            else:
                t_topics = []

            # Include subject list in topic pool for comprehensive overlap
            combined_tutor_topics = list(set(t_topics + tutor_subjects_list))

            # Deterministic topic overlap
            topic_score, matched_topics = calculate_topic_overlap(
                student_topics=student_topics,
                tutor_topics=combined_tutor_topics,
            )

            # Heuristic research-prototype score fusion for learning need
            has_student_topics = bool(student_topics)
            learning_need_score = calculate_learning_need_score(
                semantic_score=semantic_score,
                topic_score=topic_score,
                has_topics=has_student_topics,
            )

            # Location Proximity Score
            tutor_lat = float(tutor.get("latitude", 0.0))
            tutor_lon = float(tutor.get("longitude", 0.0))
            loc_score, distance_km = calculate_location_score(
                student_lat, student_lon, tutor_lat, tutor_lon, max_radius_km
            )

            # Fee Budget Score
            hourly_rate = float(tutor.get("hourly_rate", 0.0))
            fee_sc = calculate_fee_score(
                hourly_rate, budget_min, budget_max, fee_tolerance_ratio
            )

            # Time Availability Score
            availability = tutor.get("availability", [])
            if not isinstance(availability, list):
                availability = []
            time_sc = calculate_time_score(preferred_slots, availability)

            # Pedagogy Compatibility (Computed ONLY when both sides provide pedagogical data)
            tutor_skills = tutor.get("skills")
            pedagogy_compat = calculate_pedagogy_compatibility(
                student_style=pref_tutor_style,
                tutor_skills=tutor_skills,
                embedding_service=self.embedding_service,
            )

            # =====================================================================
            # Evidence-Grounded Match Reasons Generation
            # =====================================================================
            match_reasons: List[str] = []

            # 1. Topic overlap reason (only if topic matching found evidence)
            if matched_topics:
                if len(matched_topics) == 1:
                    match_reasons.append(f"Strong topic match for {matched_topics[0]}")
                else:
                    match_reasons.append(
                        f"Strong topic match for {', '.join(matched_topics[:3])}"
                    )

            # 2. Semantic alignment & learning goals
            if learning_goals and semantic_score >= 0.60:
                match_reasons.append("Learning goals align with tutor expertise")
            elif semantic_score >= 0.70:
                match_reasons.append("High semantic compatibility with your learning need")

            # 3. Teaching mode compatibility (only if both sides provided data and match)
            tutor_mode = str(
                tutor.get("preferred_teaching_mode") or tutor.get("teaching_mode") or ""
            ).strip()
            if pref_learning_mode and tutor_mode:
                s_m = pref_learning_mode.lower()
                t_m = tutor_mode.lower()
                if s_m == t_m or "both" in (s_m, t_m):
                    match_reasons.append(
                        f"Teaching mode matches your preference ({pref_learning_mode})"
                    )

            # 4. Language compatibility (only if both sides provided data and overlap)
            raw_t_langs = (
                tutor.get("languages_can_teach_in") or tutor.get("languages") or []
            )
            if isinstance(raw_t_langs, str):
                try:
                    t_langs = json.loads(raw_t_langs)
                except Exception:
                    t_langs = [l.strip() for l in raw_t_langs.split(",") if l.strip()]
            elif isinstance(raw_t_langs, list):
                t_langs = [str(l).strip() for l in raw_t_langs if str(l).strip()]
            else:
                t_langs = []

            if student_langs and t_langs:
                shared_langs = [
                    sl
                    for sl in student_langs
                    if any(sl.lower() == tl.lower() for tl in t_langs)
                ]
                if shared_langs:
                    match_reasons.append(
                        f"Tutor teaches in your preferred language ({', '.join(shared_langs)})"
                    )

            # 5. Availability compatibility (evidence from time score)
            if preferred_slots and time_sc >= 0.75:
                match_reasons.append("Tutor is available during your preferred time")

            # 6. Budget compatibility (evidence from fee score)
            if fee_sc >= 0.85:
                match_reasons.append("Tutor is within your budget")

            # 7. Student level alignment (evidence from level overlap)
            raw_t_levels = tutor.get("student_levels") or []
            if isinstance(raw_t_levels, str):
                try:
                    t_levels = json.loads(raw_t_levels)
                except Exception:
                    t_levels = [l.strip() for l in raw_t_levels.split(",") if l.strip()]
            elif isinstance(raw_t_levels, list):
                t_levels = [str(l).strip() for l in raw_t_levels if str(l).strip()]
            else:
                t_levels = []

            if student_level and t_levels:
                if any(
                    student_level.lower() in tl.lower()
                    or tl.lower() in student_level.lower()
                    for tl in t_levels
                ):
                    match_reasons.append(
                        f"Experienced in teaching {student_level} students"
                    )

            # =====================================================================
            # Deterministic Evidence-Based Explanation Summary
            # =====================================================================
            if matched_topics and learning_goals:
                summary = (
                    f"Strong match for your {subjects_needed} learning needs, "
                    f"particularly {', '.join(matched_topics[:2])} and {learning_goals.lower().rstrip('.')}."
                )
            elif matched_topics:
                summary = (
                    f"Strong match for your {subjects_needed} learning needs, "
                    f"particularly {', '.join(matched_topics[:3])}."
                )
            elif learning_goals:
                summary = (
                    f"Strong match for your {subjects_needed} learning needs, "
                    f"aligned with {learning_goals.lower().rstrip('.')}."
                )
            else:
                summary = f"Qualified match for your {subjects_needed} learning needs."

            sub_scores_list.append([learning_need_score, loc_score, fee_sc, time_sc])

            raw_results.append(
                {
                    "tutor": tutor,
                    "tutor_subjects_list": tutor_subjects_list,
                    "distance_km": distance_km,
                    "learning_need_score": round(learning_need_score, 4),
                    "semantic_score": round(semantic_score, 4),
                    "topic_score": round(topic_score, 4),
                    "subject_score": round(learning_need_score, 4),  # Alias
                    "location_score": round(loc_score, 4),
                    "fee_score": round(fee_sc, 4),
                    "time_score": round(time_sc, 4),
                    "matched_topics": matched_topics,
                    "match_reasons": match_reasons,
                    "pedagogy_compatibility": pedagogy_compat,
                    "explanation_summary": summary,
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
            s_ln, s_loc, s_fee, s_time = norm_matrix[i]
            overall = calculate_composite_score(
                learning_need_score=float(s_ln),
                location_score=float(s_loc),
                fee_score=float(s_fee),
                time_score=float(s_time),
                weight_learning_need=weight_learning_need,
                weight_location=weight_location,
                weight_fee=weight_fee,
                weight_time=weight_time,
                weight_subject=weight_subject,
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
                        "matched_topics": item["matched_topics"],
                        "match_reasons": item["match_reasons"],
                        "pedagogy_compatibility": item["pedagogy_compatibility"],
                        "explanation_summary": item["explanation_summary"],
                        "breakdown": {
                            "learning_need_score": item["learning_need_score"],
                            "semantic_score": item["semantic_score"],
                            "topic_score": item["topic_score"],
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