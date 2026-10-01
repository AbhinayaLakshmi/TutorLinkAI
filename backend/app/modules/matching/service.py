import os
import httpx
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.models.student import StudentProfile, StudentRequirements, LearningNeed
from backend.app.models.tutor import TutorProfile, TutorExpertise, Availability
from backend.app.models.user import User


logger = logging.getLogger("backend-matching-service")

# Resolve AI service URL safely from settings or environment
AI_SERVICE_URL = getattr(settings, "AI_SERVICE_URL", os.getenv("AI_SERVICE_URL", "http://localhost:8001"))

# Demo geocoding mapping for Chennai regions
GEOCODE_MAP = {
    "chennai": (13.0827, 80.2707),
    "adyar": (13.0012, 80.2565),
    "velachery": (12.9796, 80.2196),
    "anna nagar": (13.0850, 80.2101),
    "t nagar": (13.0418, 80.2337),
    "t. nagar": (13.0418, 80.2337),
    "thyagaraya nagar": (13.0418, 80.2337),
    "tambaram": (12.9249, 80.1278),
    "guindy": (13.0067, 80.2206),
    "porur": (13.0382, 80.1565),
    "ambattur": (13.1143, 80.1548)
}

def geocode_location(location_str: Optional[str]) -> Optional[tuple]:
    if not location_str:
        return None
    loc_clean = location_str.strip().lower()
    for key, coords in GEOCODE_MAP.items():
        if key in loc_clean:
            return coords
    return None

def parse_availability_text(pref_avail: Optional[str]) -> List[Dict[str, Any]]:
    """
    Parses availability text into matcher-compatible slots.
    If parsing is not possible, returns empty list which gives neutral score.
    """
    if not pref_avail:
        return []
    
    slots = []
    text_clean = pref_avail.lower()
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    for d in days:
        if d in text_clean:
            # Check for weekend or simple slots
            slots.append({
                "day": d.capitalize(),
                "start_time": "09:00",
                "end_time": "17:00"
            })
            
    return slots

async def get_student_recommendations(
    db: Session,
    student_user_id: str,
    learning_need_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    # 1. Load Student Profile
    student_profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_user_id).first()
    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    # 2. Resolve Learning Need / Requirements
    selected_learning_need: Optional[LearningNeed] = None
    selected_need_id: Optional[str] = None
    selected_need_title: Optional[str] = None
    subjects: List[str] = []
    topics: List[str] = []
    learning_goals: str = ""
    preferred_tutor_characteristics: str = ""
    preferred_availability: str = ""

    if learning_need_id:
        # Explicit LearningNeed requested: verify existence and ownership
        selected_learning_need = (
            db.query(LearningNeed)
            .filter(
                LearningNeed.id == learning_need_id,
                LearningNeed.student_profile_id == student_profile.id
            )
            .first()
        )
        if not selected_learning_need:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning need not found."
            )
        selected_need_id = selected_learning_need.id
        selected_need_title = selected_learning_need.title
        subjects = selected_learning_need.subjects or []
        topics = selected_learning_need.topics or []
        learning_goals = selected_learning_need.learning_goals or ""
        preferred_tutor_characteristics = selected_learning_need.preferred_tutor_characteristics or ""
        preferred_availability = selected_learning_need.preferred_availability or ""
    else:
        # Fallback resolution:
        # Step 2a: Check if student has active LearningNeeds (choose most recently updated active need)
        active_need = (
            db.query(LearningNeed)
            .filter(
                LearningNeed.student_profile_id == student_profile.id,
                LearningNeed.is_active == True
            )
            .order_by(LearningNeed.updated_at.desc(), LearningNeed.created_at.desc())
            .first()
        )
        if active_need and active_need.subjects:
            selected_learning_need = active_need
            selected_need_id = active_need.id
            selected_need_title = active_need.title
            subjects = active_need.subjects or []
            topics = active_need.topics or []
            learning_goals = active_need.learning_goals or ""
            preferred_tutor_characteristics = active_need.preferred_tutor_characteristics or ""
            preferred_availability = active_need.preferred_availability or ""
        else:
            # Step 2b: Fallback to legacy StudentRequirements for backward compatibility
            requirements = (
                db.query(StudentRequirements)
                .filter(StudentRequirements.student_profile_id == student_profile.id)
                .first()
            )
            if requirements and requirements.subjects:
                subjects = requirements.subjects or []
                topics = requirements.topics or []
                learning_goals = requirements.learning_goals or ""
                preferred_tutor_characteristics = requirements.preferred_tutor_characteristics or ""
                preferred_availability = requirements.preferred_availability or ""
            else:
                logger.info(f"Student {student_user_id} has no learning requirements defined yet.")
                return []

    # 3. Determine subject query (using the primary subject, i.e., the first subject in the list)
    primary_subject = subjects[0] if subjects else ""
    if not primary_subject:
        return []

    # 4. Resolve student coordinates
    student_coords = geocode_location(student_profile.location)
    if student_coords:
        student_lat, student_lon = student_coords
    else:
        # Default coordinates for Chennai if student location is unmatched
        student_lat, student_lon = (13.0827, 80.2707)

    # Resolve student level descriptor
    student_level = None
    if student_profile.grade:
        student_level = student_profile.grade
    elif student_profile.student_type == "UNIVERSITY" and student_profile.course:
        student_level = f"University ({student_profile.course})"
    elif student_profile.student_type:
        student_level = student_profile.student_type

    # Resolve student budget from selected LearningNeed (with fallback to unrestricted for legacy needs)
    budget_min = 0.0
    budget_max = 99999.0
    if selected_learning_need:
        if selected_learning_need.budget_min is not None:
            budget_min = float(selected_learning_need.budget_min)
        if selected_learning_need.budget_max is not None:
            budget_max = float(selected_learning_need.budget_max)

    # 5. Map student query parameters
    student_query = {
        "subjects_needed": primary_subject,
        "latitude": student_lat,
        "longitude": student_lon,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "preferred_slots": parse_availability_text(preferred_availability),
        "topics": topics,
        "learning_goals": learning_goals,
        "preferred_tutor_characteristics": preferred_tutor_characteristics,
        "student_level": student_level,
        "preferred_learning_mode": student_profile.preferred_learning_mode,
        "preferred_tutor_languages": student_profile.preferred_tutor_languages or [],
        "learning_need_id": selected_need_id,
        "learning_need_title": selected_need_title
    }

    # 6. Fetch verified tutors and eager-load relations
    verified_tutors = (
        db.query(TutorProfile)
        .options(
            joinedload(TutorProfile.user),
            joinedload(TutorProfile.expertise),
            joinedload(TutorProfile.availability)
        )
        .filter(TutorProfile.verification_status == "VERIFIED")
        .all()
    )

    if not verified_tutors:
        logger.info("No verified tutors found in database.")
        return []

    # 7. Convert database records to matcher-compatible objects
    candidate_tutors = []
    for tutor in verified_tutors:
        user = tutor.user
        expertise = tutor.expertise
        
        if not user or not expertise:
            continue

        # Resolve tutor coordinates
        tutor_coords = geocode_location(tutor.location)
        if tutor_coords:
            t_lat, t_lon = tutor_coords
        else:
            # If tutor location is unmatched, copy student coordinates to produce neutral distance score
            t_lat, t_lon = (student_lat, student_lon)

        # Get base hourly rate (minimum across availability days, or fallback to default 0.0)
        hourly_rate = 0.0
        if tutor.availability:
            hourly_rate = min([avail.hourly_rate for avail in tutor.availability])

        # Flatten availability slots
        tutor_slots = []
        for avail in tutor.availability:
            day = avail.day_of_week
            time_ranges = avail.time_ranges or []
            for tr in time_ranges:
                tutor_slots.append({
                    "day": day,
                    "start_time": tr.get("start", "00:00"),
                    "end_time": tr.get("end", "00:00")
                })

        candidate_tutors.append({
            "id": tutor.id,
            "user_id": user.id,
            "name": user.full_name,
            "subjects": expertise.subjects_taught or [],
            "bio": expertise.previous_experience or "",
            "hourly_rate": hourly_rate,
            "latitude": t_lat,
            "longitude": t_lon,
            "area_name": tutor.location or "Chennai",
            "availability": tutor_slots,
            "rating": 4.5,  # Matcher-compatible neutral fallback rating
            "topics_expertise": expertise.topics_expertise or [],
            "skills": expertise.skills or [],
            "student_levels": expertise.student_levels or [],
            "languages_can_teach_in": expertise.languages_can_teach_in or [],
            "preferred_teaching_mode": tutor.preferred_teaching_mode or "Both",
            "years_of_experience": expertise.years_of_experience or 0,
            "is_verified": tutor.verification_status == "VERIFIED"
        })

    # 8. Post payload to AI Matching Service via HTTPX
    payload = {
        "student_query": student_query,
        "candidate_tutors": candidate_tutors
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{AI_SERVICE_URL}/match", json=payload)
            
            if response.status_code != 200:
                logger.error(f"AI service returned error {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI Matching service returned an unexpected error."
                )
                
            ranked_results = response.json()

            # 9. Enrich the results for frontend presentation
            enriched_results = []
            for item in ranked_results:
                # Resolve details from original tutor record
                tutor_id = item.get("id")
                tutor_record = next((t for t in verified_tutors if t.id == tutor_id), None)
                
                profile_pic = None
                if tutor_record:
                    profile_pic = tutor_record.profile_picture_path

                enriched_results.append({
                    "id": item.get("id"),
                    "user_id": item.get("user_id"),
                    "name": item.get("name"),
                    "subjects": item.get("subjects", []),
                    "bio": item.get("bio") or "",
                    "hourly_rate": item.get("hourly_rate", 0.0),
                    "location": item.get("area_name"),
                    "availability": item.get("availability", []),
                    "rating": item.get("rating"),
                    "overall_score": item.get("overall_score"),
                    "overall_percentage": item.get("overall_percentage"),
                    "breakdown": item.get("breakdown"),
                    "learning_need_id": selected_need_id,
                    "learning_need_title": selected_need_title,
                    "profile_picture_path": profile_pic,
                    "matched_topics": item.get("matched_topics", []),
                    "match_reasons": item.get("match_reasons", []),
                    "pedagogy_compatibility": item.get("pedagogy_compatibility"),
                    "explanation_summary": item.get("explanation_summary")
                })

            return enriched_results

    except httpx.ConnectError:
        logger.exception("Failed to connect to AI Matching service.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Matching service is currently offline. Please try again later."
        )
    except httpx.TimeoutException:
        logger.exception("AI Matching service request timed out.")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI Matching service request timed out."
        )
    except Exception as e:
        logger.exception("Unexpected error calling AI Matching service.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recommendations: {str(e)}"
        )
