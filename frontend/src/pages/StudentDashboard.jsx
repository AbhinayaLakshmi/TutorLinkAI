import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { logout } from "../services/auth";
import "../onboarding.css";

const LANGUAGES_OPTIONS = ["English", "Spanish", "French", "German", "Mandarin", "Hindi", "Arabic", "Japanese"];
const BOARDS = ["CBSE", "Matriculation", "ICSE", "State Board", "Other"];
const GRADES = Array.from({ length: 12 }, (_, i) => `Class ${i + 1}`);

export default function StudentDashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  // Editable fields states
  const [studentType, setStudentType] = useState("SCHOOL");
  const [schoolBoard, setSchoolBoard] = useState("CBSE");
  const [grade, setGrade] = useState("Class 1");
  const [schoolName, setSchoolName] = useState("");
  const [university, setUniversity] = useState("");
  const [course, setCourse] = useState("");
  const [yearOfStudy, setYearOfStudy] = useState(1);
  const [specialization, setSpecialization] = useState("");
  
  const [location, setLocation] = useState("");
  const [preferredLearningMode, setPreferredLearningMode] = useState("Online");
  const [preferredTutorLanguages, setPreferredTutorLanguages] = useState([]);

  // Requirements states
  const [subjectInput, setSubjectInput] = useState("");
  const [subjects, setSubjects] = useState([]);
  const [topicInput, setTopicInput] = useState("");
  const [topics, setTopics] = useState([]);
  const [goals, setGoals] = useState("");
  const [characteristics, setCharacteristics] = useState("");
  const [availability, setAvailability] = useState("");

  const loadData = () => {
    const storedUser = JSON.parse(localStorage.getItem("user"));
    if (!storedUser) {
      navigate("/login");
      return;
    }
    setUser(storedUser);

    api.get("/api/onboarding/student/me")
      .then((res) => {
        const d = res.data;
        setProfile(d);
        setStudentType(d.student_type || "SCHOOL");
        setSchoolBoard(d.school_board || "CBSE");
        setGrade(d.grade || "Class 1");
        setSchoolName(d.school_name || "");
        setUniversity(d.university || "");
        setCourse(d.course || "");
        setYearOfStudy(d.year_of_study || 1);
        setSpecialization(d.specialization || "");
        setLocation(d.location || "");
        setPreferredLearningMode(d.preferred_learning_mode || "Online");
        setPreferredTutorLanguages(d.preferred_tutor_languages || []);
        
        if (d.requirements) {
          const r = d.requirements;
          setSubjects(r.subjects || []);
          setTopics(r.topics || []);
          setGoals(r.learning_goals || "");
          setCharacteristics(r.preferred_tutor_characteristics || "");
          setAvailability(r.preferred_availability || "");
        }
      })
      .catch((err) => {
        if (err.response?.status === 401) {
          logout();
          navigate("/login");
        } else {
          setError("Failed to load student dashboard details.");
        }
      });
  };

  useEffect(() => {
    loadData();
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

  const handleSave = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!location) {
      setError("Location is required.");
      return;
    }

    if (studentType === "SCHOOL" && !schoolName) {
      setError("School Name is required.");
      return;
    }
    if (studentType === "UNIVERSITY" && (!university || !course)) {
      setError("University and Course/Degree are required.");
      return;
    }

    try {
      const res = await api.put("/api/onboarding/student/me", {
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
      setProfile(res.data);
      setSuccess("Profile updated successfully!");
      setIsEditing(false);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update profile.");
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  if (!user || !profile) {
    return <div className="onboard-container"><p>Loading profile...</p></div>;
  }

  return (
    <div className="onboard-container" style={{ alignItems: "stretch", maxWidth: "1000px", margin: "0 auto" }}>
      <div className="dashboard-grid">
        {/* Sidebar */}
        <div className="dashboard-sidebar">
          <div className="sidebar-avatar">🎓</div>
          <div className="sidebar-name">{user.full_name}</div>
          <div className="sidebar-role">Student</div>
          
          <ul className="sidebar-menu">
            <li className="sidebar-menu-item active" onClick={() => setIsEditing(false)}>My Profile</li>
            <li className="sidebar-menu-item" style={{ color: "var(--error-color)" }} onClick={handleLogout}>Log Out</li>
          </ul>
        </div>

        {/* Content area */}
        <div className="dashboard-content">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <h2 style={{ margin: 0 }}>Student Dashboard</h2>
            {!isEditing && (
              <button onClick={() => setIsEditing(true)} className="btn btn-primary" style={{ padding: "8px 16px" }}>
                Edit Profile
              </button>
            )}
          </div>

          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          {!isEditing ? (
            <div>
              <div className="review-section">
                <h3>Profile Details</h3>
                <div className="review-item">
                  <div className="review-label">Student Type:</div>
                  <div className="review-value">{profile.student_type}</div>
                </div>

                {profile.student_type === "SCHOOL" ? (
                  <>
                    <div className="review-item">
                      <div className="review-label">School Board:</div>
                      <div className="review-value">{profile.school_board}</div>
                    </div>
                    <div className="review-item">
                      <div className="review-label">Grade:</div>
                      <div className="review-value">{profile.grade}</div>
                    </div>
                    <div className="review-item">
                      <div className="review-label">School Name:</div>
                      <div className="review-value">{profile.school_name}</div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="review-item">
                      <div className="review-label">University:</div>
                      <div className="review-value">{profile.university}</div>
                    </div>
                    <div className="review-item">
                      <div className="review-label">Course:</div>
                      <div className="review-value">{profile.course}</div>
                    </div>
                    <div className="review-item">
                      <div className="review-label">Year of Study:</div>
                      <div className="review-value">{profile.year_of_study}</div>
                    </div>
                    <div className="review-item">
                      <div className="review-label">Specialization:</div>
                      <div className="review-value">{profile.specialization || "None"}</div>
                    </div>
                  </>
                )}

                <div className="review-item">
                  <div className="review-label">Location:</div>
                  <div className="review-value">{profile.location}</div>
                </div>
                <div className="review-item">
                  <div className="review-label">Preferred Mode:</div>
                  <div className="review-value">{profile.preferred_learning_mode}</div>
                </div>
                <div className="review-item">
                  <div className="review-label">Preferred Language for Tutoring:</div>
                  <div className="review-value">
                    {profile.preferred_tutor_languages && profile.preferred_tutor_languages.length > 0
                      ? profile.preferred_tutor_languages.join(", ")
                      : "None specified"}
                  </div>
                </div>
              </div>

              {profile.requirements && (
                <div className="review-section">
                  <h3>Learning Requirements</h3>
                  <div className="review-item">
                    <div className="review-label">Subjects:</div>
                    <div className="review-value">
                      {profile.requirements.subjects && profile.requirements.subjects.length > 0
                        ? profile.requirements.subjects.join(", ")
                        : "None specified"}
                    </div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">Topics:</div>
                    <div className="review-value">
                      {profile.requirements.topics && profile.requirements.topics.length > 0
                        ? profile.requirements.topics.join(", ")
                        : "None specified"}
                    </div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">Goals:</div>
                    <div className="review-value">{profile.requirements.learning_goals || "Not provided"}</div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">Availability:</div>
                    <div className="review-value">{profile.requirements.preferred_availability || "Not provided"}</div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">Tutor Style:</div>
                    <div className="review-value">
                      {profile.requirements.preferred_tutor_characteristics || "Not provided"}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <form onSubmit={handleSave}>
              <h3 style={{ fontSize: "16px", marginBottom: "15px", color: "var(--primary-color)" }}>Edit Profile Details</h3>
              
              <div className="form-group">
                <label className="form-label">Student Type *</label>
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
                      <label className="form-label">School Board *</label>
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
                      required
                    />
                  </div>
                </div>
              ) : (
                <div>
                  <div className="form-group">
                    <label className="form-label">University *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={university}
                      onChange={(e) => setUniversity(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Course / Degree *</label>
                      <input
                        type="text"
                        className="form-input"
                        value={course}
                        onChange={(e) => setCourse(e.target.value)}
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
                    />
                  </div>
                </div>
              )}

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Location *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Preferred Learning Mode</label>
                  <select className="form-select" value={preferredLearningMode} onChange={(e) => setPreferredLearningMode(e.target.value)}>
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

              <h3 style={{ fontSize: "16px", marginTop: "25px", marginBottom: "15px", color: "var(--primary-color)" }}>Edit Learning Requirements</h3>

              <div className="form-group">
                <label className="form-label">Subjects</label>
                <div style={{ display: "flex", gap: "10px", marginBottom: "8px" }}>
                  <input
                    type="text"
                    className="form-input"
                    value={subjectInput}
                    onChange={(e) => setSubjectInput(e.target.value)}
                    placeholder="Add subject"
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
                <label className="form-label">Topics</label>
                <div style={{ display: "flex", gap: "10px", marginBottom: "8px" }}>
                  <input
                    type="text"
                    className="form-input"
                    value={topicInput}
                    onChange={(e) => setTopicInput(e.target.value)}
                    placeholder="Add topic"
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
                <label className="form-label">Learning Goals</label>
                <textarea
                  className="form-textarea"
                  value={goals}
                  onChange={(e) => setGoals(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Preferred Availability</label>
                <input
                  type="text"
                  className="form-input"
                  value={availability}
                  onChange={(e) => setAvailability(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Preferred Tutor Style</label>
                <textarea
                  className="form-textarea"
                  value={characteristics}
                  onChange={(e) => setCharacteristics(e.target.value)}
                />
              </div>

              <div className="btn-container">
                <button type="button" onClick={() => setIsEditing(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Changes
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
