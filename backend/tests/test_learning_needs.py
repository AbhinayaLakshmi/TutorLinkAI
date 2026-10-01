import uuid
from datetime import datetime
import pytest
from pydantic import ValidationError

from backend.app.models.user import User
from backend.app.models.student import StudentProfile, StudentRequirements, LearningNeed
from backend.app.schemas.student import (
    LearningNeedCreate,
    LearningNeedUpdate,
    LearningNeedOut,
    StudentProfileOut,
)


def _create_user_and_profile(db, email="student_test@example.com"):
    user = User(
        email=email,
        hashed_password="hashedpassword123",
        full_name="Test Student",
        phone_number="9876543210",
        role="STUDENT",
        email_verified=True,
        onboarding_status="COMPLETED",
    )
    db.add(user)
    db.flush()


    profile = StudentProfile(
        user_id=user.id,
        student_type="UNIVERSITY",
        university="Anna University",
        course="B.Tech Computer Science",
        year_of_study=4,
        location="Chennai",
        preferred_learning_mode="Online",
        preferred_tutor_languages=["English", "Tamil"],
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return user, profile


def test_learning_need_model_creation(db):
    _, profile = _create_user_and_profile(db, email="need_create@example.com")

    need = LearningNeed(
        student_profile_id=profile.id,
        title="Calculus & Differential Equations",
        subjects=["Mathematics", "Calculus"],
        topics=["Integration", "Limits", "Derivatives"],
        learning_goals="Score above 90% in semester exams",
        preferred_tutor_characteristics="Patient with step-by-step proofs",
        preferred_availability="Weekends and evenings",
        is_active=True,
    )
    db.add(need)
    db.commit()
    db.refresh(need)

    assert need.id is not None
    assert len(need.id) == 36
    assert need.student_profile_id == profile.id
    assert need.title == "Calculus & Differential Equations"
    assert need.subjects == ["Mathematics", "Calculus"]
    assert need.topics == ["Integration", "Limits", "Derivatives"]
    assert need.learning_goals == "Score above 90% in semester exams"
    assert need.preferred_tutor_characteristics == "Patient with step-by-step proofs"
    assert need.preferred_availability == "Weekends and evenings"
    assert need.is_active is True
    assert isinstance(need.created_at, datetime)
    assert isinstance(need.updated_at, datetime)


def test_learning_need_belongs_to_student_profile(db):
    _, profile = _create_user_and_profile(db, email="need_belongs@example.com")

    need = LearningNeed(
        student_profile_id=profile.id,
        title="Physics Mechanics",
        subjects=["Physics"],
        topics=["Kinematics", "Dynamics"],
        is_active=False,
    )
    db.add(need)
    db.commit()
    db.refresh(need)

    # Test relationship from need -> profile
    assert need.student_profile is not None
    assert need.student_profile.id == profile.id
    assert need.student_profile.user.email == "need_belongs@example.com"


def test_multiple_learning_needs_belong_to_one_student_profile(db):
    _, profile = _create_user_and_profile(db, email="multiple_needs@example.com")

    need1 = LearningNeed(
        student_profile_id=profile.id,
        title="Mathematics",
        subjects=["Mathematics"],
        is_active=True,
    )
    need2 = LearningNeed(
        student_profile_id=profile.id,
        title="Machine Learning",
        subjects=["Python", "Computer Science"],
        is_active=False,
    )
    need3 = LearningNeed(
        student_profile_id=profile.id,
        title="Organic Chemistry",
        subjects=["Chemistry"],
        is_active=False,
    )
    db.add_all([need1, need2, need3])
    db.commit()

    db.refresh(profile)
    assert len(profile.learning_needs) == 3
    titles = {n.title for n in profile.learning_needs}
    assert titles == {"Mathematics", "Machine Learning", "Organic Chemistry"}

    active_needs = [n for n in profile.learning_needs if n.is_active]
    assert len(active_needs) == 1
    assert active_needs[0].title == "Mathematics"


def test_existing_student_requirements_still_exists(db):
    _, profile = _create_user_and_profile(db, email="legacy_reqs@example.com")

    req = StudentRequirements(
        student_profile_id=profile.id,
        subjects=["Data Structures", "Algorithms"],
        topics=["Binary Search", "Dynamic Programming"],
        learning_goals="Pass technical interviews",
        preferred_tutor_characteristics="Experienced software engineer",
        preferred_availability="Flexible",
        preferred_learning_mode="Online",
    )
    db.add(req)
    db.commit()
    db.refresh(profile)

    assert profile.requirements is not None
    assert profile.requirements.student_profile_id == profile.id
    assert profile.requirements.subjects == ["Data Structures", "Algorithms"]
    assert profile.requirements.learning_goals == "Pass technical interviews"


def test_student_profile_can_access_both_requirements_and_learning_needs(db):
    _, profile = _create_user_and_profile(db, email="both_access@example.com")

    # Add legacy requirement
    req = StudentRequirements(
        student_profile_id=profile.id,
        subjects=["Physics"],
        topics=["Electromagnetism"],
        learning_goals="Understand Maxwell's equations",
    )
    db.add(req)

    # Add modern learning needs
    need1 = LearningNeed(
        student_profile_id=profile.id,
        title="Physics Exam Prep",
        subjects=["Physics"],
        topics=["Electromagnetism", "Optics"],
        is_active=True,
    )
    need2 = LearningNeed(
        student_profile_id=profile.id,
        title="Chemistry Lab Prep",
        subjects=["Chemistry"],
        topics=["Titration"],
        is_active=False,
    )
    db.add_all([need1, need2])
    db.commit()
    db.refresh(profile)

    # Validate coexistence
    assert profile.requirements is not None
    assert profile.requirements.subjects == ["Physics"]
    assert len(profile.learning_needs) == 2
    assert {n.title for n in profile.learning_needs} == {"Physics Exam Prep", "Chemistry Lab Prep"}


def test_learning_need_create_schema_validation():
    # Valid payload
    payload = {
        "title": "Discrete Mathematics",
        "subjects": ["Mathematics", "Computer Science"],
        "topics": ["Set Theory", "Combinatorics"],
        "learning_goals": "Master proof techniques",
        "preferred_tutor_characteristics": "Engaging and clear",
        "preferred_availability": "Weekday afternoons",
        "is_active": True,
    }
    schema = LearningNeedCreate(**payload)
    assert schema.title == "Discrete Mathematics"
    assert schema.subjects == ["Mathematics", "Computer Science"]
    assert schema.is_active is True

    # Default is_active should be False
    minimal_payload = {
        "title": "English Literature",
        "subjects": ["English"],
    }
    schema_min = LearningNeedCreate(**minimal_payload)
    assert schema_min.is_active is False
    assert schema_min.topics == []
    assert schema_min.learning_goals is None

    # Missing title should fail
    with pytest.raises(ValidationError):
        LearningNeedCreate(subjects=["Math"])

    # Missing subjects should fail
    with pytest.raises(ValidationError):
        LearningNeedCreate(title="Math Course")

    # Empty subjects list should fail
    with pytest.raises(ValidationError):
        LearningNeedCreate(title="Math Course", subjects=[])


def test_learning_need_update_schema_validation():
    # Empty update should be valid (all fields optional)
    empty_update = LearningNeedUpdate()
    assert empty_update.title is None
    assert empty_update.subjects is None
    assert empty_update.is_active is None

    # Partial update
    partial = LearningNeedUpdate(title="Advanced Calculus", is_active=True)
    assert partial.title == "Advanced Calculus"
    assert partial.is_active is True
    assert partial.subjects is None
    assert partial.topics is None


def test_learning_need_out_serialization(db):
    _, profile = _create_user_and_profile(db, email="schema_out@example.com")

    need = LearningNeed(
        student_profile_id=profile.id,
        title="Web Development",
        subjects=["JavaScript", "React"],
        topics=["Hooks", "State Management"],
        learning_goals="Build portfolio project",
        is_active=True,
    )
    db.add(need)
    db.commit()
    db.refresh(need)

    out = LearningNeedOut.model_validate(need)
    assert out.id == need.id
    assert out.student_profile_id == profile.id
    assert out.title == "Web Development"
    assert out.subjects == ["JavaScript", "React"]
    assert out.topics == ["Hooks", "State Management"]
    assert out.is_active is True
    assert out.created_at is not None
    assert out.updated_at is not None

    # Verify JSON serialization dict conversion
    out_dict = out.model_dump()
    assert out_dict["id"] == need.id
    assert out_dict["title"] == "Web Development"
    assert out_dict["is_active"] is True


def test_student_profile_out_serialization_with_learning_needs(db):
    _, profile = _create_user_and_profile(db, email="profile_out@example.com")

    req = StudentRequirements(
        student_profile_id=profile.id,
        subjects=["Mathematics"],
    )
    need = LearningNeed(
        student_profile_id=profile.id,
        title="Linear Algebra",
        subjects=["Mathematics"],
        is_active=True,
    )
    db.add_all([req, need])
    db.commit()
    db.refresh(profile)

    profile_out = StudentProfileOut.model_validate(profile)
    assert profile_out.id == profile.id
    assert profile_out.requirements is not None
    assert profile_out.requirements.subjects == ["Mathematics"]
    assert profile_out.learning_needs is not None
    assert len(profile_out.learning_needs) == 1
    assert profile_out.learning_needs[0].title == "Linear Algebra"


def test_learning_need_model_with_budget(db):
    _, profile = _create_user_and_profile(db, email="need_budget@example.com")

    need = LearningNeed(
        student_profile_id=profile.id,
        title="Physics Exam Prep",
        subjects=["Physics"],
        topics=["Thermodynamics"],
        budget_min=400.0,
        budget_max=700.0,
        is_active=True,
    )
    db.add(need)
    db.commit()
    db.refresh(need)

    assert float(need.budget_min) == 400.0
    assert float(need.budget_max) == 700.0

    out = LearningNeedOut.model_validate(need)
    assert out.budget_min == 400.0
    assert out.budget_max == 700.0


def test_learning_need_schema_budget_validation():
    # Valid budget
    valid = LearningNeedCreate(
        title="Valid Budget Need",
        subjects=["Physics"],
        budget_min=400.0,
        budget_max=700.0,
    )
    assert valid.budget_min == 400.0
    assert valid.budget_max == 700.0

    # Budget omitted (both None)
    omitted = LearningNeedCreate(
        title="No Budget Need",
        subjects=["Physics"],
    )
    assert omitted.budget_min is None
    assert omitted.budget_max is None

    # Negative minimum rejected
    with pytest.raises(ValidationError):
        LearningNeedCreate(
            title="Negative Min",
            subjects=["Physics"],
            budget_min=-50.0,
            budget_max=500.0,
        )

    # Negative maximum rejected
    with pytest.raises(ValidationError):
        LearningNeedCreate(
            title="Negative Max",
            subjects=["Physics"],
            budget_min=100.0,
            budget_max=-500.0,
        )

    # Max < Min rejected
    with pytest.raises(ValidationError):
        LearningNeedCreate(
            title="Max less than Min",
            subjects=["Physics"],
            budget_min=700.0,
            budget_max=400.0,
        )


def test_learning_need_update_schema_budget_validation():
    # Valid update budget
    up_valid = LearningNeedUpdate(
        budget_min=300.0,
        budget_max=600.0,
    )
    assert up_valid.budget_min == 300.0
    assert up_valid.budget_max == 600.0

    # Max < Min in update rejected
    with pytest.raises(ValidationError):
        LearningNeedUpdate(
            budget_min=800.0,
            budget_max=500.0,
        )

