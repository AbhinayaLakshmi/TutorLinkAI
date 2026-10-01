import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
from backend.app.core.config import settings

def _get_student_headers(client, email):
    # Register, verify, login and get student headers
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Student User",
            "phone_number": "1234567890",
            "role": "STUDENT"
        }
    )
    otp = settings.TEST_OTP_STORE[email]
    login_res = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_matching_recommendations_flow(mock_post, client, db):
    # Register tutor
    client.post(
        "/api/auth/register",
        json={
            "email": "tutor_match@example.com",
            "password": "StrongPassword123!",
            "full_name": "Math Tutor",
            "phone_number": "1234567890",
            "role": "TUTOR"
        }
    )
    from backend.app.models.user import User
    from backend.app.models.tutor import TutorProfile, TutorExpertise, Availability

    tutor_user = db.query(User).filter(User.email == "tutor_match@example.com").first()
    tutor_profile = db.query(TutorProfile).filter(TutorProfile.user_id == tutor_user.id).first()
    if not tutor_profile:
        tutor_profile = TutorProfile(user_id=tutor_user.id)
        db.add(tutor_profile)
        db.commit()
        db.refresh(tutor_profile)
        
    tutor_profile.verification_status = "VERIFIED"
    tutor_profile.location = "Adyar"
    
    expertise = TutorExpertise(
        tutor_profile_id=tutor_profile.id,
        subjects_taught=["Mathematics"],
        years_of_experience=3
    )
    db.add(expertise)
    
    avail = Availability(
        tutor_profile_id=tutor_profile.id,
        day_of_week="Monday",
        time_ranges=[{"start": "16:00", "end": "18:00"}],
        hourly_rate=600.0
    )
    db.add(avail)
    db.commit()

    # Setup mock ranked results from AI matching service
    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "id": tutor_profile.id,
            "user_id": tutor_user.id,
            "name": "Math Tutor",
            "subjects": ["Mathematics"],
            "bio": "Expert math tutor",
            "hourly_rate": 600.0,
            "area_name": "Adyar",
            "availability": [],
            "rating": 4.5,
            "overall_score": 0.95,
            "overall_percentage": 95,
            "breakdown": {
                "subject_score": 1.0,
                "location_score": 0.9,
                "fee_score": 1.0,
                "time_score": 0.9,
                "distance_km": 2.5
            }
        }
    ]
    mock_post.return_value = mock_response

    # Register and setup student profile
    email = "student_match_test@example.com"
    headers = _get_student_headers(client, email)

    # Save student profile location and requirements
    client.put(
        "/api/onboarding/student/me",
        headers=headers,
        json={
            "student_type": "SCHOOL",
            "school_board": "CBSE",
            "grade": "Class 10",
            "school_name": "Public School",
            "location": "Velachery",
            "preferred_learning_mode": "Online",
            "preferred_tutor_languages": ["English"],
            "requirements": {
                "subjects": ["Mathematics"],
                "topics": ["Algebra"],
                "learning_goals": "Improve basic math skills",
                "preferred_tutor_characteristics": "Patient tutor",
                "preferred_availability": "Monday evening"
            }
        }
    )

    # Fetch recommendations
    res = client.get("/api/matching/recommendations", headers=headers)
    
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data) == 1
    tutor = data[0]
    assert tutor["name"] == "Math Tutor"
    assert tutor["overall_percentage"] == 95
    assert tutor["breakdown"]["distance_km"] == 2.5
    assert tutor["location"] == "Adyar"

def test_matching_unauthorized_access(client):
    res = client.get("/api/matching/recommendations")
    assert res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_matching_with_specific_learning_need_id(mock_post, client, db):
    # 1. Setup mock AI service response
    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "id": "tutor-123",
            "user_id": "user-tutor-123",
            "name": "Prof. Euler",
            "subjects": ["Mathematics", "Calculus"],
            "bio": "Math educator",
            "hourly_rate": 500.0,
            "area_name": "Adyar",
            "availability": [],
            "rating": 4.8,
            "overall_score": 0.92,
            "overall_percentage": 92,
            "breakdown": {
                "subject_score": 1.0,
                "location_score": 0.9,
                "fee_score": 0.9,
                "time_score": 0.9,
                "distance_km": 3.0
            }
        }
    ]
    mock_post.return_value = mock_response

    # 2. Setup verified tutor in DB
    from backend.app.models.user import User
    from backend.app.models.tutor import TutorProfile, TutorExpertise, Availability
    t_user = User(
        email="euler_tutor@example.com",
        hashed_password="hashedpassword123",
        full_name="Prof. Euler",
        role="TUTOR",
        email_verified=True,
        onboarding_status="COMPLETED"
    )
    db.add(t_user)
    db.flush()
    t_prof = TutorProfile(
        id="tutor-123",
        user_id=t_user.id,
        verification_status="VERIFIED",
        location="Adyar"
    )
    db.add(t_prof)
    db.add(TutorExpertise(tutor_profile_id=t_prof.id, subjects_taught=["Mathematics"]))
    db.add(Availability(tutor_profile_id=t_prof.id, day_of_week="Monday", time_ranges=[{"start": "10:00", "end": "12:00"}], hourly_rate=500.0))
    db.commit()

    # 3. Setup student with 2 learning needs
    email = "multi_need_student@example.com"
    headers = _get_student_headers(client, email)

    # Setup profile location
    client.put(
        "/api/onboarding/student/me",
        headers=headers,
        json={
            "student_type": "UNIVERSITY",
            "university": "Anna University",
            "course": "Engineering",
            "year_of_study": 3,
            "location": "Velachery",
            "preferred_learning_mode": "Online",
            "preferred_tutor_languages": ["English"]
        }
    )

    # Create Math need
    res_math = client.post(
        "/api/onboarding/student/me/learning-needs",
        headers=headers,
        json={
            "title": "Calculus & Linear Algebra",
            "subjects": ["Mathematics", "Calculus"],
            "topics": ["Integrals", "Matrices"],
            "learning_goals": "Score high in semester exam",
            "preferred_tutor_characteristics": "Patient tutor",
            "preferred_availability": "Monday morning",
            "is_active": True
        }
    )
    math_need_id = res_math.json()["id"]

    # Create Physics need
    res_phys = client.post(
        "/api/onboarding/student/me/learning-needs",
        headers=headers,
        json={
            "title": "Quantum Mechanics",
            "subjects": ["Physics"],
            "topics": ["Wave Equations"],
            "learning_goals": "Research preparation",
            "is_active": True
        }
    )
    phys_need_id = res_phys.json()["id"]

    # 4. Request recommendations specifically for Math need
    res_match_math = client.get(
        f"/api/matching/recommendations?learning_need_id={math_need_id}",
        headers=headers
    )
    assert res_match_math.status_code == status.HTTP_200_OK
    data = res_match_math.json()
    assert len(data) == 1
    rec = data[0]
    assert rec["name"] == "Prof. Euler"
    assert rec["learning_need_id"] == math_need_id
    assert rec["learning_need_title"] == "Calculus & Linear Algebra"

    # Verify AI service was called with Math parameters
    assert mock_post.called
    called_payload = mock_post.call_args[1]["json"]
    assert called_payload["student_query"]["subjects_needed"] == "Mathematics"
    assert called_payload["student_query"]["learning_need_id"] == math_need_id
    assert called_payload["student_query"]["learning_goals"] == "Score high in semester exam"

    # 5. Request recommendations specifically for Physics need
    res_match_phys = client.get(
        f"/api/matching/recommendations?learning_need_id={phys_need_id}",
        headers=headers
    )
    assert res_match_phys.status_code == status.HTTP_200_OK
    phys_data = res_match_phys.json()
    assert len(phys_data) == 1
    assert phys_data[0]["learning_need_id"] == phys_need_id
    assert phys_data[0]["learning_need_title"] == "Quantum Mechanics"

    # Verify AI service was called with Physics parameters
    called_payload_phys = mock_post.call_args[1]["json"]
    assert called_payload_phys["student_query"]["subjects_needed"] == "Physics"
    assert called_payload_phys["student_query"]["learning_need_id"] == phys_need_id


def test_matching_with_invalid_or_nonexistent_learning_need_id(client, db):
    headers = _get_student_headers(client, "invalid_need_student@example.com")
    res = client.get(
        "/api/matching/recommendations?learning_need_id=non-existent-need-uuid",
        headers=headers
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_matching_cross_student_learning_need_forbidden(client, db):
    headers_a = _get_student_headers(client, "student_owner_a@example.com")
    headers_b = _get_student_headers(client, "student_owner_b@example.com")

    # Student A creates a need
    res_need_a = client.post(
        "/api/onboarding/student/me/learning-needs",
        headers=headers_a,
        json={"title": "Private Math Need", "subjects": ["Mathematics"]}
    )
    need_a_id = res_need_a.json()["id"]

    # Student B attempts to query recommendations using Student A's need -> 404
    res_cross = client.get(
        f"/api/matching/recommendations?learning_need_id={need_a_id}",
        headers=headers_b
    )
    assert res_cross.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_matching_deterministic_active_need_fallback_when_no_id_provided(mock_post, client, db):
    # Setup verified tutor in DB
    from backend.app.models.user import User
    from backend.app.models.tutor import TutorProfile, TutorExpertise, Availability
    t_user = User(
        email="chem_tutor@example.com",
        hashed_password="hashedpassword123",
        full_name="Active Tutor",
        role="TUTOR",
        email_verified=True,
        onboarding_status="COMPLETED"
    )
    db.add(t_user)
    db.flush()
    t_prof = TutorProfile(
        id="tutor-fb",
        user_id=t_user.id,
        verification_status="VERIFIED",
        location="Adyar"
    )
    db.add(t_prof)
    db.add(TutorExpertise(tutor_profile_id=t_prof.id, subjects_taught=["Chemistry"]))
    db.add(Availability(tutor_profile_id=t_prof.id, day_of_week="Monday", time_ranges=[{"start": "10:00", "end": "12:00"}], hourly_rate=450.0))
    db.commit()

    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "id": "tutor-fb",
            "user_id": t_user.id,
            "name": "Active Tutor",
            "subjects": ["Chemistry"],
            "bio": "Chemistry teacher",
            "hourly_rate": 450.0,
            "area_name": "Adyar",
            "availability": [],
            "rating": 4.6,
            "overall_score": 0.88,
            "overall_percentage": 88,
            "breakdown": {
                "subject_score": 1.0,
                "location_score": 0.8,
                "fee_score": 0.9,
                "time_score": 0.9,
                "distance_km": 5.0
            }
        }
    ]
    mock_post.return_value = mock_response

    # Setup student
    headers = _get_student_headers(client, "active_fallback_student@example.com")

    # Add 1 inactive need (Math) and 1 active need (Chemistry)
    client.post(
        "/api/onboarding/student/me/learning-needs",
        headers=headers,
        json={"title": "Math Need", "subjects": ["Mathematics"], "is_active": False}
    )
    res_chem = client.post(
        "/api/onboarding/student/me/learning-needs",
        headers=headers,
        json={"title": "Chemistry Need", "subjects": ["Chemistry"], "is_active": True}
    )
    chem_need_id = res_chem.json()["id"]

    # Request recommendations without learning_need_id
    res = client.get("/api/matching/recommendations", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data) == 1
    assert data[0]["learning_need_id"] == chem_need_id
    assert data[0]["learning_need_title"] == "Chemistry Need"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_matching_recommendations_with_explainability_fields(mock_post, client, db):
    # Setup verified tutor in DB
    from backend.app.models.user import User
    from backend.app.models.tutor import TutorProfile, TutorExpertise, Availability
    t_user = User(
        email="explain_tutor@example.com",
        hashed_password="hashedpassword123",
        full_name="Dr. Feynman",
        role="TUTOR",
        email_verified=True,
        onboarding_status="COMPLETED"
    )
    db.add(t_user)
    db.flush()
    t_prof = TutorProfile(
        id="tutor-exp-1",
        user_id=t_user.id,
        verification_status="VERIFIED",
        location="Adyar",
        preferred_teaching_mode="Online"
    )
    db.add(t_prof)
    db.add(TutorExpertise(
        tutor_profile_id=t_prof.id,
        subjects_taught=["Physics"],
        topics_expertise=["Quantum Mechanics", "Electrodynamics"],
        skills=["Concept visualization", "Exam preparation"],
        student_levels=["Undergraduate"],
        languages_can_teach_in=["English"],
        years_of_experience=8
    ))
    db.add(Availability(tutor_profile_id=t_prof.id, day_of_week="Tuesday", time_ranges=[{"start": "14:00", "end": "16:00"}], hourly_rate=700.0))
    db.commit()

    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "id": t_prof.id,
            "user_id": t_user.id,
            "name": "Dr. Feynman",
            "subjects": ["Physics"],
            "bio": "Physics professor",
            "hourly_rate": 700.0,
            "area_name": "Adyar",
            "availability": [],
            "rating": 4.9,
            "overall_score": 0.94,
            "overall_percentage": 94,
            "matched_topics": ["Quantum Mechanics"],
            "match_reasons": [
                "Strong topic match for Quantum Mechanics",
                "Teaching mode matches your preference (Online)",
                "Tutor teaches in your preferred language (English)"
            ],
            "pedagogy_compatibility": 0.88,
            "explanation_summary": "Strong match for your Physics learning needs, particularly Quantum Mechanics.",
            "breakdown": {
                "learning_need_score": 0.95,
                "semantic_score": 0.92,
                "topic_score": 1.0,
                "subject_score": 0.95,
                "location_score": 0.9,
                "fee_score": 0.95,
                "time_score": 0.9,
                "distance_km": 3.2
            }
        }
    ]
    mock_post.return_value = mock_response

    headers = _get_student_headers(client, "explain_student@example.com")
    client.put(
        "/api/onboarding/student/me",
        headers=headers,
        json={
            "student_type": "UNIVERSITY",
            "course": "Physics",
            "location": "Velachery",
            "preferred_learning_mode": "Online",
            "preferred_tutor_languages": ["English"]
        }
    )

    res_need = client.post(
        "/api/onboarding/student/me/learning-needs",
        headers=headers,
        json={
            "title": "Quantum Physics Masterclass",
            "subjects": ["Physics"],
            "topics": ["Quantum Mechanics"],
            "learning_goals": "Advanced research readiness",
            "preferred_tutor_characteristics": "Concept visualization",
            "is_active": True
        }
    )
    need_id = res_need.json()["id"]

    res = client.get(f"/api/matching/recommendations?learning_need_id={need_id}", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data) == 1
    rec = data[0]
    assert rec["name"] == "Dr. Feynman"
    assert rec["matched_topics"] == ["Quantum Mechanics"]
    assert len(rec["match_reasons"]) == 3
    assert rec["pedagogy_compatibility"] == 0.88
    assert "Quantum Mechanics" in rec["explanation_summary"]
    assert rec["breakdown"]["learning_need_score"] == 0.95
    assert rec["breakdown"]["semantic_score"] == 0.92
    assert rec["breakdown"]["topic_score"] == 1.0

    # Verify query forwarded student_level, learning_goals, topics, languages, mode
    assert mock_post.called
    sent_query = mock_post.call_args[1]["json"]["student_query"]
    assert sent_query["topics"] == ["Quantum Mechanics"]
    assert sent_query["learning_goals"] == "Advanced research readiness"
    assert sent_query["preferred_learning_mode"] == "Online"
    assert sent_query["preferred_tutor_languages"] == ["English"]
    assert sent_query["student_level"] == "University (Physics)"

    # Verify candidate tutor had expertise forwarded
    sent_tutor = mock_post.call_args[1]["json"]["candidate_tutors"][0]
    assert sent_tutor["topics_expertise"] == ["Quantum Mechanics", "Electrodynamics"]
    assert sent_tutor["skills"] == ["Concept visualization", "Exam preparation"]
    assert sent_tutor["student_levels"] == ["Undergraduate"]
    assert sent_tutor["languages_can_teach_in"] == ["English"]
    assert sent_tutor["years_of_experience"] == 8


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_matching_passes_learning_need_budget_to_ai_service(mock_post, client, db):
    from unittest.mock import MagicMock
    from backend.app.models.user import User
    from backend.app.models.tutor import TutorProfile, TutorExpertise, Availability

    # 1. Setup tutor in DB
    t_user = User(
        email="budget_tutor@example.com",
        hashed_password="hashedpassword123",
        full_name="Budget Math Tutor",
        role="TUTOR",
        email_verified=True,
        onboarding_status="COMPLETED"
    )
    db.add(t_user)
    db.flush()
    t_prof = TutorProfile(
        id="tutor-budget-1",
        user_id=t_user.id,
        verification_status="VERIFIED",
        location="Adyar"
    )
    db.add(t_prof)
    db.add(TutorExpertise(tutor_profile_id=t_prof.id, subjects_taught=["Physics"]))
    db.add(Availability(tutor_profile_id=t_prof.id, day_of_week="Monday", time_ranges=[{"start": "10:00", "end": "12:00"}], hourly_rate=600.0))
    db.commit()

    # 2. Mock AI service response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "id": t_prof.id,
            "user_id": t_user.id,
            "name": "Budget Math Tutor",
            "subjects": ["Physics"],
            "bio": "Physics expert",
            "hourly_rate": 600.0,
            "area_name": "Adyar",
            "availability": [],
            "rating": 4.8,
            "overall_score": 0.95,
            "overall_percentage": 95,
            "match_reasons": ["Tutor is within your budget"],
            "breakdown": {
                "subject_score": 1.0,
                "location_score": 0.9,
                "fee_score": 1.0,
                "time_score": 0.9,
                "distance_km": 2.0
            }
        }
    ]
    mock_post.return_value = mock_response

    # 3. Setup student and learning need with explicit budget
    headers = _get_student_headers(client, "budget_student_test@example.com")
    res_need = client.post(
        "/api/onboarding/student/me/learning-needs",
        headers=headers,
        json={
            "title": "Physics Preparation",
            "subjects": ["Physics"],
            "budget_min": 400.0,
            "budget_max": 700.0,
            "is_active": True
        }
    )
    need_id = res_need.json()["id"]

    # 4. Request recommendations
    res = client.get(f"/api/matching/recommendations?learning_need_id={need_id}", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    # 5. Verify the AI service received the student's actual budget
    assert mock_post.called
    sent_query = mock_post.call_args[1]["json"]["student_query"]
    assert sent_query["budget_min"] == 400.0
    assert sent_query["budget_max"] == 700.0


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_matching_legacy_learning_need_without_budget_fallback(mock_post, client, db):
    from unittest.mock import MagicMock
    from backend.app.models.user import User
    from backend.app.models.tutor import TutorProfile, TutorExpertise, Availability

    # 1. Setup tutor in DB
    t_user = User(
        email="legacy_tutor@example.com",
        hashed_password="hashedpassword123",
        full_name="Legacy Tutor",
        role="TUTOR",
        email_verified=True,
        onboarding_status="COMPLETED"
    )
    db.add(t_user)
    db.flush()
    t_prof = TutorProfile(
        id="tutor-legacy-1",
        user_id=t_user.id,
        verification_status="VERIFIED",
        location="Adyar"
    )
    db.add(t_prof)
    db.add(TutorExpertise(tutor_profile_id=t_prof.id, subjects_taught=["Chemistry"]))
    db.add(Availability(tutor_profile_id=t_prof.id, day_of_week="Monday", time_ranges=[{"start": "10:00", "end": "12:00"}], hourly_rate=500.0))
    db.commit()

    # 2. Mock AI service response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "id": t_prof.id,
            "user_id": t_user.id,
            "name": "Legacy Tutor",
            "subjects": ["Chemistry"],
            "bio": "Chemistry tutor",
            "hourly_rate": 500.0,
            "area_name": "Adyar",
            "availability": [],
            "rating": 4.5,
            "overall_score": 0.90,
            "overall_percentage": 90,
            "breakdown": {
                "subject_score": 1.0,
                "location_score": 0.9,
                "fee_score": 1.0,
                "time_score": 0.9,
                "distance_km": 2.0
            }
        }
    ]
    mock_post.return_value = mock_response

    # 3. Setup student and learning need WITHOUT budget (legacy record)
    headers = _get_student_headers(client, "legacy_student_test@example.com")
    res_need = client.post(
        "/api/onboarding/student/me/learning-needs",
        headers=headers,
        json={
            "title": "Legacy Chemistry Need",
            "subjects": ["Chemistry"],
            "is_active": True
        }
    )
    need_id = res_need.json()["id"]

    # 4. Request recommendations
    res = client.get(f"/api/matching/recommendations?learning_need_id={need_id}", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    # 5. Verify the AI service received fallback budget values (0.0 to 99999.0)
    assert mock_post.called
    sent_query = mock_post.call_args[1]["json"]["student_query"]
    assert sent_query["budget_min"] == 0.0
    assert sent_query["budget_max"] == 99999.0




