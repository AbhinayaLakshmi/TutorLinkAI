import pytest
from app.matching.matcher import TutorMatcher, build_student_semantic_text, build_tutor_semantic_text, calculate_pedagogy_compatibility
from app.matching.scoring import calculate_topic_overlap, calculate_learning_need_score, calculate_composite_score
from app.matching.embeddings import get_embedding_service


@pytest.fixture(scope="module")
def matcher():
    return TutorMatcher()


def test_student_and_tutor_semantic_text_builders():
    student_query = {
        "subjects_needed": "Physics",
        "topics": ["rotational motion", "mechanics"],
        "learning_goals": "exam-oriented problem solving",
        "student_level": "undergraduate",
        "preferred_tutor_characteristics": "patient, concept-focused",
        "preferred_learning_mode": "Online",
        "preferred_tutor_languages": ["English"]
    }
    s_text = build_student_semantic_text(student_query)
    assert "Subject: Physics." in s_text
    assert "rotational motion" in s_text
    assert "undergraduate" in s_text
    assert "patient, concept-focused" in s_text

    tutor = {
        "topics_expertise": ["mechanics", "rotational motion", "numerical problem solving"],
        "skills": ["exam preparation", "concept teaching"],
        "student_levels": ["undergraduate"],
        "preferred_teaching_mode": "Online",
        "languages_can_teach_in": ["English"],
        "years_of_experience": 5,
        "bio": "Experienced physics lecturer"
    }
    t_text = build_tutor_semantic_text(tutor, ["Physics"])
    assert "Subjects taught: Physics." in t_text
    assert "Topics expertise: mechanics, rotational motion" in t_text
    assert "Skills: exam preparation" in t_text
    assert "Teaching mode: Online." in t_text
    assert "Languages: English." in t_text


def test_topic_overlap_exact_and_case_insensitive():
    # Exact and case-insensitive
    score, matched = calculate_topic_overlap(
        student_topics=["Rotational Motion", "Thermodynamics"],
        tutor_topics=["rotational motion", "thermodynamics", "optics"]
    )
    assert score == 1.0
    assert "Rotational Motion" in matched
    assert "Thermodynamics" in matched


def test_topic_overlap_substring_and_token_overlap():
    # Token overlap: "rotational motion" vs "rotational mechanics"
    score, matched = calculate_topic_overlap(
        student_topics=["rotational motion"],
        tutor_topics=["rotational mechanics", "quantum physics"]
    )
    assert score > 0.3
    assert "rotational motion" in matched


def test_topic_overlap_no_match():
    score, matched = calculate_topic_overlap(
        student_topics=["organic chemistry"],
        tutor_topics=["astrophysics", "electromagnetism"]
    )
    assert score == 0.0
    assert matched == []


def test_no_topic_fallback_heuristic_score():
    # When student has no topics, score relies 100% on semantic score
    score = calculate_learning_need_score(semantic_score=0.82, topic_score=0.0, has_topics=False)
    assert score == 0.82

    # When student has topics, score uses 0.60 * semantic + 0.40 * topic
    score_with_topics = calculate_learning_need_score(semantic_score=0.80, topic_score=0.50, has_topics=True)
    expected = (0.60 * 0.80) + (0.40 * 0.50)
    assert abs(score_with_topics - expected) < 1e-5


def test_pedagogy_compatibility_evidence_requirement(matcher):
    embedder = matcher.embedding_service

    # Both provide pedagogy data
    ped_score = calculate_pedagogy_compatibility(
        student_style="patient, step-by-step concept explanations",
        tutor_skills=["concept teaching", "patient mentor", "interactive problem solving"],
        embedding_service=embedder
    )
    assert ped_score is not None
    assert 0.0 <= ped_score <= 1.0
    assert ped_score > 0.4  # strong pedagogical alignment

    # Student lacks style -> None
    ped_none_1 = calculate_pedagogy_compatibility(
        student_style=None,
        tutor_skills=["concept teaching"],
        embedding_service=embedder
    )
    assert ped_none_1 is None

    # Tutor lacks skills -> None
    ped_none_2 = calculate_pedagogy_compatibility(
        student_style="patient",
        tutor_skills=[],
        embedding_service=embedder
    )
    assert ped_none_2 is None


def test_strong_vs_weak_semantic_match(matcher):
    student_query = {
        "subjects_needed": "Computer Science",
        "topics": ["machine learning", "neural networks"],
        "learning_goals": "Master deep learning architectures and backpropagation",
        "latitude": 13.0827,
        "longitude": 80.2707
    }

    # Tutor A: Deep Learning specialist (Strong semantic match)
    tutor_a = {
        "id": "tutor-a",
        "user_id": "u-a",
        "name": "AI Specialist",
        "subjects": ["Computer Science"],
        "topics_expertise": ["deep learning", "neural networks", "gradient descent"],
        "skills": ["backpropagation implementation", "PyTorch"],
        "hourly_rate": 500.0,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "availability": []
    }

    # Tutor B: Web development specialist (Weaker semantic match for deep learning)
    tutor_b = {
        "id": "tutor-b",
        "user_id": "u-b",
        "name": "Web Developer",
        "subjects": ["Computer Science"],
        "topics_expertise": ["HTML", "CSS", "Frontend JavaScript"],
        "skills": ["web design", "DOM manipulation"],
        "hourly_rate": 500.0,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "availability": []
    }

    results = matcher.rank_tutors(
        student_query=student_query,
        candidate_tutors=[tutor_a, tutor_b]
    )

    assert len(results) == 2
    assert results[0]["id"] == "tutor-a"
    assert results[0]["breakdown"]["semantic_score"] > results[1]["breakdown"]["semantic_score"]
    assert results[0]["breakdown"]["learning_need_score"] > results[1]["breakdown"]["learning_need_score"]


def test_stage1_subject_gate_exclusion(matcher):
    student_query = {
        "subjects_needed": "Physics",
        "latitude": 13.0827,
        "longitude": 80.2707
    }

    # Tutor in History (Should fail Stage 1)
    tutor_history = {
        "id": "tutor-hist",
        "user_id": "u-hist",
        "name": "History Tutor",
        "subjects": ["World History", "Civics"],
        "hourly_rate": 400.0,
        "latitude": 13.0827,
        "longitude": 80.2707
    }

    results = matcher.rank_tutors(student_query=student_query, candidate_tutors=[tutor_history])
    assert len(results) == 0


def test_verified_tutor_filtering(matcher):
    student_query = {
        "subjects_needed": "Mathematics",
        "latitude": 13.0827,
        "longitude": 80.2707
    }

    unverified_tutor = {
        "id": "tutor-unverified",
        "user_id": "u-unv",
        "name": "Unverified Math Tutor",
        "subjects": ["Mathematics"],
        "is_verified": False,
        "hourly_rate": 400.0,
        "latitude": 13.0827,
        "longitude": 80.2707
    }

    results = matcher.rank_tutors(student_query=student_query, candidate_tutors=[unverified_tutor])
    assert len(results) == 0


def test_explainability_fields_evidence_grounded(matcher):
    student_query = {
        "subjects_needed": "Physics",
        "topics": ["Rotational Motion", "Mechanics"],
        "learning_goals": "Score well on competitive exam",
        "preferred_learning_mode": "Online",
        "preferred_tutor_languages": ["English"],
        "student_level": "Undergraduate",
        "preferred_tutor_characteristics": "Patient and clear conceptual explanations",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "budget_min": 400.0,
        "budget_max": 800.0,
        "preferred_slots": [{"day": "Monday", "start_time": "10:00", "end_time": "12:00"}]
    }

    tutor = {
        "id": "tutor-phys",
        "user_id": "u-phys",
        "name": "Dr. Raman",
        "subjects": ["Physics"],
        "topics_expertise": ["Rotational Motion", "Classical Mechanics"],
        "skills": ["conceptual clarity", "patient tutor", "exam preparation"],
        "preferred_teaching_mode": "Online",
        "languages_can_teach_in": ["English", "Tamil"],
        "student_levels": ["Undergraduate", "High School"],
        "hourly_rate": 500.0,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "availability": [{"day": "Monday", "start_time": "10:00", "end_time": "12:00"}]
    }

    results = matcher.rank_tutors(student_query=student_query, candidate_tutors=[tutor])
    assert len(results) == 1
    res = results[0]

    # Check matched_topics contains evidence
    assert "Rotational Motion" in res["matched_topics"]

    # Check match_reasons are grounded in evidence
    reasons = res["match_reasons"]
    assert any("Rotational Motion" in r for r in reasons)
    assert any("Online" in r for r in reasons)
    assert any("English" in r for r in reasons)
    assert any("budget" in r.lower() for r in reasons)
    assert any("time" in r.lower() for r in reasons)
    assert any("undergraduate" in r.lower() for r in reasons)

    # Check pedagogy_compatibility is computed
    assert res["pedagogy_compatibility"] is not None
    assert res["pedagogy_compatibility"] > 0.0

    # Check explanation_summary
    assert "Physics" in res["explanation_summary"]
    assert "Rotational Motion" in res["explanation_summary"]


def test_graceful_degradation_missing_optional_fields(matcher):
    # Student with only subject, no topics, no goals, no style, no languages
    student_query = {
        "subjects_needed": "Chemistry",
        "latitude": 13.0827,
        "longitude": 80.2707
    }

    # Tutor with only basic info
    tutor = {
        "id": "tutor-chem",
        "user_id": "u-chem",
        "name": "Chem Tutor",
        "subjects": ["Chemistry"],
        "hourly_rate": 400.0,
        "latitude": 13.0827,
        "longitude": 80.2707
    }

    results = matcher.rank_tutors(student_query=student_query, candidate_tutors=[tutor])
    assert len(results) == 1
    res = results[0]
    assert res["overall_score"] > 0.0
    assert res["matched_topics"] == []
    assert res["pedagogy_compatibility"] is None
    assert "Chemistry" in res["explanation_summary"]
