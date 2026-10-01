import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { API_BASE_URL } from "../services/api";
import { logout } from "../services/auth";
import "../onboarding.css";

const LANGUAGES_OPTIONS = ["English", "Spanish", "French", "German", "Mandarin", "Hindi", "Arabic", "Japanese"];
const MODES_OPTIONS = ["Online", "Offline", "Both"];
const DEGREES = ["Bachelor", "Master", "PhD", "Associate Degree", "Diploma", "High School"];
const LEVEL_OPTIONS = ["Primary", "Middle School", "High School", "University", "Adult"];
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function TutorDashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [activeTab, setActiveTab] = useState("profile"); // "profile" | "requests" | "sessions"
  const [bookingRequests, setBookingRequests] = useState([]);
  const [loadingRequests, setLoadingRequests] = useState(false);
  const [decisionLoadingId, setDecisionLoadingId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [sessionActionLoadingId, setSessionActionLoadingId] = useState(null);
  const [completeModalSession, setCompleteModalSession] = useState(null);
  const [completionNote, setCompletionNote] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState("");
  const fileInputRef = React.useRef(null);
  const [uploading, setUploading] = useState(false);

  // Reviews and Rating Summary state
  const [reviews, setReviews] = useState([]);
  const [reviewSummary, setReviewSummary] = useState({ average_rating: 0, total_reviews: 0, rating_distribution: {} });
  const [loadingReviews, setLoadingReviews] = useState(false);

  const handlePhotoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const allowedExtensions = /(\.jpg|\.jpeg|\.png)$/i;
    if (!allowedExtensions.exec(file.name)) {
      setError("Only JPG, JPEG, and PNG images are allowed.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    setError("");
    setSuccess("");

    try {
      const res = await api.post("/api/onboarding/tutor/me/profile-picture", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      const updatedProfile = res.data;
      setProfile(updatedProfile);
      if (updatedProfile.profile_picture_path) {
        setAvatarUrl(`${API_BASE_URL}/uploads/${updatedProfile.profile_picture_path}?t=${Date.now()}`);
      }
      setSuccess("Profile picture updated successfully!");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to upload profile picture.");
    } finally {
      setUploading(false);
    }
  };

  // Editable fields
  const [location, setLocation] = useState("");
  const [selectedLanguages, setSelectedLanguages] = useState([]);
  const [teachMode, setTeachMode] = useState("Online");
  const [highestDegree, setHighestDegree] = useState("Bachelor");
  const [degreeName, setDegreeName] = useState("");
  const [university, setUniversity] = useState("");
  const [specialization, setSpecialization] = useState("");
  const [graduationYear, setGraduationYear] = useState(new Date().getFullYear());

  const [subjectInput, setSubjectInput] = useState("");
  const [subjects, setSubjects] = useState([]);
  const [topicInput, setTopicInput] = useState("");
  const [topics, setTopics] = useState([]);
  const [selectedLevels, setSelectedLevels] = useState([]);
  const [yearsExp, setYearsExp] = useState(0);
  const [prevExp, setPrevExp] = useState("");
  const [skillInput, setSkillInput] = useState("");
  const [skills, setSkills] = useState([]);

  const [selectedDay, setSelectedDay] = useState("Monday");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");
  const [availabilities, setAvailabilities] = useState([]);
  const [duration, setDuration] = useState(60);
  const [hourlyRate, setHourlyRate] = useState(30.0);

  const loadData = () => {
    const storedUser = JSON.parse(localStorage.getItem("user"));
    if (!storedUser) {
      navigate("/login");
      return;
    }
    setUser(storedUser);

    api.get("/api/onboarding/tutor/me")
      .then((res) => {
        const d = res.data;
        setProfile(d);
        setLocation(d.location || "");
        setSelectedLanguages(d.languages_spoken || []);
        setTeachMode(d.preferred_teaching_mode || "Online");
        if (d.profile_picture_path) {
          setAvatarUrl(`${API_BASE_URL}/uploads/${d.profile_picture_path}?t=${Date.now()}`);
        }
        if (d.id) {
          loadReviews(d.id);
        }

        if (d.education && d.education.length > 0) {
          const edu = d.education[0];
          setHighestDegree(edu.highest_degree);
          setDegreeName(edu.degree_name);
          setUniversity(edu.university);
          setSpecialization(edu.specialization || "");
          setGraduationYear(edu.graduation_year);
        }

        if (d.expertise) {
          const exp = d.expertise;
          setSubjects(exp.subjects_taught || []);
          setTopics(exp.topics_expertise || []);
          setSelectedLevels(exp.student_levels || []);
          setYearsExp(exp.years_of_experience || 0);
          setPrevExp(exp.previous_experience || "");
          setSkills(exp.skills || []);
        }

        if (d.availability && d.availability.length > 0) {
          const formatted = d.availability.map((a) => {
            const range = a.time_ranges && a.time_ranges.length > 0 ? a.time_ranges[0] : { start: "09:00", end: "17:00" };
            return {
              day_of_week: a.day_of_week,
              start: range.start,
              end: range.end,
              duration: a.preferred_session_duration,
              rate: a.hourly_rate
            };
          });
          setAvailabilities(formatted);
          setDuration(d.availability[0].preferred_session_duration);
          setHourlyRate(d.availability[0].hourly_rate);
        }
      })
      .catch((err) => {
        if (err.response?.status === 401) {
          logout();
          navigate("/login");
        } else {
          setError("Failed to load tutor dashboard details.");
        }
      });
  };

  const loadBookingRequests = () => {
    setLoadingRequests(true);
    api.get("/api/booking/tutor/requests")
      .then((res) => {
        setBookingRequests(res.data || []);
        setLoadingRequests(false);
      })
      .catch((err) => {
        console.error("Failed to load tutor booking requests:", err);
        setLoadingRequests(false);
      });
  };

  const handleDecision = async (bookingId, decision) => {
    setDecisionLoadingId(bookingId);
    setError("");
    setSuccess("");
    try {
      const res = await api.post(`/api/booking/${bookingId}/decision`, {
        decision: decision // "ACCEPTED" or "REJECTED"
      });
      setSuccess(`Booking successfully ${decision === "ACCEPTED" ? "confirmed" : "declined"}!`);
      loadBookingRequests();
      loadSessions();
      setTimeout(() => setSuccess(""), 3500);
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to ${decision.toLowerCase()} booking.`);
    } finally {
      setDecisionLoadingId(null);
    }
  };

  const loadSessions = () => {
    setLoadingSessions(true);
    api.get("/api/session/tutor")
      .then((res) => {
        setSessions(res.data || []);
        setLoadingSessions(false);
      })
      .catch((err) => {
        console.error("Failed to load tutor sessions:", err);
        setLoadingSessions(false);
      });
  };

  const loadReviews = (tutorProfileId) => {
    if (!tutorProfileId) return;
    setLoadingReviews(true);
    Promise.all([
      api.get(`/api/reviews/tutor/${tutorProfileId}`),
      api.get(`/api/reviews/tutor/${tutorProfileId}/summary`),
    ])
      .then(([revRes, sumRes]) => {
        setReviews(revRes.data || []);
        setReviewSummary(sumRes.data || { average_rating: 0, total_reviews: 0, rating_distribution: {} });
        setLoadingReviews(false);
      })
      .catch((err) => {
        console.error("Failed to load tutor reviews:", err);
        setLoadingReviews(false);
      });
  };

  const handleStartSession = async (sessionId) => {
    setSessionActionLoadingId(sessionId);
    setError("");
    setSuccess("");
    try {
      await api.post(`/api/session/${sessionId}/start`);
      setSuccess("Session started! Status is now In-Progress.");
      loadSessions();
      setTimeout(() => setSuccess(""), 3500);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start session.");
    } finally {
      setSessionActionLoadingId(null);
    }
  };

  const handleCompleteSession = async (sessionId, note) => {
    setSessionActionLoadingId(sessionId);
    setError("");
    setSuccess("");
    try {
      await api.post(`/api/session/${sessionId}/complete`, {
        completion_note: note || null,
      });
      setSuccess("Session successfully completed! Duration and summary logged.");
      setCompleteModalSession(null);
      setCompletionNote("");
      loadSessions();
      setTimeout(() => setSuccess(""), 3500);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to complete session.");
    } finally {
      setSessionActionLoadingId(null);
    }
  };

  const handleCancelSession = async (sessionId) => {
    if (!window.confirm("Are you sure you want to cancel this scheduled session?")) return;
    setSessionActionLoadingId(sessionId);
    setError("");
    setSuccess("");
    try {
      await api.post(`/api/session/${sessionId}/cancel`, {
        reason: "Cancelled by tutor",
      });
      setSuccess("Session cancelled successfully.");
      loadSessions();
      setTimeout(() => setSuccess(""), 3500);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to cancel session.");
    } finally {
      setSessionActionLoadingId(null);
    }
  };

  useEffect(() => {
    loadData();
    loadBookingRequests();
    loadSessions();
  }, [navigate]);

  const toggleLanguage = (lang) => {
    if (selectedLanguages.includes(lang)) {
      setSelectedLanguages(selectedLanguages.filter((l) => l !== lang));
    } else {
      setSelectedLanguages([...selectedLanguages, lang]);
    }
  };

  const toggleLevel = (lvl) => {
    if (selectedLevels.includes(lvl)) {
      setSelectedLevels(selectedLevels.filter((l) => l !== lvl));
    } else {
      setSelectedLevels([...selectedLevels, lvl]);
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

  const addSkill = () => {
    const val = skillInput.trim();
    if (val && !skills.includes(val)) {
      setSkills([...skills, val]);
      setSkillInput("");
    }
  };
  const removeSkill = (sk) => setSkills(skills.filter((s) => s !== sk));

  const addAvailability = () => {
    if (startTime >= endTime) {
      setError("Start time must be earlier than end time.");
      return;
    }
    setError("");
    const newAvail = {
      day_of_week: selectedDay,
      start: startTime,
      end: endTime,
      duration: parseInt(duration),
      rate: parseFloat(hourlyRate)
    };
    setAvailabilities([...availabilities, newAvail]);
  };

  const removeAvailability = (index) => {
    setAvailabilities(availabilities.filter((_, i) => i !== index));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!location || !degreeName || !university) {
      setError("Location, degree name, and university are required.");
      return;
    }

    const formattedAvailability = availabilities.map((av) => ({
      day_of_week: av.day_of_week,
      time_ranges: [{ start: av.start, end: av.end }],
      preferred_session_duration: av.duration,
      hourly_rate: av.rate
    }));

    try {
      const res = await api.put("/api/onboarding/tutor/me", {
        location,
        languages_spoken: selectedLanguages,
        preferred_teaching_mode: teachMode,
        education: [
          {
            highest_degree: highestDegree,
            degree_name: degreeName,
            university,
            specialization,
            graduation_year: parseInt(graduationYear)
          }
        ],
        expertise: {
          subjects_taught: subjects,
          topics_expertise: topics,
          student_levels: selectedLevels,
          years_of_experience: parseInt(yearsExp) || 0,
          previous_experience: prevExp,
          skills,
          languages_can_teach_in: selectedLanguages
        },
        availability: formattedAvailability
      });
      setProfile(res.data);
      setSuccess("Profile updated successfully!");
      setIsEditing(false);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update profile.");
    }
  };

  const downloadCertificate = async (certId, filename) => {
    setError("");
    try {
      const response = await api.get(`/api/onboarding/tutor/me/certificates/${certId}/download`, {
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError("Failed to download certificate. Unauthorized or file missing.");
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
    <div className="onboard-container" style={{ alignItems: "stretch", maxWidth: "1050px", margin: "0 auto" }}>
      <div className="dashboard-grid">
        {/* Sidebar */}
        <div className="dashboard-sidebar">
          <div className="sidebar-avatar">
            {avatarUrl ? <img src={avatarUrl} alt="Avatar" /> : "👨‍🏫"}
          </div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handlePhotoUpload}
            accept=".jpg,.jpeg,.png"
            style={{ display: "none" }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="btn btn-primary"
            disabled={uploading}
            style={{
              fontSize: "11px",
              padding: "6px 12px",
              margin: "-5px auto 15px",
              display: "block",
              width: "100%",
              maxWidth: "140px",
              cursor: "pointer"
            }}
          >
            {uploading ? "Uploading..." : avatarUrl ? "Change Photo" : "Upload Photo"}
          </button>
          <div className="sidebar-name">{user.full_name}</div>
          <div className="sidebar-role">Tutor</div>
          
          <ul className="sidebar-menu">
            <li
              className={`sidebar-menu-item ${activeTab === "profile" ? "active" : ""}`}
              onClick={() => { setActiveTab("profile"); setIsEditing(false); }}
            >
              👤 My Profile
            </li>
            <li
              className={`sidebar-menu-item ${activeTab === "requests" ? "active" : ""}`}
              onClick={() => { setActiveTab("requests"); setIsEditing(false); loadBookingRequests(); }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                <span>📅 Booking Requests</span>
                {bookingRequests.filter(r => r.status === "PENDING").length > 0 && (
                  <span style={{ background: "var(--primary-color)", color: "#fff", padding: "1px 6px", borderRadius: "10px", fontSize: "11px", fontWeight: "bold" }}>
                    {bookingRequests.filter(r => r.status === "PENDING").length}
                  </span>
                )}
              </div>
            </li>
            <li
              className={`sidebar-menu-item ${activeTab === "sessions" ? "active" : ""}`}
              onClick={() => { setActiveTab("sessions"); setIsEditing(false); loadSessions(); }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                <span>🎯 My Sessions</span>
                {sessions.filter(s => s.status === "SCHEDULED" || s.status === "IN_PROGRESS").length > 0 && (
                  <span style={{ background: "var(--primary-color)", color: "#fff", padding: "1px 6px", borderRadius: "10px", fontSize: "11px", fontWeight: "bold" }}>
                    {sessions.filter(s => s.status === "SCHEDULED" || s.status === "IN_PROGRESS").length}
                  </span>
                )}
              </div>
            </li>
            <li className="sidebar-menu-item" style={{ color: "var(--error-color)" }} onClick={handleLogout}>Log Out</li>
          </ul>
        </div>

        {/* Content area */}
        <div className="dashboard-content">
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          {/* TAB 1: PROFILE */}
          {activeTab === "profile" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                <h2 style={{ margin: 0 }}>Tutor Dashboard</h2>
            {!isEditing && (
              <button onClick={() => setIsEditing(true)} className="btn btn-primary" style={{ padding: "8px 16px" }}>
                Edit Profile
              </button>
            )}
          </div>

          {profile.verification_status === "VERIFIED" && (
            <div className="alert alert-success" style={{ display: "flex", alignItems: "center", gap: "10px", padding: "12px 15px", marginBottom: "20px" }}>
              <span style={{ fontSize: "20px", fontWeight: "bold" }}>✓</span>
              <div>
                <strong>Tutor Verified</strong>
                <p style={{ margin: "2px 0 0 0", fontSize: "12px" }}>
                  Your identity and credentials have been successfully verified.
                </p>
              </div>
            </div>
          )}

          {profile.verification_status === "PENDING" && (
            <div className="alert alert-warning" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong>Verification Pending</strong> — Your degree certificate is uploaded. Please run the automated consistency validation.
              </div>
              <button 
                onClick={() => navigate("/dashboard/tutor/verify")} 
                className="btn btn-secondary" 
                style={{ margin: 0, padding: "4px 10px", fontSize: "12px", borderStyle: "solid", color: "#92400e", background: "transparent" }}
              >
                Validate Certificate
              </button>
            </div>
          )}

          {profile.verification_status === "MANUAL_REVIEW" && (
            <div className="alert alert-warning" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong>Manual Review In Progress</strong> — Minor profile discrepancies are being manually audited by our administration team.
              </div>
              <button 
                onClick={() => navigate("/dashboard/tutor/verify")} 
                className="btn btn-secondary" 
                style={{ margin: 0, padding: "4px 10px", fontSize: "12px", borderStyle: "solid", color: "#92400e", background: "transparent" }}
              >
                View Pipeline Details
              </button>
            </div>
          )}

          {profile.verification_status === "FAILED" && (
            <div className="alert alert-error" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong>Verification Failed</strong> — An automated mismatch occurred. Please inspect discrepancy details.
              </div>
              <button 
                onClick={() => navigate("/dashboard/tutor/verify")} 
                className="btn btn-primary" 
                style={{ margin: 0, padding: "4px 10px", fontSize: "12px", color: "#fff" }}
              >
                View Fail Reason
              </button>
            </div>
          )}

          {!isEditing ? (
            <div>
              <div className="review-section">
                <h3>Personal Details</h3>
                <div className="review-item">
                  <div className="review-label">Location:</div>
                  <div className="review-value">{profile.location}</div>
                </div>
                <div className="review-item">
                  <div className="review-label">Languages You Can Teach In:</div>
                  <div className="review-value">
                    {profile.languages_spoken && profile.languages_spoken.length > 0 ? profile.languages_spoken.join(", ") : "None specified"}
                  </div>
                </div>
                <div className="review-item">
                  <div className="review-label">Teaching Mode:</div>
                  <div className="review-value">{profile.preferred_teaching_mode}</div>
                </div>
              </div>

              <div className="review-section">
                <h3>Education & Qualifications</h3>
                {profile.education && profile.education.map((edu, idx) => (
                  <div key={idx} style={{ marginBottom: "15px" }}>
                    <div className="review-item">
                      <div className="review-label">Degree:</div>
                      <div className="review-value">{edu.highest_degree} ({edu.degree_name})</div>
                    </div>
                    <div className="review-item">
                      <div className="review-label">University:</div>
                      <div className="review-value">{edu.university}</div>
                    </div>
                    <div className="review-item">
                      <div className="review-label">Graduation Year:</div>
                      <div className="review-value">{edu.graduation_year}</div>
                    </div>
                  </div>
                ))}

                {profile.certificates && profile.certificates.length > 0 && (
                  <div className="review-item" style={{ alignItems: "center", marginTop: "15px" }}>
                    <div className="review-label">Certificates:</div>
                    <div className="review-value" style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
                      {profile.certificates.map((c) => (
                        <button
                          key={c.id}
                          className="btn btn-secondary"
                          style={{ padding: "4px 10px", fontSize: "12px", borderStyle: "solid" }}
                          onClick={() => downloadCertificate(c.id, c.original_filename)}
                        >
                          📥 Download {c.original_filename}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {profile.expertise && (
                <div className="review-section">
                  <h3>Teaching Expertise</h3>
                  <div className="review-item">
                    <div className="review-label">Subjects:</div>
                    <div className="review-value">
                      {profile.expertise.subjects_taught && profile.expertise.subjects_taught.length > 0
                        ? profile.expertise.subjects_taught.join(", ")
                        : "None specified"}
                    </div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">Experience:</div>
                    <div className="review-value">{profile.expertise.years_of_experience} Years</div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">Skills:</div>
                    <div className="review-value">
                      {profile.expertise.skills && profile.expertise.skills.length > 0
                        ? profile.expertise.skills.join(", ")
                        : "None specified"}
                    </div>
                  </div>
                  <div className="review-item">
                    <div className="review-label">Student Levels:</div>
                    <div className="review-value">
                      {profile.expertise.student_levels && profile.expertise.student_levels.length > 0
                        ? profile.expertise.student_levels.join(", ")
                        : "None specified"}
                    </div>
                  </div>
                </div>
              )}

              <div className="review-section">
                <h3>Availability & Pricing</h3>
                <div className="review-item">
                  <div className="review-label">Hourly Rate:</div>
                  <div className="review-value">₹{hourlyRate} / Hr</div>
                </div>
                <div className="review-item">
                  <div className="review-label">Duration:</div>
                  <div className="review-value">{duration} Minutes</div>
                </div>
                <div className="review-item">
                  <div className="review-label">Availability Slots:</div>
                  <div className="review-value" style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
                    {availabilities.map((av, index) => (
                      <span key={index}>
                        <strong>{av.day_of_week}</strong>: {av.start} - {av.end}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSave}>
              <h3 style={{ fontSize: "16px", marginBottom: "15px", color: "var(--primary-color)" }}>Edit Profile Details</h3>
              
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
                  <label className="form-label">Preferred Mode</label>
                  <select className="form-select" value={teachMode} onChange={(e) => setTeachMode(e.target.value)}>
                    {MODES_OPTIONS.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Languages You Can Teach In</label>
                <div className="chip-container">
                  {LANGUAGES_OPTIONS.map((lang) => (
                    <div
                      key={lang}
                      className={`chip ${selectedLanguages.includes(lang) ? "selected" : ""}`}
                      onClick={() => toggleLanguage(lang)}
                    >
                      {lang}
                    </div>
                  ))}
                </div>
              </div>

              <h3 style={{ fontSize: "16px", marginTop: "25px", marginBottom: "15px", color: "var(--primary-color)" }}>Edit Education</h3>
              
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Degree Level *</label>
                  <select className="form-select" value={highestDegree} onChange={(e) => setHighestDegree(e.target.value)}>
                    {DEGREES.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Degree Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={degreeName}
                    onChange={(e) => setDegreeName(e.target.value)}
                    required
                  />
                </div>
              </div>

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
                  <label className="form-label">Specialization</label>
                  <input
                    type="text"
                    className="form-input"
                    value={specialization}
                    onChange={(e) => setSpecialization(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Graduation Year *</label>
                  <input
                    type="number"
                    className="form-input"
                    value={graduationYear}
                    onChange={(e) => setGraduationYear(e.target.value)}
                    required
                  />
                </div>
              </div>

              <h3 style={{ fontSize: "16px", marginTop: "25px", marginBottom: "15px", color: "var(--primary-color)" }}>Edit Expertise</h3>

              <div className="form-group">
                <label className="form-label">Subjects You Teach *</label>
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

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Years of Experience</label>
                  <input
                    type="number"
                    className="form-input"
                    value={yearsExp}
                    onChange={(e) => setYearsExp(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Target Student Levels</label>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginTop: "8px" }}>
                    {LEVEL_OPTIONS.map((lvl) => (
                      <label key={lvl} style={{ display: "flex", alignItems: "center", fontSize: "14px", gap: "5px" }}>
                        <input
                          type="checkbox"
                          checked={selectedLevels.includes(lvl)}
                          onChange={() => toggleLevel(lvl)}
                        />
                        {lvl}
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <h3 style={{ fontSize: "16px", marginTop: "25px", marginBottom: "15px", color: "var(--primary-color)" }}>Edit Availability & Pricing</h3>

              <div style={{ border: "1px solid var(--border-color)", padding: "16px", borderRadius: "6px", marginBottom: "20px" }}>
                <div className="form-row-three" style={{ alignItems: "flex-end" }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Day</label>
                    <select className="form-select" value={selectedDay} onChange={(e) => setSelectedDay(e.target.value)}>
                      {DAYS.map((d) => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Start</label>
                    <input type="time" className="form-input" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">End</label>
                    <input type="time" className="form-input" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
                  </div>
                </div>
                <button type="button" onClick={addAvailability} className="btn btn-secondary" style={{ width: "100%", marginTop: "12px", padding: "6px" }}>
                  Add Slot
                </button>
              </div>

              {availabilities.length > 0 && (
                <div style={{ marginBottom: "20px" }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    {availabilities.map((av, index) => (
                      <div key={index} style={{ display: "flex", justifyContent: "space-between", background: "var(--bg-color)", padding: "6px 12px", borderRadius: "4px", fontSize: "13px" }}>
                        <span><strong>{av.day_of_week}</strong>: {av.start} - {av.end}</span>
                        <span style={{ color: "var(--error-color)", cursor: "pointer" }} onClick={() => removeAvailability(index)}>Delete</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Session Duration</label>
                  <select className="form-select" value={duration} onChange={(e) => setDuration(e.target.value)}>
                    <option value={30}>30 Minutes</option>
                    <option value={45}>45 Minutes</option>
                    <option value={60}>60 Minutes</option>
                    <option value={90}>90 Minutes</option>
                    <option value={120}>120 Minutes</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Hourly Rate (₹) *</label>
                  <input
                    type="number"
                    className="form-input"
                    value={hourlyRate}
                    onChange={(e) => setHourlyRate(e.target.value)}
                    required
                  />
                </div>
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
          )}

          {/* TAB 2: INCOMING BOOKING REQUESTS */}
          {activeTab === "requests" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
                <div>
                  <h2 style={{ margin: "0 0 4px 0", fontSize: "22px" }}>Incoming Booking Requests</h2>
                  <p style={{ margin: 0, fontSize: "14px", color: "var(--text-muted)" }}>
                    Review students requesting tutoring sessions and accept or decline requests.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={loadBookingRequests}
                  className="btn btn-secondary"
                  disabled={loadingRequests}
                  style={{ padding: "6px 14px", fontSize: "13px" }}
                >
                  {loadingRequests ? "Refreshing..." : "🔄 Refresh"}
                </button>
              </div>

              {loadingRequests && (
                <div
                  style={{
                    textAlign: "center",
                    padding: "40px 20px",
                    background: "var(--bg-color)",
                    border: "1px dashed var(--border-color)",
                    borderRadius: "8px",
                    color: "var(--text-muted)",
                    fontSize: "14px"
                  }}
                >
                  Loading incoming booking requests...
                </div>
              )}

              {!loadingRequests && bookingRequests.length === 0 && (
                <div
                  style={{
                    textAlign: "center",
                    padding: "48px 20px",
                    background: "var(--bg-color)",
                    border: "1px dashed var(--border-color)",
                    borderRadius: "8px"
                  }}
                >
                  <div style={{ fontSize: "36px", marginBottom: "12px" }}>📬</div>
                  <h3 style={{ margin: "0 0 8px 0", fontSize: "18px" }}>No Booking Requests</h3>
                  <p style={{ margin: "0", fontSize: "14px", color: "var(--text-muted)" }}>
                    You have no incoming session booking requests at this time.
                  </p>
                </div>
              )}

              {!loadingRequests && bookingRequests.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  {bookingRequests.map((req) => {
                    const statusConfig = {
                      PENDING: {
                        label: "Action Required",
                        bg: "rgba(245, 158, 11, 0.15)",
                        color: "#d97706",
                        border: "1px solid rgba(245, 158, 11, 0.35)"
                      },
                      CONFIRMED: {
                        label: "Accepted / Confirmed",
                        bg: "rgba(16, 185, 129, 0.15)",
                        color: "var(--success-color)",
                        border: "1px solid rgba(16, 185, 129, 0.35)"
                      },
                      REJECTED: {
                        label: "Declined",
                        bg: "rgba(239, 68, 68, 0.12)",
                        color: "var(--error-color)",
                        border: "1px solid rgba(239, 68, 68, 0.3)"
                      },
                      CANCELLED: {
                        label: "Cancelled by Student",
                        bg: "var(--border-color)",
                        color: "var(--text-muted)",
                        border: "1px solid var(--border-color)"
                      }
                    }[req.status] || {
                      label: req.status,
                      bg: "var(--border-color)",
                      color: "var(--text-color)",
                      border: "1px solid var(--border-color)"
                    };

                    const isPending = req.status === "PENDING";
                    const isProcessing = decisionLoadingId === req.id;

                    return (
                      <div
                        key={req.id}
                        style={{
                          background: "var(--card-bg)",
                          border: isPending ? "1px solid rgba(245, 158, 11, 0.5)" : "1px solid var(--border-color)",
                          borderRadius: "10px",
                          padding: "20px",
                          boxShadow: isPending ? "0 2px 10px rgba(245, 158, 11, 0.08)" : "0 2px 6px rgba(0,0,0,0.02)"
                        }}
                      >
                        {/* Header: Student Info + Status Badge */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
                          <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                              <span style={{ fontSize: "22px" }}>🎓</span>
                              <div>
                                <h4 style={{ margin: 0, fontSize: "16px", fontWeight: "700" }}>
                                  {req.student_name || "Student"}
                                </h4>
                                {req.learning_need_title && (
                                  <div style={{ fontSize: "12px", color: "var(--primary-color)", marginTop: "2px", fontWeight: "500" }}>
                                    🎯 Target: {req.learning_need_title}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>

                          <span
                            style={{
                              background: statusConfig.bg,
                              color: statusConfig.color,
                              border: statusConfig.border,
                              padding: "4px 12px",
                              borderRadius: "16px",
                              fontSize: "12px",
                              fontWeight: "700"
                            }}
                          >
                            {statusConfig.label}
                          </span>
                        </div>

                        {/* Booking Details Grid */}
                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                            gap: "12px",
                            background: "var(--bg-color)",
                            padding: "12px 14px",
                            borderRadius: "6px",
                            fontSize: "13px",
                            marginBottom: "12px"
                          }}
                        >
                          <div>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                              Scheduled Date
                            </div>
                            <div style={{ fontWeight: "600", color: "var(--text-h)" }}>
                              📅 {req.scheduled_date}
                            </div>
                          </div>

                          <div>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                              Time & Duration
                            </div>
                            <div style={{ fontWeight: "600", color: "var(--text-h)" }}>
                              ⏰ {req.start_time} ({req.duration_minutes} mins)
                            </div>
                          </div>

                          <div>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                              Hourly Rate
                            </div>
                            <div style={{ fontWeight: "600", color: "var(--text-h)" }}>
                              ₹{req.hourly_rate} / hr
                            </div>
                          </div>

                          <div>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                              Total Booking Value
                            </div>
                            <div style={{ fontWeight: "700", color: "var(--success-color)" }}>
                              ₹{req.total_amount ? Number(req.total_amount).toFixed(2) : (req.hourly_rate * (req.duration_minutes / 60)).toFixed(2)}
                            </div>
                          </div>
                        </div>

                        {/* Student Message / Notes */}
                        {req.student_message && (
                          <div style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "14px", background: "rgba(0,0,0,0.02)", padding: "10px 14px", borderRadius: "6px", borderLeft: "3px solid var(--primary-color)" }}>
                            <strong style={{ color: "var(--text-h)" }}>Student Note:</strong> {req.student_message}
                          </div>
                        )}

                        {/* Accept / Reject Action Buttons for PENDING */}
                        {isPending && (
                          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", borderTop: "1px solid var(--border-color)", paddingTop: "14px", marginTop: "6px" }}>
                            <button
                              type="button"
                              onClick={() => handleDecision(req.id, "REJECTED")}
                              className="btn btn-secondary"
                              disabled={isProcessing}
                              style={{ padding: "8px 18px", fontSize: "13px", color: "var(--error-color)", borderColor: "rgba(239, 68, 68, 0.4)" }}
                            >
                              {isProcessing ? "Processing..." : "✕ Reject"}
                            </button>

                            <button
                              type="button"
                              onClick={() => handleDecision(req.id, "ACCEPTED")}
                              className="btn btn-primary"
                              disabled={isProcessing}
                              style={{ padding: "8px 20px", fontSize: "13px", background: "var(--success-color)", borderColor: "var(--success-color)" }}
                            >
                              {isProcessing ? "Processing..." : "✓ Accept Request"}
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: TUTOR SESSIONS */}
          {activeTab === "sessions" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
                <div>
                  <h2 style={{ margin: "0 0 4px 0", fontSize: "22px" }}>My Tutoring Sessions</h2>
                  <p style={{ margin: 0, fontSize: "14px", color: "var(--text-muted)" }}>
                    Manage your scheduled teaching sessions, track active classes, and record completion notes.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    loadSessions();
                    if (profile?.id) loadReviews(profile.id);
                  }}
                  className="btn btn-secondary"
                  disabled={loadingSessions || loadingReviews}
                  style={{ padding: "6px 14px", fontSize: "13px" }}
                >
                  {loadingSessions ? "Refreshing..." : "🔄 Refresh"}
                </button>
              </div>

              {/* RATINGS & REVIEWS SUMMARY CARD */}
              <div
                style={{
                  background: "var(--card-bg)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "10px",
                  padding: "20px",
                  marginBottom: "24px",
                  boxShadow: "0 2px 6px rgba(0,0,0,0.02)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div
                      style={{
                        width: "44px",
                        height: "44px",
                        borderRadius: "10px",
                        background: "rgba(245, 158, 11, 0.12)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "22px",
                      }}
                    >
                      ⭐
                    </div>
                    <div>
                      <h3 style={{ margin: "0 0 2px 0", fontSize: "16px", fontWeight: "700", color: "var(--text-h)" }}>
                        Student Ratings & Feedback
                      </h3>
                      <p style={{ margin: 0, fontSize: "12px", color: "var(--text-muted)" }}>
                        Post-session evaluations submitted by verified students.
                      </p>
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    {reviewSummary.total_reviews > 0 ? (
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: "20px", fontWeight: "800", color: "#d97706" }}>
                          ⭐ {reviewSummary.average_rating.toFixed(1)}{" "}
                          <span style={{ fontSize: "13px", fontWeight: "500", color: "var(--text-muted)" }}>/ 5.0</span>
                        </div>
                        <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                          Based on {reviewSummary.total_reviews} review{reviewSummary.total_reviews > 1 ? "s" : ""}
                        </div>
                      </div>
                    ) : (
                      <div style={{ fontSize: "13px", color: "var(--text-muted)", fontStyle: "italic", background: "var(--bg-color)", padding: "6px 12px", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                        No reviews yet
                      </div>
                    )}
                  </div>
                </div>

                {/* Recent Reviews List */}
                {reviews.length > 0 && (
                  <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "14px", marginTop: "14px" }}>
                    <div style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-h)", marginBottom: "10px" }}>
                      Recent Student Reviews:
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                      {reviews.slice(0, 3).map((rev) => (
                        <div
                          key={rev.id}
                          style={{
                            background: "var(--bg-color)",
                            padding: "10px 14px",
                            borderRadius: "8px",
                            border: "1px solid var(--border-color)",
                          }}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px", flexWrap: "wrap", gap: "6px" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                              <span style={{ color: "#d97706", fontSize: "13px", fontWeight: "700" }}>
                                {"★".repeat(rev.rating)}{"☆".repeat(5 - rev.rating)}
                              </span>
                              <span style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-h)" }}>
                                {rev.student_name || "Verified Student"}
                              </span>
                            </div>
                            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                              {new Date(rev.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          {rev.review_text && (
                            <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "var(--text-muted)", lineHeight: "1.4" }}>
                              "{rev.review_text}"
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {loadingSessions && (
                <div
                  style={{
                    textAlign: "center",
                    padding: "40px 20px",
                    background: "var(--bg-color)",
                    border: "1px dashed var(--border-color)",
                    borderRadius: "8px",
                    color: "var(--text-muted)",
                    fontSize: "14px"
                  }}
                >
                  Loading sessions...
                </div>
              )}

              {!loadingSessions && sessions.length === 0 && (
                <div
                  style={{
                    textAlign: "center",
                    padding: "48px 20px",
                    background: "var(--bg-color)",
                    border: "1px dashed var(--border-color)",
                    borderRadius: "8px"
                  }}
                >
                  <div style={{ fontSize: "36px", marginBottom: "12px" }}>🎯</div>
                  <h3 style={{ margin: "0 0 8px 0", fontSize: "18px" }}>No Sessions Yet</h3>
                  <p style={{ margin: "0", fontSize: "14px", color: "var(--text-muted)" }}>
                    When you accept incoming booking requests, your scheduled sessions will appear here.
                  </p>
                </div>
              )}

              {!loadingSessions && sessions.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  {sessions.map((session) => {
                    const statusConfig = {
                      SCHEDULED: {
                        label: "Scheduled",
                        bg: "rgba(59, 130, 246, 0.12)",
                        color: "#2563eb",
                        border: "1px solid rgba(59, 130, 246, 0.3)"
                      },
                      IN_PROGRESS: {
                        label: "🟢 In Progress / Active",
                        bg: "rgba(16, 185, 129, 0.15)",
                        color: "var(--success-color)",
                        border: "1px solid rgba(16, 185, 129, 0.35)"
                      },
                      COMPLETED: {
                        label: "Completed",
                        bg: "rgba(99, 102, 241, 0.12)",
                        color: "#4f46e5",
                        border: "1px solid rgba(99, 102, 241, 0.3)"
                      },
                      CANCELLED: {
                        label: "Cancelled",
                        bg: "var(--border-color)",
                        color: "var(--text-muted)",
                        border: "1px solid var(--border-color)"
                      }
                    }[session.status] || {
                      label: session.status,
                      bg: "var(--border-color)",
                      color: "var(--text-color)",
                      border: "1px solid var(--border-color)"
                    };

                    const isScheduled = session.status === "SCHEDULED";
                    const isInProgress = session.status === "IN_PROGRESS";
                    const isCompleted = session.status === "COMPLETED";
                    const isActionLoading = sessionActionLoadingId === session.id;

                    return (
                      <div
                        key={session.id}
                        style={{
                          background: "var(--card-bg)",
                          border: isInProgress ? "1px solid var(--success-color)" : isScheduled ? "1px solid rgba(59, 130, 246, 0.4)" : "1px solid var(--border-color)",
                          borderRadius: "10px",
                          padding: "20px",
                          boxShadow: isInProgress ? "0 2px 10px rgba(16, 185, 129, 0.12)" : "0 2px 6px rgba(0,0,0,0.02)"
                        }}
                      >
                        {/* Header: Student Info + Status Badge */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
                          <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                              <span style={{ fontSize: "22px" }}>🎓</span>
                              <div>
                                <h4 style={{ margin: 0, fontSize: "16px", fontWeight: "700" }}>
                                  {session.student_name || "Student"}
                                </h4>
                                {session.learning_need_title && (
                                  <div style={{ fontSize: "12px", color: "var(--primary-color)", marginTop: "2px", fontWeight: "500" }}>
                                    🎯 Focus: {session.learning_need_title}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>

                          <span
                            style={{
                              background: statusConfig.bg,
                              color: statusConfig.color,
                              border: statusConfig.border,
                              padding: "4px 12px",
                              borderRadius: "16px",
                              fontSize: "12px",
                              fontWeight: "700"
                            }}
                          >
                            {statusConfig.label}
                          </span>
                        </div>

                        {/* Session Details Grid */}
                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                            gap: "12px",
                            background: "var(--bg-color)",
                            padding: "12px 14px",
                            borderRadius: "6px",
                            fontSize: "13px",
                            marginBottom: "12px"
                          }}
                        >
                          <div>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                              Scheduled Date
                            </div>
                            <div style={{ fontWeight: "600", color: "var(--text-h)" }}>
                              📅 {session.scheduled_date}
                            </div>
                          </div>

                          <div>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                              Start Time & Duration
                            </div>
                            <div style={{ fontWeight: "600", color: "var(--text-h)" }}>
                              ⏰ {session.start_time} ({session.duration_minutes} mins)
                            </div>
                          </div>

                          {session.started_at && (
                            <div>
                              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                                Started Time
                              </div>
                              <div style={{ fontWeight: "600", color: "var(--success-color)" }}>
                                {new Date(session.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </div>
                            </div>
                          )}

                          {isCompleted && (
                            <div>
                              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                                Actual Duration
                              </div>
                              <div style={{ fontWeight: "700", color: "#4f46e5" }}>
                                {session.actual_duration_minutes || session.duration_minutes} mins
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Completion Note */}
                        {isCompleted && session.completion_note && (
                          <div style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "12px", background: "rgba(99, 102, 241, 0.05)", padding: "10px 14px", borderRadius: "6px", borderLeft: "3px solid #6366f1" }}>
                            <strong style={{ color: "var(--text-h)" }}>Your Summary Note:</strong> {session.completion_note}
                          </div>
                        )}

                        {/* Cancellation Reason */}
                        {session.status === "CANCELLED" && session.cancellation_reason && (
                          <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "10px", background: "rgba(239, 68, 68, 0.05)", padding: "8px 12px", borderRadius: "4px" }}>
                            <strong>Cancellation Reason:</strong> {session.cancellation_reason}
                          </div>
                        )}

                        {/* Action Buttons */}
                        {isScheduled && (
                          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", borderTop: "1px solid var(--border-color)", paddingTop: "14px", marginTop: "6px" }}>
                            <button
                              type="button"
                              onClick={() => handleCancelSession(session.id)}
                              className="btn btn-secondary"
                              disabled={isActionLoading}
                              style={{ padding: "6px 14px", fontSize: "12px", color: "var(--error-color)", borderColor: "rgba(239, 68, 68, 0.3)" }}
                            >
                              {isActionLoading ? "Processing..." : "Cancel Session"}
                            </button>

                            <button
                              type="button"
                              onClick={() => handleStartSession(session.id)}
                              className="btn btn-primary"
                              disabled={isActionLoading}
                              style={{ padding: "6px 18px", fontSize: "12px", background: "var(--primary-color)" }}
                            >
                              {isActionLoading ? "Processing..." : "🚀 Start Session"}
                            </button>
                          </div>
                        )}

                        {isInProgress && (
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid var(--border-color)", paddingTop: "14px", marginTop: "6px", flexWrap: "wrap", gap: "10px" }}>
                            <span style={{ fontSize: "12px", color: "var(--success-color)", fontWeight: "600" }}>
                              Session currently in progress...
                            </span>
                            <button
                              type="button"
                              onClick={() => {
                                setCompleteModalSession(session);
                                setCompletionNote("");
                              }}
                              className="btn btn-primary"
                              disabled={isActionLoading}
                              style={{ padding: "6px 18px", fontSize: "12px", background: "var(--success-color)", borderColor: "var(--success-color)" }}
                            >
                              ✓ Complete Session
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* COMPLETE SESSION MODAL */}
      {completeModalSession && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "20px"
          }}
        >
          <div
            style={{
              background: "var(--card-bg, #ffffff)",
              borderRadius: "12px",
              width: "100%",
              maxWidth: "500px",
              padding: "24px",
              boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"
            }}
          >
            <h3 style={{ margin: "0 0 8px 0", fontSize: "18px" }}>Complete Session</h3>
            <p style={{ margin: "0 0 16px 0", fontSize: "13px", color: "var(--text-muted)" }}>
              Completing session with <strong>{completeModalSession.student_name || "Student"}</strong> ({completeModalSession.learning_need_title || "Tutoring"}). Actual duration will be logged.
            </p>

            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "6px" }}>
                Session Summary / Completion Note (Optional)
              </label>
              <textarea
                rows={4}
                className="form-input"
                value={completionNote}
                onChange={(e) => setCompletionNote(e.target.value)}
                placeholder="Topics covered, student progress, homework assigned..."
                style={{ width: "100%", fontSize: "13px", resize: "vertical" }}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCompleteModalSession(null)}
                disabled={sessionActionLoadingId === completeModalSession.id}
                style={{ padding: "8px 16px", fontSize: "13px" }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => handleCompleteSession(completeModalSession.id, completionNote)}
                disabled={sessionActionLoadingId === completeModalSession.id}
                style={{ padding: "8px 18px", fontSize: "13px", background: "var(--success-color)", borderColor: "var(--success-color)" }}
              >
                {sessionActionLoadingId === completeModalSession.id ? "Completing..." : "Confirm Completion"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
