from datetime import datetime
import pytest
from fastapi import status

from backend.app.core.security import create_access_token
from backend.app.models.user import User
from backend.app.models.student import StudentProfile, StudentRequirements, LearningNeed


def _create_authenticated_student(db, email="student_api@example.com", name="API Student"):
    user = User(
        email=email,
        hashed_password="hashedpassword123",
        full_name=name,
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
        course="Computer Science",
        year_of_study=3,
        location="Chennai",
        preferred_learning_mode="Online",
        preferred_tutor_languages=["English"],
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    db.refresh(profile)

    token = create_access_token(subject=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}
    return user, profile, headers


def _create_authenticated_tutor(db, email="tutor_api@example.com"):
    user = User(
        email=email,
        hashed_password="hashedpassword123",
        full_name="API Tutor",
        phone_number="9876543211",
        role="TUTOR",
        email_verified=True,
        onboarding_status="COMPLETED",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def test_unauthenticated_access_rejected(client):
    res_list = client.get("/api/onboarding/student/me/learning-needs")
    assert res_list.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    res_create = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Test", "subjects": ["Math"]},
    )
    assert res_create.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_tutor_role_forbidden(client, db):
    _, tutor_headers = _create_authenticated_tutor(db, email="tutor_forbidden@example.com")
    res = client.get("/api/onboarding/student/me/learning-needs", headers=tutor_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_student_list_learning_needs_empty_initially(client, db):
    _, _, headers = _create_authenticated_student(db, email="empty_list@example.com")
    res = client.get("/api/onboarding/student/me/learning-needs", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json() == []


def test_student_create_learning_need(client, db):
    _, _, headers = _create_authenticated_student(db, email="create_need@example.com")
    payload = {
        "title": "Machine Learning Fundamentals",
        "subjects": ["Computer Science", "Artificial Intelligence"],
        "topics": ["Supervised Learning", "Neural Networks"],
        "learning_goals": "Understand deep learning architectures",
        "preferred_tutor_characteristics": "Industry practitioner",
        "preferred_availability": "Weekday evenings",
        "is_active": False,
    }
    res = client.post("/api/onboarding/student/me/learning-needs", json=payload, headers=headers)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["id"] is not None
    assert data["title"] == "Machine Learning Fundamentals"
    assert data["subjects"] == ["Computer Science", "Artificial Intelligence"]
    assert data["topics"] == ["Supervised Learning", "Neural Networks"]
    assert data["learning_goals"] == "Understand deep learning architectures"
    assert data["is_active"] is False


def test_student_create_active_mathematics_and_physics_simultaneously(client, db):
    _, _, headers = _create_authenticated_student(db, email="multiple_active@example.com")

    # 1. Create active Mathematics learning need
    math_payload = {
        "title": "Mathematics",
        "subjects": ["Mathematics"],
        "topics": ["Calculus", "Linear Algebra"],
        "is_active": True,
    }
    res_math = client.post("/api/onboarding/student/me/learning-needs", json=math_payload, headers=headers)
    assert res_math.status_code == status.HTTP_201_CREATED
    assert res_math.json()["is_active"] is True

    # 2. Create active Physics learning need
    physics_payload = {
        "title": "Physics",
        "subjects": ["Physics"],
        "topics": ["Mechanics", "Optics"],
        "is_active": True,
    }
    res_phys = client.post("/api/onboarding/student/me/learning-needs", json=physics_payload, headers=headers)
    assert res_phys.status_code == status.HTTP_201_CREATED
    assert res_phys.json()["is_active"] is True

    # 3. List learning needs - BOTH Mathematics and Physics must be ACTIVE
    res_list = client.get("/api/onboarding/student/me/learning-needs", headers=headers)
    assert res_list.status_code == status.HTTP_200_OK
    items = res_list.json()
    assert len(items) == 2
    for item in items:
        assert item["is_active"] is True
    titles = {item["title"] for item in items}
    assert titles == {"Mathematics", "Physics"}


def test_activate_endpoint_does_not_deactivate_other_needs(client, db):
    _, _, headers = _create_authenticated_student(db, email="activate_endpoint@example.com")

    # Math is active
    res_math = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Mathematics", "subjects": ["Mathematics"], "is_active": True},
        headers=headers,
    )
    math_id = res_math.json()["id"]

    # Physics is inactive
    res_phys = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Physics", "subjects": ["Physics"], "is_active": False},
        headers=headers,
    )
    phys_id = res_phys.json()["id"]
    assert res_phys.json()["is_active"] is False

    # Activate Physics
    res_act = client.post(f"/api/onboarding/student/me/learning-needs/{phys_id}/activate", headers=headers)
    assert res_act.status_code == status.HTTP_200_OK
    assert res_act.json()["is_active"] is True
    assert res_act.json()["id"] == phys_id

    # Verify both Mathematics and Physics are ACTIVE now
    res_list = client.get("/api/onboarding/student/me/learning-needs", headers=headers)
    items = {item["id"]: item for item in res_list.json()}
    assert items[math_id]["is_active"] is True
    assert items[phys_id]["is_active"] is True


def test_student_get_single_learning_need(client, db):
    _, _, headers = _create_authenticated_student(db, email="get_single@example.com")
    res_create = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Chemistry", "subjects": ["Chemistry"], "topics": ["Organic"]},
        headers=headers,
    )
    need_id = res_create.json()["id"]

    res_get = client.get(f"/api/onboarding/student/me/learning-needs/{need_id}", headers=headers)
    assert res_get.status_code == status.HTTP_200_OK
    data = res_get.json()
    assert data["id"] == need_id
    assert data["title"] == "Chemistry"
    assert data["subjects"] == ["Chemistry"]


def test_student_update_own_learning_need(client, db):
    _, _, headers = _create_authenticated_student(db, email="update_need@example.com")
    res_create = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Old Title", "subjects": ["Biology"], "is_active": False},
        headers=headers,
    )
    need_id = res_create.json()["id"]

    # Partial update
    update_payload = {
        "title": "New Title - Molecular Biology",
        "topics": ["Genetics", "Cell Biology"],
        "is_active": True,
    }
    res_update = client.put(f"/api/onboarding/student/me/learning-needs/{need_id}", json=update_payload, headers=headers)
    assert res_update.status_code == status.HTTP_200_OK
    data = res_update.json()
    assert data["title"] == "New Title - Molecular Biology"
    assert data["topics"] == ["Genetics", "Cell Biology"]
    assert data["subjects"] == ["Biology"]  # Unchanged
    assert data["is_active"] is True


def test_setting_one_need_inactive_does_not_modify_other_needs(client, db):
    _, _, headers = _create_authenticated_student(db, email="inactivate_single@example.com")

    res_math = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Math", "subjects": ["Math"], "is_active": True},
        headers=headers,
    )
    math_id = res_math.json()["id"]

    res_phys = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Physics", "subjects": ["Physics"], "is_active": True},
        headers=headers,
    )
    phys_id = res_phys.json()["id"]

    # Set Math to inactive
    res_put = client.put(f"/api/onboarding/student/me/learning-needs/{math_id}", json={"is_active": False}, headers=headers)
    assert res_put.status_code == status.HTTP_200_OK
    assert res_put.json()["is_active"] is False

    # Verify Physics is still active
    res_phys_get = client.get(f"/api/onboarding/student/me/learning-needs/{phys_id}", headers=headers)
    assert res_phys_get.json()["is_active"] is True


def test_student_delete_inactive_learning_need(client, db):
    _, _, headers = _create_authenticated_student(db, email="delete_inactive@example.com")
    res_create = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "To Delete", "subjects": ["History"], "is_active": False},
        headers=headers,
    )
    need_id = res_create.json()["id"]

    res_del = client.delete(f"/api/onboarding/student/me/learning-needs/{need_id}", headers=headers)
    assert res_del.status_code == status.HTTP_204_NO_CONTENT

    res_get = client.get(f"/api/onboarding/student/me/learning-needs/{need_id}", headers=headers)
    assert res_get.status_code == status.HTTP_404_NOT_FOUND


def test_student_delete_active_learning_need(client, db):
    _, _, headers = _create_authenticated_student(db, email="delete_active@example.com")
    res_create = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Active Need", "subjects": ["Math"], "is_active": True},
        headers=headers,
    )
    need_id = res_create.json()["id"]

    res_del = client.delete(f"/api/onboarding/student/me/learning-needs/{need_id}", headers=headers)
    assert res_del.status_code == status.HTTP_204_NO_CONTENT

    res_get = client.get(f"/api/onboarding/student/me/learning-needs/{need_id}", headers=headers)
    assert res_get.status_code == status.HTTP_404_NOT_FOUND


def test_deleting_one_learning_need_does_not_modify_other_learning_needs(client, db):
    _, _, headers = _create_authenticated_student(db, email="delete_isolation@example.com")

    res_1 = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Need 1", "subjects": ["Math"], "is_active": True},
        headers=headers,
    )
    id_1 = res_1.json()["id"]

    res_2 = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Need 2", "subjects": ["Physics"], "is_active": True},
        headers=headers,
    )
    id_2 = res_2.json()["id"]

    # Delete Need 1
    client.delete(f"/api/onboarding/student/me/learning-needs/{id_1}", headers=headers)

    # Need 2 must still exist and be active
    res_2_get = client.get(f"/api/onboarding/student/me/learning-needs/{id_2}", headers=headers)
    assert res_2_get.status_code == status.HTTP_200_OK
    assert res_2_get.json()["is_active"] is True


def test_deleting_learning_need_does_not_delete_student_requirements(client, db):
    _, profile, headers = _create_authenticated_student(db, email="reqs_preserved@example.com")

    # Add legacy requirement directly to profile
    req = StudentRequirements(
        student_profile_id=profile.id,
        subjects=["Legacy Subject"],
        topics=["Legacy Topic"],
    )
    db.add(req)
    db.commit()

    # Create and delete learning need via API
    res_create = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Temp Need", "subjects": ["Temp"], "is_active": True},
        headers=headers,
    )
    need_id = res_create.json()["id"]
    res_del = client.delete(f"/api/onboarding/student/me/learning-needs/{need_id}", headers=headers)
    assert res_del.status_code == status.HTTP_204_NO_CONTENT

    # Verify student requirement is completely intact
    db.refresh(profile)
    assert profile.requirements is not None
    assert profile.requirements.subjects == ["Legacy Subject"]


def test_cross_student_isolation_ownership_enforcement(client, db):
    _, _, headers_a = _create_authenticated_student(db, email="student_a@example.com", name="Student A")
    _, _, headers_b = _create_authenticated_student(db, email="student_b@example.com", name="Student B")

    # Student A creates a need
    res_a = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Need A", "subjects": ["Subject A"]},
        headers=headers_a,
    )
    need_a_id = res_a.json()["id"]

    # Student B creates a need
    res_b = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Need B", "subjects": ["Subject B"]},
        headers=headers_b,
    )
    need_b_id = res_b.json()["id"]

    # Student A CANNOT GET Student B's need (404)
    res_cross_get = client.get(f"/api/onboarding/student/me/learning-needs/{need_b_id}", headers=headers_a)
    assert res_cross_get.status_code == status.HTTP_404_NOT_FOUND

    # Student A CANNOT PUT Student B's need (404)
    res_cross_put = client.put(
        f"/api/onboarding/student/me/learning-needs/{need_b_id}",
        json={"title": "Hacked Title"},
        headers=headers_a,
    )
    assert res_cross_put.status_code == status.HTTP_404_NOT_FOUND

    # Student A CANNOT activate Student B's need (404)
    res_cross_act = client.post(
        f"/api/onboarding/student/me/learning-needs/{need_b_id}/activate",
        headers=headers_a,
    )
    assert res_cross_act.status_code == status.HTTP_404_NOT_FOUND

    # Student A CANNOT delete Student B's need (404)
    res_cross_del = client.delete(
        f"/api/onboarding/student/me/learning-needs/{need_b_id}",
        headers=headers_a,
    )
    assert res_cross_del.status_code == status.HTTP_404_NOT_FOUND

    # Listing needs returns strictly owned records
    list_a = client.get("/api/onboarding/student/me/learning-needs", headers=headers_a).json()
    assert len(list_a) == 1
    assert list_a[0]["id"] == need_a_id

    list_b = client.get("/api/onboarding/student/me/learning-needs", headers=headers_b).json()
    assert len(list_b) == 1
    assert list_b[0]["id"] == need_b_id


def test_validation_errors_on_create_and_update(client, db):
    _, _, headers = _create_authenticated_student(db, email="validation_errs@example.com")

    # Empty subjects -> 422
    res_empty_sub = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "No Subjects", "subjects": []},
        headers=headers,
    )
    assert res_empty_sub.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Missing title -> 422
    res_no_title = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"subjects": ["Math"]},
        headers=headers,
    )
    assert res_no_title.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Non-existent ID -> 404
    res_nonexistent = client.get("/api/onboarding/student/me/learning-needs/non-existent-id", headers=headers)
    assert res_nonexistent.status_code == status.HTTP_404_NOT_FOUND


def test_learning_needs_ordering(client, db):
    _, _, headers = _create_authenticated_student(db, email="ordering_test@example.com")

    # 1. Inactive need
    client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Inactive First", "subjects": ["History"], "is_active": False},
        headers=headers,
    )

    # 2. Active need
    client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Active Second", "subjects": ["Math"], "is_active": True},
        headers=headers,
    )

    res = client.get("/api/onboarding/student/me/learning-needs", headers=headers)
    items = res.json()
    assert len(items) == 2
    # Active should be first
    assert items[0]["title"] == "Active Second"
    assert items[0]["is_active"] is True
    assert items[1]["title"] == "Inactive First"
    assert items[1]["is_active"] is False


def test_student_create_learning_need_with_budget(client, db):
    _, _, headers = _create_authenticated_student(db, email="create_budget_need@example.com")
    payload = {
        "title": "Physics Preparation",
        "subjects": ["Physics"],
        "topics": ["Mechanics"],
        "budget_min": 400.0,
        "budget_max": 700.0,
        "is_active": True,
    }
    res = client.post("/api/onboarding/student/me/learning-needs", json=payload, headers=headers)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["id"] is not None
    assert data["budget_min"] == 400.0
    assert data["budget_max"] == 700.0

    # Retrieve by ID and verify budget
    need_id = data["id"]
    res_get = client.get(f"/api/onboarding/student/me/learning-needs/{need_id}", headers=headers)
    assert res_get.status_code == status.HTTP_200_OK
    get_data = res_get.json()
    assert get_data["budget_min"] == 400.0
    assert get_data["budget_max"] == 700.0

    # List learning needs and verify budget
    res_list = client.get("/api/onboarding/student/me/learning-needs", headers=headers)
    assert res_list.status_code == status.HTTP_200_OK
    list_items = res_list.json()
    matching_item = next((item for item in list_items if item["id"] == need_id), None)
    assert matching_item is not None
    assert matching_item["budget_min"] == 400.0
    assert matching_item["budget_max"] == 700.0


def test_student_update_learning_need_budget(client, db):
    _, _, headers = _create_authenticated_student(db, email="update_budget_need@example.com")
    payload = {
        "title": "Initial Need",
        "subjects": ["Mathematics"],
        "budget_min": 300.0,
        "budget_max": 500.0,
    }
    res_create = client.post("/api/onboarding/student/me/learning-needs", json=payload, headers=headers)
    assert res_create.status_code == status.HTTP_201_CREATED
    need_id = res_create.json()["id"]

    # Update budget
    update_payload = {
        "budget_min": 450.0,
        "budget_max": 800.0,
    }
    res_update = client.put(f"/api/onboarding/student/me/learning-needs/{need_id}", json=update_payload, headers=headers)
    assert res_update.status_code == status.HTTP_200_OK
    update_data = res_update.json()
    assert update_data["budget_min"] == 450.0
    assert update_data["budget_max"] == 800.0


def test_learning_need_budget_validation_errors(client, db):
    _, _, headers = _create_authenticated_student(db, email="budget_validation@example.com")

    # Negative budget_min -> 422
    res_neg_min = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Test", "subjects": ["Math"], "budget_min": -50.0, "budget_max": 500.0},
        headers=headers,
    )
    assert res_neg_min.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Negative budget_max -> 422
    res_neg_max = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Test", "subjects": ["Math"], "budget_min": 100.0, "budget_max": -10.0},
        headers=headers,
    )
    assert res_neg_max.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # budget_max < budget_min -> 422
    res_invalid_range = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Test", "subjects": ["Math"], "budget_min": 600.0, "budget_max": 400.0},
        headers=headers,
    )
    assert res_invalid_range.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_learning_need_budget_omitted_is_null(client, db):
    _, _, headers = _create_authenticated_student(db, email="omitted_budget@example.com")
    payload = {
        "title": "No Budget Need",
        "subjects": ["Biology"],
    }
    res = client.post("/api/onboarding/student/me/learning-needs", json=payload, headers=headers)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["budget_min"] is None
    assert data["budget_max"] is None


def test_cross_student_cannot_modify_learning_need_budget(client, db):
    _, _, headers_a = _create_authenticated_student(db, email="budget_owner_a@example.com", name="Student A")
    _, _, headers_b = _create_authenticated_student(db, email="budget_owner_b@example.com", name="Student B")

    # Student A creates need with budget
    res_create = client.post(
        "/api/onboarding/student/me/learning-needs",
        json={"title": "Student A Need", "subjects": ["Physics"], "budget_min": 500.0, "budget_max": 800.0},
        headers=headers_a,
    )
    need_id = res_create.json()["id"]

    # Student B attempts to modify Student A's budget -> 404
    res_hack = client.put(
        f"/api/onboarding/student/me/learning-needs/{need_id}",
        json={"budget_min": 100.0, "budget_max": 200.0},
        headers=headers_b,
    )
    assert res_hack.status_code == status.HTTP_404_NOT_FOUND

    # Verify Student A's budget remains unchanged
    res_check = client.get(f"/api/onboarding/student/me/learning-needs/{need_id}", headers=headers_a)
    assert res_check.status_code == status.HTTP_200_OK
    assert res_check.json()["budget_min"] == 500.0
    assert res_check.json()["budget_max"] == 800.0

