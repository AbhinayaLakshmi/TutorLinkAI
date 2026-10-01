"""
Deterministic Preprocessing & Feature Extraction for Research Evaluation.
Provides uniform normalization for queries, tutors, topics, subjects, and semantic text representations.
"""
import re
from typing import Dict, List, Any, Tuple


class ResearchPreprocessor:
    """Provides deterministic string, categorical, and numerical preprocessing."""

    @staticmethod
    def normalize_text(text: Any) -> str:
        """Standardizes freeform text by stripping whitespace, lowercasing, and normalizing spaces."""
        if text is None:
            return ""
        text_str = str(text).strip().lower()
        # Collapse multiple spaces into single space
        return re.sub(r"\s+", " ", text_str)

    @staticmethod
    def normalize_subject(subject: Any) -> str:
        """Canonical subject string normalization."""
        if subject is None:
            return ""
        return str(subject).strip()

    @staticmethod
    def normalize_topic_list(topics: Any) -> List[str]:
        """Normalizes topic list into a deterministic, deduplicated, sorted list."""
        if not topics or not isinstance(topics, (list, tuple, set)):
            return []
        cleaned = set()
        for t in topics:
            if t:
                cleaned.add(str(t).strip().lower())
        return sorted(list(cleaned))

    @staticmethod
    def normalize_languages(languages: Any) -> List[str]:
        """Normalizes spoken/instruction languages into a deterministic, sorted list."""
        if not languages or not isinstance(languages, (list, tuple, set)):
            return ["English"]
        cleaned = set()
        for lang in languages:
            if lang:
                cleaned.add(str(lang).strip())
        return sorted(list(cleaned)) if cleaned else ["English"]

    @staticmethod
    def prepare_query(raw_query: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts and normalizes query fields for matching models."""
        subject = raw_query.get("subject") or raw_query.get("subjects_needed", "")
        return {
            "query_id": str(raw_query.get("query_id", "")),
            "subject": ResearchPreprocessor.normalize_subject(subject),
            "subjects_needed": ResearchPreprocessor.normalize_subject(subject),
            "topics": raw_query.get("topics", []),
            "normalized_topics": ResearchPreprocessor.normalize_topic_list(raw_query.get("topics", [])),
            "learning_goals": str(raw_query.get("learning_goals", "")),
            "preferred_tutor_characteristics": str(raw_query.get("preferred_tutor_characteristics", "")),
            "student_level": str(raw_query.get("student_level", "")),
            "preferred_learning_mode": str(raw_query.get("preferred_learning_mode", "Online")),
            "preferred_tutor_languages": ResearchPreprocessor.normalize_languages(raw_query.get("preferred_tutor_languages")),
            "latitude": float(raw_query.get("latitude", 13.0827)),
            "longitude": float(raw_query.get("longitude", 80.2707)),
            "budget_min": float(raw_query.get("budget_min", 300.0)),
            "budget_max": float(raw_query.get("budget_max", 1000.0)),
            "preferred_slots": raw_query.get("preferred_slots", []),
        }

    @staticmethod
    def prepare_tutor(raw_tutor: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts and normalizes tutor profile fields for matching models."""
        subjects = raw_tutor.get("subjects") or raw_tutor.get("subjects_taught", [])
        if isinstance(subjects, str):
            subjects = [subjects]
        return {
            "tutor_id": str(raw_tutor.get("tutor_id", "")),
            "name": str(raw_tutor.get("name", "")),
            "subjects": subjects,
            "subjects_taught": subjects,
            "topics_expertise": raw_tutor.get("topics_expertise", []),
            "normalized_topics": ResearchPreprocessor.normalize_topic_list(raw_tutor.get("topics_expertise", [])),
            "skills": raw_tutor.get("skills", []),
            "student_levels": raw_tutor.get("student_levels", []),
            "languages_can_teach_in": ResearchPreprocessor.normalize_languages(raw_tutor.get("languages_can_teach_in")),
            "preferred_teaching_mode": str(raw_tutor.get("preferred_teaching_mode", "Online")),
            "hourly_rate": float(raw_tutor.get("hourly_rate", 500.0)),
            "latitude": float(raw_tutor.get("latitude", 13.0827)),
            "longitude": float(raw_tutor.get("longitude", 80.2707)),
            "location": str(raw_tutor.get("location", "")),
            "availability": raw_tutor.get("availability", []),
            "rating": float(raw_tutor.get("rating", 4.5)),
            "review_count": int(raw_tutor.get("review_count", 0)),
            "years_of_experience": int(raw_tutor.get("years_of_experience", 0)),
            "is_verified": bool(raw_tutor.get("is_verified", True)),
        }

    @staticmethod
    def build_student_semantic_text(query: Dict[str, Any]) -> str:
        """Constructs deterministic narrative string for student query embedding."""
        parts = []
        subject = query.get("subject") or query.get("subjects_needed", "")
        if subject:
            parts.append(f"Subject needed: {subject}")
        topics = query.get("topics", [])
        if topics:
            parts.append(f"Topics to study: {', '.join(topics)}")
        if query.get("learning_goals"):
            parts.append(f"Learning goals: {query['learning_goals']}")
        if query.get("preferred_tutor_characteristics"):
            parts.append(f"Preferred tutor style: {query['preferred_tutor_characteristics']}")
        if query.get("student_level"):
            parts.append(f"Student level: {query['student_level']}")
        if query.get("preferred_learning_mode"):
            parts.append(f"Preferred mode: {query['preferred_learning_mode']}")
        return ". ".join(parts)

    @staticmethod
    def build_tutor_semantic_text(tutor: Dict[str, Any]) -> str:
        """Constructs deterministic narrative string for tutor profile embedding."""
        parts = []
        subjects = tutor.get("subjects") or tutor.get("subjects_taught", [])
        if subjects:
            parts.append(f"Subjects taught: {', '.join(subjects)}")
        topics = tutor.get("topics_expertise", [])
        if topics:
            parts.append(f"Specialized topics: {', '.join(topics)}")
        skills = tutor.get("skills", [])
        if skills:
            parts.append(f"Skills and teaching methods: {', '.join(skills)}")
        student_levels = tutor.get("student_levels", [])
        if student_levels:
            parts.append(f"Target student levels: {', '.join(student_levels)}")
        if tutor.get("preferred_teaching_mode"):
            parts.append(f"Teaching mode: {tutor['preferred_teaching_mode']}")
        return ". ".join(parts)
