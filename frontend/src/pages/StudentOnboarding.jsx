import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "../onboarding.css";

const LANGUAGES_OPTIONS = ["English", "Spanish", "French", "German", "Mandarin", "Hindi", "Arabic", "Japanese"];
const BOARDS = ["CBSE", "Matriculation", "ICSE", "State Board", "Other"];
const GRADES = Array.from({ length: 12 }, (_, i) => `Class ${i + 1}`);

export default function StudentOnboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [user, setUser] = useState(null);

  // Profile fields states
  const [studentType, setStudentType] = useState("SCHOOL"); // SCHOOL, UNIVERSITY
  const [schoolBoard, setSchoolBoard] = useState("CBSE");
  const [grade, setGrade] = useState("Class 1");
  const [schoolName, setSchoolName] = useState("");
  const [university, setUniversity] = useState("");
  const [course, setCourse] = useState("");
  const [yearOfStudy, setYearOfStudy] = useState(1);
  const [specialization, setSpecialization] = useState("");
  
  const [location, setLocation] = useState("");
  const [preferredLearningMode, setPreferredLearningMode] = useState("Online"); // Online, Offline, Both
  const [preferredTutorLanguages, setPreferredTutorLanguages] = useState([]);

  // Requirements states
  const [subjectInput, setSubjectInput] = useState("");
  const [subjects, setSubjects] = useState([]);
  const [topicInput, setTopicInput] = useState("");
  const [topics, setTopics] = useState([]);
  const [goals, setGoals] = useState("");
  const [characteristics, setCharacteristics] = useState("");
  const [availability, setAvailability] = useState("");

  useEffect(() => {
    // Get user details
    api.get("/api/auth/me")
      .then((res) => {
        setUser(res.data);
        if (!res.data.email_verified) {
          setError("Your email address is not verified. Please verify your email first.");
          navigate(`/verify-otp?email=${encodeURIComponent(res.data.email)}`);
        }
      })
      .catch(() => navigate("/login"));

    // Load profile skeleton
    api.get("/api/onboarding/student/me")
      .then((res) => {
        const d = res.data;
        if (d.student_type) setStudentType(d.student_type);
        if (d.school_board) setSchoolBoard(d.school_board);
        if (d.grade) setGrade(d.grade);
        if (d.school_name) setSchoolName(d.school_name);
        if (d.university) setUniversity(d.university);
        if (d.course) setCourse(d.course);
        if (d.year_of_study) setYearOfStudy(d.year_of_study);
        if (d.specialization) setSpecialization(d.specialization);
        if (d.location) setLocation(d.location);
        if (d.preferred_learning_mode) setPreferredLearningMode(d.preferred_learning_mode);
        if (d.preferred_tutor_languages) setPreferredTutorLanguages(d.preferred_tutor_languages);
        
        if (d.requirements) {
          const r = d.requirements;
          if (r.subjects) setSubjects(r.subjects);
          if (r.topics) setTopics(r.topics);
          if (r.learning_goals) setGoals(r.learning_goals);
          if (r.preferred_tutor_characteristics) setCharacteristics(r.preferred_tutor_characteristics);
          if (r.preferred_availability) setAvailability(r.preferred_availability);
        }
      })
      .catch((err) => {
        setError("Failed to load student onboarding data.");
      });
  }, [navigate]);

  const toggleLanguage = (lang) => {
    if (preferredTutorLanguages.includes(lang)) {
      setPreferredTutorLanguages(preferredTutorLanguages.filter((l) => l !== lang));
    } else {
      setPreferredTutorLanguages([...preferredTutorLanguages, lang]);
    }
  };

  const addSubject = () => {
    const val = subjectInput.trim();
    if (val && !subjects.includes(val)) {
      setSubjects([...subjects, val]);
      setSubjectInput("");
    }
  };
  const removeSubject = (sub) => setSubjects(subjects.filter((s) => s !== sub));

  const addTopic = () => {
    const val = topicInput.trim();
    if (val && !topics.includes(val)) {
      setTopics([...topics, val]);
      setTopicInput("");
    }
  };
  const removeTopic = (top) => setTopics(topics.filter((t) => t !== top));

  const saveProfileData = async () => {
    setError("");
    try {
      await api.put("/api/onboarding/student/me", {
        student_type: studentType,
        school_board: studentType === "SCHOOL" ? schoolBoard : null,
        grade: studentType === "SCHOOL" ? grade : null,
        school_name: studentType === "SCHOOL" ? schoolName : null,
        university: studentType === "UNIVERSITY" ? university : null,
        course: studentType === "UNIVERSITY" ? course : null,
        year_of_study: studentType === "UNIVERSITY" ? parseInt(yearOfStudy) : null,
        specialization: studentType === "UNIVERSITY" ? specialization : null,
        location,
        preferred_learning_mode: preferredLearningMode,
        preferred_tutor_languages: preferredTutorLanguages,
        requirements: {
          subjects,
          topics,
          learning_goals: goals,
          preferred_tutor_characteristics: characteristics,
          preferred_availability: availability,
          preferred_learning_mode: preferredLearningMode,
        },
      });
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save profile changes.");
      return false;
    }
  };

  const handleNext = async () => {
    if (step === 1) {
      if (!location) {
        setError("Location is required.");
        return;
      }
      if (studentType === "SCHOOL") {
        if (!schoolName) {
          setError("School name is required.");
          return;
        }
      } else {
        if (!university || !course) {
          setError("University and Course/Degree are required.");
          return;
        }
      }
    }
    if (step === 2) {
      if (subjects.length === 0) {
        setError("Please add at least one subject.");
        return;
      }
    }

    const saved = await saveProfileData();
    if (saved) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    setError("");
    setStep(step - 1);
  };

  const handleSubmit = async () => {
    setError("");
    setSubmitting(true);

    const saved = await saveProfileData();
    if (!saved) {
      setSubmitting(false);
      return;
    }

    try {
      await api.post("/api/onboarding/student/complete");
      setSuccess("Onboarding completed successfully! Redirecting...");
      setTimeout(() => {
        navigate("/dashboard/student");
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to complete onboarding.");
      setSubmitting(false);
    }
  };

  return (
    <div className="onboard-container">
      <div className="onboard-card">
        <h2 className="onboard-title">Student Onboarding</h2>
        <p className="onboard-subtitle">Provide details to connect with specialized tutors.</p>

        {/* Step Indicator */}
        <div className="step-indicator">
          <div className={`step-item ${step >= 1 ? "active" : ""} ${step > 1 ? "completed" : ""}`}>1</div>
          <div className={`step-item ${step >= 2 ? "active" : ""} ${step > 2 ? "completed" : ""}`}>2</div>
          <div className={`step-item ${step >= 3 ? "active" : ""} ${step > 3 ? "completed" : ""}`}>3</div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {/* STEP 1: Student Details */}
        {step === 1 && (
          <div>
            <h3 style={{ fontSize: "18px", marginBottom: "20px", fontWeight: "600" }}>Step 1 — Student Profile</h3>
            
            <div className="form-group">
              <label className="form-label">What type of student are you? *</label>
              <div className="chip-container">
                <div
                  className={`chip ${studentType === "SCHOOL" ? "selected" : ""}`}
                  onClick={() => setStudentType("SCHOOL")}
                >
                  School Student
                </div>
                <div
                  className={`chip ${studentType === "UNIVERSITY" ? "selected" : ""}`}
                  onClick={() => setStudentType("UNIVERSITY")}
                >
                  University / College Student
                </div>
              </div>
            </div>

            {studentType === "SCHOOL" ? (
              <div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">School Board / Curriculum *</label>
                    <select className="form-select" value={schoolBoard} onChange={(e) => setSchoolBoard(e.target.value)}>
                      {BOARDS.map((b) => (
                        <option key={b} value={b}>{b}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Grade *</label>
                    <select className="form-select" value={grade} onChange={(e) => setGrade(e.target.value)}>
                      {GRADES.map((g) => (
                        <option key={g} value={g}>{g}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">School Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={schoolName}
                    onChange={(e) => setSchoolName(e.target.value)}
                    placeholder="e.g. Saint Paul High School"
                    required
                  />
                </div>
              </div>
            ) : (
              <div>
                <div className="form-group">
                  <label className="form-label">University / College *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={university}
                    onChange={(e) => setUniversity(e.target.value)}
                    placeholder="e.g. Stanford University"
                    required
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Degree / Course *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={course}
                      onChange={(e) => setCourse(e.target.value)}
                      placeholder="e.g. Bachelor of Science"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Year of Study *</label>
                    <input
                      type="number"
                      className="form-input"
                      value={yearOfStudy}
                      min={1}
                      max={10}
                      onChange={(e) => setYearOfStudy(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Specialization</label>
                  <input
                    type="text"
                    className="form-input"
                    value={specialization}
                    onChange={(e) => setSpecialization(e.target.value)}
                    placeholder="e.g. Artificial Intelligence"
                  />
                </div>
              </div>
            )}

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Home Location *</label>
                <input
                  type="text"
                  className="form-input"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Chennai, TN"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Preferred Learning Mode *</label>
                <select
                  className="form-select"
                  value={preferredLearningMode}
                  onChange={(e) => setPreferredLearningMode(e.target.value)}
                >
                  <option value="Online">Online</option>
                  <option value="Offline">Offline</option>
                  <option value="Both">Both</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Preferred Language for Tutoring</label>
              <div className="chip-container">
                {LANGUAGES_OPTIONS.map((lang) => (
                  <div
                    key={lang}
                    className={`chip ${preferredTutorLanguages.includes(lang) ? "selected" : ""}`}
                    onClick={() => toggleLanguage(lang)}
                  >
                    {lang}
                  </div>
                ))}
              </div>
            </div>

            <div className="btn-container" style={{ justifyContent: "flex-end" }}>
              <button onClick={handleNext} className="btn btn-primary">
                Next Step
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Requirements */}
        {step === 2 && (
          <div>
            <h3 style={{ fontSize: "18px", marginBottom: "20px", fontWeight: "600" }}>Step 2 — Learning Requirements</h3>
            
            <div className="form-group">
              <label className="form-label">Subjects You Need Help With *</label>
              <div style={{ display: "flex", gap: "10px", marginBottom: "8px" }}>
                <input
                  type="text"
                  className="form-input"
                  value={subjectInput}
                  onChange={(e) => setSubjectInput(e.target.value)}
                  placeholder="Add subject (e.g. Physics)"
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addSubject())}
                />
                <button type="button" onClick={addSubject} className="btn btn-secondary">Add</button>
              </div>
              <div className="chip-container">
                {subjects.map((sub) => (
                  <span key={sub} className="chip selected">
                    {sub} <span style={{ marginLeft: "6px", cursor: "pointer" }} onClick={() => removeSubject(sub)}>×</span>
                  </span>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Specific Topics</label>
              <div style={{ display: "flex", gap: "10px", marginBottom: "8px" }}>
                <input
                  type="text"
                  className="form-input"
                  value={topicInput}
                  onChange={(e) => setTopicInput(e.target.value)}
                  placeholder="Add topic (e.g. Calculus)"
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addTopic())}
                />
                <button type="button" onClick={addTopic} className="btn btn-secondary">Add</button>
              </div>
              <div className="chip-container">
                {topics.map((top) => (
                  <span key={top} className="chip selected" style={{ backgroundColor: "#10b981" }}>
                    {top} <span style={{ marginLeft: "6px", cursor: "pointer" }} onClick={() => removeTopic(top)}>×</span>
                  </span>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Learning Goals & Scope of Help</label>
              <textarea
                className="form-textarea"
                value={goals}
                onChange={(e) => setGoals(e.target.value)}
                placeholder="Describe your learning difficulties and what you want to accomplish..."
              />
            </div>

            <div className="form-group">
              <label className="form-label">Preferred Availability</label>
              <input
                type="text"
                className="form-input"
                value={availability}
                onChange={(e) => setAvailability(e.target.value)}
                placeholder="e.g. Weekends, Weekday afternoons"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Preferred Tutor Characteristics</label>
              <textarea
                className="form-textarea"
                value={characteristics}
                onChange={(e) => setCharacteristics(e.target.value)}
                placeholder="e.g. Patient, interactive teaching style, highly qualified..."
              />
            </div>

            <div className="btn-container">
              <button onClick={handleBack} className="btn btn-secondary">Back</button>
              <button onClick={handleNext} className="btn btn-primary">Next Step</button>
            </div>
          </div>
        )}

        {/* STEP 3: Review & Submit */}
        {step === 3 && (
          <div>
            <h3 style={{ fontSize: "18px", marginBottom: "20px", fontWeight: "600" }}>Step 3 — Review & Submit</h3>
            <p style={{ fontSize: "14px", color: "var(--text-muted)", marginBottom: "20px" }}>
              Verify your information before completing your onboarding registration.
            </p>

            <div className="review-section">
              <h3>Profile Details</h3>
              <div className="review-item">
                <div className="review-label">Student Type:</div>
                <div className="review-value">{studentType.replace("_", " ")}</div>
              </div>
              
              {studentType === "SCHOOL" ? (
                <>
                  <div className="review-item">
                    <div className="review-label">School Board:</div>
                    <div className="review-value">{schoolBoard}</div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">Grade:</div>
                    <div className="review-value">{grade}</div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">School Name:</div>
                    <div className="review-value">{schoolName}</div>
                  </div>
                </>
              ) : (
                <>
                  <div className="review-item">
                    <div className="review-label">University:</div>
                    <div className="review-value">{university}</div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">Degree Course:</div>
                    <div className="review-value">{course}</div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">Year of Study:</div>
                    <div className="review-value">{yearOfStudy}</div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">Specialization:</div>
                    <div className="review-value">{specialization || "None"}</div>
                  </div>
                </>
              )}
              
              <div className="review-item">
                <div className="review-label">Home Location:</div>
                <div className="review-value">{location}</div>
              </div>
              <div className="review-item">
                <div className="review-label">Preferred Mode:</div>
                <div className="review-value">{preferredLearningMode}</div>
              </div>
              <div className="review-item">
                <div className="review-label">Tutoring Languages:</div>
                <div className="review-value">
                  {preferredTutorLanguages.length > 0 ? preferredTutorLanguages.join(", ") : "None specified"}
                </div>
              </div>
            </div>

            <div className="review-section">
              <h3>Learning Requirements</h3>
              <div className="review-item">
                <div className="review-label">Subjects:</div>
                <div className="review-value">{subjects.join(", ")}</div>
              </div>
              <div className="review-item">
                <div className="review-label">Topics:</div>
                <div className="review-value">{topics.join(", ") || "None specified"}</div>
              </div>
              <div className="review-item">
                <div className="review-label">Goals:</div>
                <div className="review-value">{goals || "None specified"}</div>
              </div>
              <div className="review-item">
                <div className="review-label">Availability:</div>
                <div className="review-value">{availability || "None specified"}</div>
              </div>
              <div className="review-item">
                <div className="review-label">Tutor Style:</div>
                <div className="review-value">{characteristics || "None specified"}</div>
              </div>
            </div>

            <div className="btn-container">
              <button onClick={handleBack} className="btn btn-secondary" disabled={submitting}>
                Back
              </button>
              <button
                onClick={handleSubmit}
                className="btn btn-primary"
                style={{ backgroundColor: "#10b981" }}
                disabled={submitting}
              >
                {submitting ? "Submitting..." : "Submit Onboarding"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
