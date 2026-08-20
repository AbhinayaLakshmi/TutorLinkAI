from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.student import StudentProfile, StudentRequirements
from backend.app.models.tutor import TutorProfile, Education, TutorExpertise, Availability, Certificate
from backend.app.schemas.student import StudentProfileUpdate
from backend.app.schemas.tutor import TutorProfileUpdate
from backend.app.core.exceptions import BadRequestException, ResourceNotFoundException

# --- STUDENT SERVICE OPERATIONS ---

def get_student_profile(db: Session, user_id: str) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if not profile:
        profile = StudentProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

def update_student_profile(db: Session, user_id: str, data: StudentProfileUpdate) -> StudentProfile:
    profile = get_student_profile(db, user_id)
    
    # Update profile fields
    profile.student_type = data.student_type.upper()
    profile.location = data.location
    profile.preferred_learning_mode = data.preferred_learning_mode
    profile.preferred_tutor_languages = data.preferred_tutor_languages
    
    if data.student_type.upper() == "SCHOOL":
        profile.school_board = data.school_board
        profile.grade = data.grade
        profile.school_name = data.school_name
        # Clear university fields to prevent collision
        profile.university = None
        profile.course = None
        profile.year_of_study = None
        profile.specialization = None
    else:
        profile.university = data.university
        profile.course = data.course
        profile.year_of_study = data.year_of_study
        profile.specialization = data.specialization
        # Clear school fields
        profile.school_board = None
        profile.grade = None
        profile.school_name = None

    # Update requirements if provided
    if data.requirements is not None:
        req = db.query(StudentRequirements).filter(StudentRequirements.student_profile_id == profile.id).first()
        if not req:
            req = StudentRequirements(student_profile_id=profile.id)
            db.add(req)
        
        req.subjects = data.requirements.subjects
        req.topics = data.requirements.topics
        req.learning_goals = data.requirements.learning_goals
        req.preferred_tutor_characteristics = data.requirements.preferred_tutor_characteristics
        req.preferred_availability = data.requirements.preferred_availability
        req.preferred_learning_mode = data.preferred_learning_mode

    db.commit()
    db.refresh(profile)
    return profile

def complete_student_onboarding(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundException("User not found")
        
    if not user.email_verified:
        raise BadRequestException("Please verify your email address before completing onboarding.")
    
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if not profile or not profile.student_type or not profile.location:
        raise BadRequestException("Please fill out your profile details before completing onboarding")
         
    if profile.student_type == "SCHOOL":
        if not profile.school_board or not profile.grade or not profile.school_name:
            raise BadRequestException("Please complete all school student profile details.")
    else:
        if not profile.university or not profile.course or not profile.year_of_study:
            raise BadRequestException("Please complete all university student profile details.")
            
    # Verify requirements are set
    if not profile.requirements or not profile.requirements.subjects:
        raise BadRequestException("Please specify at least one learning requirement subject.")

    user.onboarding_status = "COMPLETED"
    db.commit()
    db.refresh(user)
    return user


# --- TUTOR SERVICE OPERATIONS ---

def get_tutor_profile(db: Session, user_id: str) -> TutorProfile:
    profile = db.query(TutorProfile).filter(TutorProfile.user_id == user_id).first()
    if not profile:
        profile = TutorProfile(user_id=user_id, verification_status="PENDING")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

def update_tutor_profile(db: Session, user_id: str, data: TutorProfileUpdate) -> TutorProfile:
    profile = get_tutor_profile(db, user_id)
    
    if data.location is not None:
        profile.location = data.location
    if data.languages_spoken is not None:
        profile.languages_spoken = data.languages_spoken
    if data.preferred_teaching_mode is not None:
        profile.preferred_teaching_mode = data.preferred_teaching_mode

    # Update Education records
    if data.education is not None:
        # Clear existing education
        db.query(Education).filter(Education.tutor_profile_id == profile.id).delete()
        for edu in data.education:
            new_edu = Education(
                tutor_profile_id=profile.id,
                highest_degree=edu.highest_degree,
                degree_name=edu.degree_name,
                university=edu.university,
                specialization=edu.specialization,
                graduation_year=edu.graduation_year
            )
            db.add(new_edu)

    # Update Expertise
    if data.expertise is not None:
        exp = db.query(TutorExpertise).filter(TutorExpertise.tutor_profile_id == profile.id).first()
        if not exp:
            exp = TutorExpertise(tutor_profile_id=profile.id)
            db.add(exp)
        
        exp.subjects_taught = data.expertise.subjects_taught
        exp.topics_expertise = data.expertise.topics_expertise
        exp.student_levels = data.expertise.student_levels
        exp.years_of_experience = data.expertise.years_of_experience
        exp.previous_experience = data.expertise.previous_experience
        exp.skills = data.expertise.skills
        exp.languages_can_teach_in = data.expertise.languages_can_teach_in

    # Update Availability
    if data.availability is not None:
        # Clear existing availability records
        db.query(Availability).filter(Availability.tutor_profile_id == profile.id).delete()
        for avail in data.availability:
            ranges_serialized = [{"start": t.start, "end": t.end} for t in avail.time_ranges]
            new_avail = Availability(
                tutor_profile_id=profile.id,
                day_of_week=avail.day_of_week,
                time_ranges=ranges_serialized,
                preferred_session_duration=avail.preferred_session_duration,
                hourly_rate=avail.hourly_rate
            )
            db.add(new_avail)

    db.commit()
    db.refresh(profile)
    return profile

def update_tutor_profile_picture(db: Session, user_id: str, relative_path: str) -> TutorProfile:
    profile = get_tutor_profile(db, user_id)
    profile.profile_picture_path = relative_path
    db.commit()
    db.refresh(profile)
    return profile

def add_tutor_certificate(
    db: Session, 
    user_id: str, 
    relative_path: str, 
    original_filename: str, 
    file_type: str, 
    file_size: int
) -> Certificate:
    profile = get_tutor_profile(db, user_id)
    
    new_cert = Certificate(
        tutor_profile_id=profile.id,
        file_path=relative_path,
        original_filename=original_filename,
        file_type=file_type,
        file_size=file_size,
        verification_status="PENDING"
    )
    db.add(new_cert)
    db.commit()
    db.refresh(new_cert)
    return new_cert

def complete_tutor_onboarding(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundException("User not found")
        
    if not user.email_verified:
        raise BadRequestException("Please verify your email address before completing onboarding.")
        
    profile = db.query(TutorProfile).filter(TutorProfile.user_id == user_id).first()
    if not profile or not profile.location or not profile.education or not profile.expertise:
        raise BadRequestException("Please fill out profile, education and expertise before submitting")
        
    if not profile.certificates:
        raise BadRequestException("Please upload at least one degree certificate before submitting.")
        
    user.onboarding_status = "COMPLETED"
    profile.verification_status = "PENDING"
    
    db.commit()
    db.refresh(user)
    return user
