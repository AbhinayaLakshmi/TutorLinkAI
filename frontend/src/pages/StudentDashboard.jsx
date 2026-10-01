import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api, { API_BASE_URL } from "../services/api";
import { logout } from "../services/auth";
import ProductionTutorDetailModal from "../components/ProductionTutorDetailModal";
import ReviewModal from "../components/ReviewModal";
import "../onboarding.css";

const LANGUAGES_OPTIONS = ["English", "Spanish", "French", "German", "Mandarin", "Hindi", "Arabic", "Japanese"];
const BOARDS = ["CBSE", "Matriculation", "ICSE", "State Board", "Other"];
const GRADES = Array.from({ length: 12 }, (_, i) => `Class ${i + 1}`);

export default function StudentDashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [activeTab, setActiveTab] = useState("learning_needs"); // "learning_needs" | "profile"
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isEditingProfile, setIsEditingProfile] = useState(false);

  // Profile editable state
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

  // Learning Needs state
  const [learningNeeds, setLearningNeeds] = useState([]);
  const [loadingNeeds, setLoadingNeeds] = useState(false);
  const [selectedNeedId, setSelectedNeedId] = useState(null);

  // Bookings state
  const [bookings, setBookings] = useState([]);
  const [loadingBookings, setLoadingBookings] = useState(false);
  const [cancellingBookingId, setCancellingBookingId] = useState(null);

  // Sessions state
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [cancellingSessionId, setCancellingSessionId] = useState(null);
  const [sessionReviews, setSessionReviews] = useState({});
  const [reviewModalSession, setReviewModalSession] = useState(null);

  // Create / Edit Learning Need Modal state
  const [isNeedModalOpen, setIsNeedModalOpen] = useState(false);
  const [editingNeed, setEditingNeed] = useState(null); // null when creating, object when editing
  const [needTitle, setNeedTitle] = useState("");
  const [needSubjectInput, setNeedSubjectInput] = useState("");
  const [needSubjects, setNeedSubjects] = useState([]);
  const [needTopicInput, setNeedTopicInput] = useState("");
  const [needTopics, setNeedTopics] = useState([]);
  const [needGoals, setNeedGoals] = useState("");
  const [needCharacteristics, setNeedCharacteristics] = useState("");
  const [needAvailability, setNeedAvailability] = useState("");
  const [needBudgetMin, setNeedBudgetMin] = useState("");
  const [needBudgetMax, setNeedBudgetMax] = useState("");
  const [needIsActive, setNeedIsActive] = useState(false);
  const [needFormError, setNeedFormError] = useState("");
  const [submittingNeed, setSubmittingNeed] = useState(false);

  // Recommendations state
  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [recommendationsError, setRecommendationsError] = useState("");
  const [hasFetchedRecommendations, setHasFetchedRecommendations] = useState(false);
  const [activeRecommendationForModal, setActiveRecommendationForModal] = useState(null);

  // Fetch Student Profile
  const loadProfile = useCallback(() => {
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
      })
      .catch((err) => {
        if (err.response?.status === 401) {
          logout();
          navigate("/login");
        } else {
          setError("Failed to load student dashboard details.");
        }
      });
  }, [navigate]);

  // Fetch Learning Needs from Backend
  const loadLearningNeeds = useCallback(() => {
    setLoadingNeeds(true);
    api.get("/api/onboarding/student/me/learning-needs")
      .then((res) => {
        const needs = res.data || [];
        setLearningNeeds(needs);
        setLoadingNeeds(false);

        // Auto-select active need if available, else first need
        const active = needs.find((n) => n.is_active);
        if (active) {
          setSelectedNeedId((prev) => prev || active.id);
        } else if (needs.length > 0) {
          setSelectedNeedId((prev) => prev || needs[0].id);
        }
      })
      .catch((err) => {
        console.error("Failed to load learning needs:", err);
        setLoadingNeeds(false);
      });
  }, []);

  // Fetch Bookings from Backend
  const loadBookings = useCallback(() => {
    setLoadingBookings(true);
    api.get("/api/booking/student")
      .then((res) => {
        setBookings(res.data || []);
        setLoadingBookings(false);
      })
      .catch((err) => {
        console.error("Failed to load student bookings:", err);
        setLoadingBookings(false);
      });
  }, []);

  const handleCancelBooking = async (bookingId) => {
    if (!window.confirm("Are you sure you want to cancel this booking?")) return;
    setCancellingBookingId(bookingId);
    setError("");
    setSuccess("");
    try {
      await api.post(`/api/booking/${bookingId}/cancel`, {
        reason: "Cancelled by student"
      });
      setSuccess("Booking cancelled successfully.");
      loadBookings();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to cancel booking.");
    } finally {
      setCancellingBookingId(null);
    }
  };

  // Fetch Sessions from Backend
  const loadSessions = useCallback(() => {
    setLoadingSessions(true);
    api.get("/api/session/student")
      .then(async (res) => {
        const sessList = res.data || [];
        setSessions(sessList);
        setLoadingSessions(false);

        // Fetch reviews for completed sessions
        const completedSessions = sessList.filter((s) => s.status === "COMPLETED");
        const revMap = {};
        for (const s of completedSessions) {
          try {
            const rRes = await api.get(`/api/reviews/session/${s.id}`);
            if (rRes.data) {
              revMap[s.id] = rRes.data;
            }
          } catch (e) {
            // No review yet for this session
          }
        }
        setSessionReviews((prev) => ({ ...prev, ...revMap }));
      })
      .catch((err) => {
        console.error("Failed to load student sessions:", err);
        setLoadingSessions(false);
      });
  }, []);

  const handleReviewSuccess = (sessionId, reviewData) => {
    setSessionReviews((prev) => ({
      ...prev,
      [sessionId]: reviewData,
    }));
    setSuccess("Thank you! Your review and rating have been submitted.");
    setTimeout(() => setSuccess(""), 4000);
  };

  const handleCancelSession = async (sessionId) => {
    if (!window.confirm("Are you sure you want to cancel this scheduled session?")) return;
    setCancellingSessionId(sessionId);
    setError("");
    setSuccess("");
    try {
      await api.post(`/api/session/${sessionId}/cancel`, {
        reason: "Cancelled by student"
      });
      setSuccess("Session cancelled successfully.");
      loadSessions();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to cancel session.");
    } finally {
      setCancellingSessionId(null);
    }
  };

  useEffect(() => {
    loadProfile();
    loadLearningNeeds();
    loadBookings();
    loadSessions();
  }, [loadProfile, loadLearningNeeds, loadBookings, loadSessions]);

  // Fetch Real AI Recommendations for a specific learning need
  const fetchRecommendations = (learningNeedIdToUse) => {
    const targetId = learningNeedIdToUse || selectedNeedId;
    setLoadingRecommendations(true);
    setRecommendationsError("");
    setRecommendations([]);

    const queryParam = targetId ? `?learning_need_id=${encodeURIComponent(targetId)}` : "";
    
    api.get(`/api/matching/recommendations${queryParam}`)
      .then((res) => {
        setRecommendations(res.data || []);
        setLoadingRecommendations(false);
        setHasFetchedRecommendations(true);
      })
      .catch((err) => {
        console.error("Failed to fetch recommendations:", err);
        const detail = err.response?.data?.detail;
        if (err.response?.status === 404) {
          setRecommendationsError("Selected learning need not found. Please select or create an active learning need.");
        } else if (err.response?.status === 503 || err.response?.status === 502) {
          setRecommendationsError("We couldn't load recommendations right now. Please try again.");
        } else {
          setRecommendationsError(detail || "We couldn't load recommendations right now. Please try again.");
        }
        setLoadingRecommendations(false);
        setHasFetchedRecommendations(true);
      });
  };

  // Open modal to create new learning need
  const handleOpenCreateModal = () => {
    setEditingNeed(null);
    setNeedTitle("");
    setNeedSubjectInput("");
    setNeedSubjects([]);
    setNeedTopicInput("");
    setNeedTopics([]);
    setNeedGoals("");
    setNeedCharacteristics("");
    setNeedAvailability("");
    setNeedBudgetMin("");
    setNeedBudgetMax("");
    setNeedIsActive(learningNeeds.length === 0); // Active by default if first need
    setNeedFormError("");
    setIsNeedModalOpen(true);
  };

  // Open modal to edit existing learning need
  const handleOpenEditModal = (need) => {
    setEditingNeed(need);
    setNeedTitle(need.title || "");
    setNeedSubjectInput("");
    setNeedSubjects(need.subjects || []);
    setNeedTopicInput("");
    setNeedTopics(need.topics || []);
    setNeedGoals(need.learning_goals || "");
    setNeedCharacteristics(need.preferred_tutor_characteristics || "");
    setNeedAvailability(need.preferred_availability || "");
    setNeedBudgetMin(need.budget_min !== null && need.budget_min !== undefined ? need.budget_min : "");
    setNeedBudgetMax(need.budget_max !== null && need.budget_max !== undefined ? need.budget_max : "");
    setNeedIsActive(Boolean(need.is_active));
    setNeedFormError("");
    setIsNeedModalOpen(true);
  };

  // Subject tag handlers inside modal
  const addNeedSubject = () => {
    const val = needSubjectInput.trim();
    if (val && !needSubjects.includes(val)) {
      setNeedSubjects([...needSubjects, val]);
      setNeedSubjectInput("");
    }
  };
  const removeNeedSubject = (sub) => setNeedSubjects(needSubjects.filter((s) => s !== sub));

  // Topic tag handlers inside modal
  const addNeedTopic = () => {
    const val = needTopicInput.trim();
    if (val && !needTopics.includes(val)) {
      setNeedTopics([...needTopics, val]);
      setNeedTopicInput("");
    }
  };
  const removeNeedTopic = (top) => setNeedTopics(needTopics.filter((t) => t !== top));

  // Submit Create or Edit Learning Need
  const handleSaveLearningNeed = async (e) => {
    e.preventDefault();
    setNeedFormError("");

    if (!needTitle.trim()) {
      setNeedFormError("Title is required.");
      return;
    }
    if (needSubjects.length === 0) {
      setNeedFormError("Please add at least one subject.");
      return;
    }

    const minVal = needBudgetMin !== "" ? parseFloat(needBudgetMin) : null;
    const maxVal = needBudgetMax !== "" ? parseFloat(needBudgetMax) : null;

    if (minVal !== null && isNaN(minVal)) {
      setNeedFormError("Minimum budget must be a valid number.");
      return;
    }
    if (maxVal !== null && isNaN(maxVal)) {
      setNeedFormError("Maximum budget must be a valid number.");
      return;
    }
    if (minVal !== null && minVal < 0) {
      setNeedFormError("Minimum budget cannot be negative.");
      return;
    }
    if (maxVal !== null && maxVal < 0) {
      setNeedFormError("Maximum budget cannot be negative.");
      return;
    }
    if (minVal !== null && maxVal !== null && maxVal < minVal) {
      setNeedFormError("Maximum budget cannot be less than minimum budget.");
      return;
    }

    setSubmittingNeed(true);
    const payload = {
      title: needTitle.trim(),
      subjects: needSubjects,
      topics: needTopics,
      learning_goals: needGoals.trim() || null,
      preferred_tutor_characteristics: needCharacteristics.trim() || null,
      preferred_availability: needAvailability.trim() || null,
      budget_min: minVal,
      budget_max: maxVal,
      is_active: needIsActive,
    };

    try {
      if (editingNeed) {
        // Edit existing learning need
        await api.put(`/api/onboarding/student/me/learning-needs/${editingNeed.id}`, payload);
        setSuccess("Learning need updated successfully!");
      } else {
        // Create new learning need
        const created = await api.post("/api/onboarding/student/me/learning-needs", payload);
        if (created.data?.id) {
          setSelectedNeedId(created.data.id);
        }
        setSuccess("Learning need created successfully!");
      }
      setIsNeedModalOpen(false);
      loadLearningNeeds();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setNeedFormError(err.response?.data?.detail || "Failed to save learning need.");
    } finally {
      setSubmittingNeed(false);
    }
  };

  // Set Active Learning Need
  const handleActivateLearningNeed = async (needId) => {
    setError("");
    try {
      await api.post(`/api/onboarding/student/me/learning-needs/${needId}/activate`);
      setSuccess("Active learning need updated!");
      setSelectedNeedId(needId);
      loadLearningNeeds();
      // Automatically refresh recommendations for the newly activated need
      fetchRecommendations(needId);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to activate learning need.");
    }
  };

  // Delete Learning Need
  const handleDeleteLearningNeed = async (needId) => {
    if (!window.confirm("Are you sure you want to delete this learning need? This action cannot be undone.")) {
      return;
    }

    setError("");
    try {
      await api.delete(`/api/onboarding/student/me/learning-needs/${needId}`);
      setSuccess("Learning need deleted.");
      if (selectedNeedId === needId) {
        setSelectedNeedId(null);
        setRecommendations([]);
        setHasFetchedRecommendations(false);
      }
      loadLearningNeeds();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete learning need.");
    }
  };

  // Profile Save
  const handleSaveProfile = async (e) => {
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
      });
      setProfile(res.data);
      setSuccess("Profile updated successfully!");
      setIsEditingProfile(false);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update profile.");
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const toggleLanguage = (lang) => {
    if (preferredTutorLanguages.includes(lang)) {
      setPreferredTutorLanguages(preferredTutorLanguages.filter((l) => l !== lang));
    } else {
      setPreferredTutorLanguages([...preferredTutorLanguages, lang]);
    }
  };

  if (!user || !profile) {
    return <div className="onboard-container"><p>Loading student dashboard...</p></div>;
  }

  const selectedNeed = learningNeeds.find((n) => n.id === selectedNeedId);

  return (
    <div className="onboard-container" style={{ alignItems: "stretch", maxWidth: "1140px", margin: "0 auto" }}>
      <div className="dashboard-grid" style={{ gridTemplateColumns: "260px 1fr" }}>
        
        {/* Sidebar */}
        <div className="dashboard-sidebar">
          <div className="sidebar-avatar">🎓</div>
          <div className="sidebar-name">{user.full_name}</div>
          <div className="sidebar-role">Student</div>

          <ul className="sidebar-menu">
            <li
              className={`sidebar-menu-item ${activeTab === "learning_needs" ? "active" : ""}`}
              onClick={() => { setActiveTab("learning_needs"); setIsEditingProfile(false); }}
            >
              📚 Learning Needs & Tutors
            </li>
            <li
              className={`sidebar-menu-item ${activeTab === "bookings" ? "active" : ""}`}
              onClick={() => { setActiveTab("bookings"); setIsEditingProfile(false); loadBookings(); }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                <span>📅 My Bookings</span>
                {bookings.filter(b => b.status === "PENDING" || b.status === "CONFIRMED").length > 0 && (
                  <span style={{ background: "var(--primary-color)", color: "#fff", padding: "1px 6px", borderRadius: "10px", fontSize: "11px", fontWeight: "bold" }}>
                    {bookings.filter(b => b.status === "PENDING" || b.status === "CONFIRMED").length}
                  </span>
                )}
              </div>
            </li>
            <li
              className={`sidebar-menu-item ${activeTab === "sessions" ? "active" : ""}`}
              onClick={() => { setActiveTab("sessions"); setIsEditingProfile(false); loadSessions(); }}
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
            <li
              className={`sidebar-menu-item ${activeTab === "profile" ? "active" : ""}`}
              onClick={() => { setActiveTab("profile"); }}
            >
              👤 My Profile
            </li>
            <li
              className="sidebar-menu-item"
              style={{ color: "var(--primary-color)", marginTop: "12px", borderTop: "1px solid var(--border-color)", paddingTop: "12px" }}
              onClick={() => navigate("/demo/recommendations")}
            >
              🚀 Review Demo Mode
            </li>
            <li
              className="sidebar-menu-item"
              style={{ color: "var(--error-color)" }}
              onClick={handleLogout}
            >
              Log Out
            </li>
          </ul>
        </div>

        {/* Main Content Area */}
        <div className="dashboard-content">
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          {/* TAB 1: LEARNING NEEDS & TUTOR MATCHING */}
          {activeTab === "learning_needs" && (
            <div>
              {/* Header with Title and Create Button */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
                <div>
                  <h2 style={{ margin: "0 0 4px 0", fontSize: "22px" }}>My Learning Needs</h2>
                  <p style={{ margin: 0, fontSize: "14px", color: "var(--text-muted)" }}>
                    Manage specific subjects and goals to get targeted AI tutor recommendations.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleOpenCreateModal}
                  className="btn btn-primary"
                  style={{ padding: "8px 18px", fontSize: "14px", display: "flex", alignItems: "center", gap: "6px" }}
                >
                  <span>+</span>
                  <span>New Learning Need</span>
                </button>
              </div>

              {/* Learning Needs List */}
              {loadingNeeds ? (
                <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)" }}>
                  Loading your learning needs...
                </div>
              ) : learningNeeds.length === 0 ? (
                <div
                  style={{
                    textAlign: "center",
                    padding: "36px 20px",
                    background: "var(--bg-color)",
                    border: "1px dashed var(--border-color)",
                    borderRadius: "8px",
                    marginBottom: "30px"
                  }}
                >
                  <p style={{ margin: "0 0 14px 0", color: "var(--text-muted)", fontSize: "14px" }}>
                    You have not created any learning needs yet.
                  </p>
                  <button
                    type="button"
                    onClick={handleOpenCreateModal}
                    className="btn btn-primary"
                    style={{ padding: "8px 18px", fontSize: "13px" }}
                  >
                    Create Your First Learning Need
                  </button>
                </div>
              ) : (
                <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "16px", marginBottom: "32px" }}>
                  {learningNeeds.map((need) => {
                    const isSelected = need.id === selectedNeedId;
                    return (
                      <div
                        key={need.id}
                        style={{
                          background: isSelected ? "var(--card-bg)" : "var(--card-bg)",
                          border: isSelected ? "2px solid var(--primary-color)" : "1px solid var(--border-color)",
                          borderRadius: "10px",
                          padding: "18px 22px",
                          boxShadow: isSelected ? "0 4px 12px rgba(59, 130, 246, 0.08)" : "none",
                          transition: "all 0.2s ease"
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px", flexWrap: "wrap", marginBottom: "10px" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                            <h3 style={{ margin: 0, fontSize: "17px", fontWeight: "700", color: "var(--text-h)" }}>
                              {need.title}
                            </h3>
                            {need.is_active ? (
                              <span
                                style={{
                                  background: "rgba(16, 185, 129, 0.15)",
                                  color: "var(--success-color)",
                                  border: "1px solid rgba(16, 185, 129, 0.3)",
                                  padding: "2px 10px",
                                  borderRadius: "12px",
                                  fontSize: "11px",
                                  fontWeight: "700"
                                }}
                              >
                                Active
                              </span>
                            ) : (
                              <span
                                style={{
                                  background: "var(--border-color)",
                                  color: "var(--text-muted)",
                                  padding: "2px 8px",
                                  borderRadius: "12px",
                                  fontSize: "11px"
                                }}
                              >
                                Inactive
                              </span>
                            )}
                          </div>

                          {/* Action buttons */}
                          <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                            {!need.is_active && (
                              <button
                                type="button"
                                onClick={() => handleActivateLearningNeed(need.id)}
                                className="btn btn-secondary"
                                style={{ padding: "4px 10px", fontSize: "12px" }}
                                title="Set as default active need"
                              >
                                Set Active
                              </button>
                            )}

                            <button
                              type="button"
                              onClick={() => {
                                setSelectedNeedId(need.id);
                                fetchRecommendations(need.id);
                              }}
                              className={`btn ${isSelected ? "btn-primary" : "btn-secondary"}`}
                              style={{ padding: "4px 12px", fontSize: "12px" }}
                            >
                              🔍 Find Tutors
                            </button>

                            <button
                              type="button"
                              onClick={() => handleOpenEditModal(need)}
                              className="btn btn-secondary"
                              style={{ padding: "4px 10px", fontSize: "12px" }}
                              title="Edit learning need"
                            >
                              ✏️ Edit
                            </button>

                            <button
                              type="button"
                              onClick={() => handleDeleteLearningNeed(need.id)}
                              className="btn btn-secondary"
                              style={{ padding: "4px 8px", fontSize: "12px", color: "var(--error-color)" }}
                              title="Delete learning need"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>

                        {/* Subjects & Topics */}
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "10px" }}>
                          {need.subjects?.map((sub) => (
                            <span
                              key={sub}
                              style={{
                                fontSize: "11px",
                                background: "var(--primary-color)",
                                color: "#ffffff",
                                padding: "2px 8px",
                                borderRadius: "4px",
                                fontWeight: "500"
                              }}
                            >
                              {sub}
                            </span>
                          ))}
                          {need.topics?.map((top) => (
                            <span
                              key={top}
                              style={{
                                fontSize: "11px",
                                background: "var(--border-color)",
                                color: "var(--text-color)",
                                padding: "2px 8px",
                                borderRadius: "4px"
                              }}
                            >
                              #{top}
                            </span>
                          ))}
                        </div>

                        {/* Details */}
                        {need.learning_goals && (
                          <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px" }}>
                            <strong>Goals:</strong> {need.learning_goals}
                          </div>
                        )}
                        {((need.budget_min !== null && need.budget_min !== undefined) || (need.budget_max !== null && need.budget_max !== undefined)) && (
                          <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px" }}>
                            <strong>Hourly Budget:</strong> {
                              need.budget_min !== null && need.budget_min !== undefined && need.budget_max !== null && need.budget_max !== undefined
                                ? `₹${need.budget_min} – ₹${need.budget_max}/hr`
                                : need.budget_min !== null && need.budget_min !== undefined
                                ? `Min ₹${need.budget_min}/hr`
                                : `Up to ₹${need.budget_max}/hr`
                            }
                          </div>
                        )}
                        {need.preferred_availability && (
                          <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "4px" }}>
                            <strong>Preferred Schedule:</strong> {need.preferred_availability}
                          </div>
                        )}
                        {need.preferred_tutor_characteristics && (
                          <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                            <strong>Tutor Style:</strong> {need.preferred_tutor_characteristics}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* RECOMMENDATIONS SECTION */}
              <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "26px", marginTop: "10px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
                  <div>
                    <h3 style={{ margin: "0 0 4px 0", fontSize: "18px", fontWeight: "700" }}>
                      AI Recommended Tutors
                    </h3>
                    {selectedNeed ? (
                      <p style={{ margin: 0, fontSize: "13px", color: "var(--text-muted)" }}>
                        Matching candidates for: <strong style={{ color: "var(--text-h)" }}>{selectedNeed.title}</strong> ({selectedNeed.subjects?.join(", ")})
                      </p>
                    ) : (
                      <p style={{ margin: 0, fontSize: "13px", color: "var(--text-muted)" }}>
                        Select a learning need above to discover personalized AI recommendations.
                      </p>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => fetchRecommendations()}
                    className="btn btn-primary"
                    disabled={loadingRecommendations || !selectedNeedId}
                    style={{ padding: "8px 20px", fontSize: "13px" }}
                  >
                    {loadingRecommendations ? "Finding tutors..." : "Find Tutors"}
                  </button>
                </div>

                {/* State Handling */}
                {recommendationsError && (
                  <div className="alert alert-error">{recommendationsError}</div>
                )}

                {loadingRecommendations && (
                  <div
                    style={{
                      textAlign: "center",
                      padding: "48px 20px",
                      background: "var(--bg-color)",
                      border: "1px dashed var(--border-color)",
                      borderRadius: "8px",
                      color: "var(--primary-color)",
                      fontSize: "14px",
                      fontWeight: "500"
                    }}
                  >
                    Finding tutors for your learning need...
                  </div>
                )}

                {!loadingRecommendations && hasFetchedRecommendations && recommendations.length === 0 && !recommendationsError && (
                  <div
                    style={{
                      textAlign: "center",
                      padding: "48px 20px",
                      background: "var(--bg-color)",
                      border: "1px dashed var(--border-color)",
                      borderRadius: "8px",
                      color: "var(--text-muted)",
                      fontSize: "14px"
                    }}
                  >
                    No suitable tutors were found for this learning need.
                  </div>
                )}

                {!loadingRecommendations && !hasFetchedRecommendations && (
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
                    No recommendations loaded yet. Click <strong>"Find Tutors"</strong> to view real matching candidates.
                  </div>
                )}

                {/* Real Recommendation Cards Grid */}
                {!loadingRecommendations && recommendations.length > 0 && (
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
                      gap: "20px",
                      marginTop: "16px"
                    }}
                  >
                    {recommendations.map((rec) => (
                      <div
                        key={rec.id}
                        style={{
                          background: "var(--card-bg)",
                          border: "1px solid var(--border-color)",
                          borderRadius: "10px",
                          padding: "20px",
                          display: "flex",
                          flexDirection: "column",
                          justifyContent: "space-between",
                          boxShadow: "0 2px 6px rgba(0,0,0,0.02)",
                          position: "relative"
                        }}
                      >
                        <div>
                          {/* Card Header: Avatar / Name / Rating / Match % */}
                          <div style={{ display: "flex", gap: "12px", marginBottom: "14px", alignItems: "center" }}>
                            <div
                              style={{
                                width: "48px",
                                height: "48px",
                                borderRadius: "50%",
                                background: "var(--border-color)",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                overflow: "hidden",
                                fontSize: "18px",
                                fontWeight: "600",
                                color: "var(--text-muted)",
                                border: "2px solid var(--border-color)",
                                flexShrink: 0
                              }}
                            >
                              {rec.profile_picture_path ? (
                                <img
                                  src={`${API_BASE_URL}${rec.profile_picture_path}`}
                                  alt={rec.name}
                                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                                  onError={(e) => {
                                    e.target.style.display = "none";
                                    e.target.parentNode.innerText = rec.name.charAt(0);
                                  }}
                                />
                              ) : (
                                rec.name.charAt(0)
                              )}
                            </div>

                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div
                                style={{
                                  fontWeight: "700",
                                  fontSize: "15px",
                                  color: "var(--text-h)",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis"
                                }}
                              >
                                {rec.name}
                              </div>
                              <div style={{ fontSize: "12px", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "8px", marginTop: "2px" }}>
                                <span style={{ color: "#eab308" }}>
                                  ★ {rec.rating ? rec.rating.toFixed(1) : "4.5"}
                                </span>
                                <span>📍 {rec.location || "Online"}</span>
                              </div>
                            </div>

                            <div
                              style={{
                                background:
                                  rec.overall_percentage >= 80
                                    ? "rgba(16, 185, 129, 0.12)"
                                    : "rgba(59, 130, 246, 0.12)",
                                color:
                                  rec.overall_percentage >= 80
                                    ? "var(--success-color)"
                                    : "var(--primary-color)",
                                padding: "4px 10px",
                                borderRadius: "16px",
                                fontSize: "11px",
                                fontWeight: "700",
                                border:
                                  rec.overall_percentage >= 80
                                    ? "1px solid rgba(16, 185, 129, 0.25)"
                                    : "1px solid rgba(59, 130, 246, 0.25)"
                              }}
                            >
                              {rec.overall_percentage}% Match
                            </div>
                          </div>

                          {/* Subjects & Matched Topics Tags */}
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "12px" }}>
                            {rec.subjects?.map((sub) => (
                              <span
                                key={sub}
                                style={{
                                  fontSize: "11px",
                                  background: "var(--border-color)",
                                  color: "var(--text-color)",
                                  padding: "2px 7px",
                                  borderRadius: "4px",
                                  fontWeight: "500"
                                }}
                              >
                                {sub}
                              </span>
                            ))}
                            {rec.matched_topics?.map((top) => (
                              <span
                                key={top}
                                style={{
                                  fontSize: "10px",
                                  background: "rgba(16, 185, 129, 0.12)",
                                  color: "var(--success-color)",
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                  fontWeight: "600"
                                }}
                              >
                                ✓ {top}
                              </span>
                            ))}
                          </div>

                          {/* Explanation Summary / Bio snippet */}
                          <p
                            style={{
                              fontSize: "12px",
                              color: "var(--text-muted)",
                              marginBottom: "14px",
                              lineHeight: "1.4",
                              display: "-webkit-box",
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: "vertical",
                              overflow: "hidden"
                            }}
                          >
                            {rec.explanation_summary || rec.bio || "No summary provided."}
                          </p>

                          {/* Match Breakdown metrics */}
                          {rec.breakdown && (
                            <div
                              style={{
                                background: "var(--bg-color)",
                                borderRadius: "6px",
                                padding: "10px 12px",
                                fontSize: "11px",
                                color: "var(--text-muted)",
                                marginBottom: "16px",
                                border: "1px solid var(--border-color)"
                              }}
                            >
                              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                                <span>Subject Match:</span>
                                <span style={{ fontWeight: "600", color: "var(--text-h)" }}>
                                  {Math.round((rec.breakdown.subject_score || 0) * 100)}%
                                </span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                                <span>Budget Match:</span>
                                <span style={{ fontWeight: "600", color: "var(--text-h)" }}>
                                  {Math.round((rec.breakdown.fee_score || 0) * 100)}%
                                </span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span>Schedule Match:</span>
                                <span style={{ fontWeight: "600", color: "var(--text-h)" }}>
                                  {Math.round((rec.breakdown.time_score || 0) * 100)}%
                                </span>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Card Footer: Rate & Buttons */}
                        <div
                          style={{
                            borderTop: "1px solid var(--border-color)",
                            paddingTop: "14px",
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            gap: "8px",
                            flexWrap: "wrap"
                          }}
                        >
                          <div>
                            <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>
                              Rate
                            </div>
                            <div style={{ fontSize: "15px", fontWeight: "700", color: "var(--text-h)" }}>
                              ₹{rec.hourly_rate} / hr
                            </div>
                          </div>

                          <div style={{ display: "flex", gap: "6px" }}>
                            <button
                              type="button"
                              onClick={() => setActiveRecommendationForModal(rec)}
                              className="btn btn-secondary"
                              style={{ padding: "6px 12px", fontSize: "12px" }}
                            >
                              View Details
                            </button>

                            <button
                              type="button"
                              onClick={() => setActiveRecommendationForModal(rec)}
                              className="btn btn-primary"
                              style={{ padding: "6px 12px", fontSize: "12px" }}
                            >
                              Book Tutor
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB: MY BOOKINGS */}
          {activeTab === "bookings" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
                <div>
                  <h2 style={{ margin: "0 0 4px 0", fontSize: "22px" }}>My Bookings</h2>
                  <p style={{ margin: 0, fontSize: "14px", color: "var(--text-muted)" }}>
                    Track your requested sessions, confirmed appointments, and status updates.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={loadBookings}
                  className="btn btn-secondary"
                  disabled={loadingBookings}
                  style={{ padding: "6px 14px", fontSize: "13px" }}
                >
                  {loadingBookings ? "Refreshing..." : "🔄 Refresh"}
                </button>
              </div>

              {loadingBookings && (
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
                  Loading your bookings...
                </div>
              )}

              {!loadingBookings && bookings.length === 0 && (
                <div
                  style={{
                    textAlign: "center",
                    padding: "48px 20px",
                    background: "var(--bg-color)",
                    border: "1px dashed var(--border-color)",
                    borderRadius: "8px"
                  }}
                >
                  <div style={{ fontSize: "36px", marginBottom: "12px" }}>📅</div>
                  <h3 style={{ margin: "0 0 8px 0", fontSize: "18px" }}>No Bookings Yet</h3>
                  <p style={{ margin: "0 0 16px 0", fontSize: "14px", color: "var(--text-muted)" }}>
                    You haven't requested any tutoring sessions yet. Browse AI recommended tutors to book a session!
                  </p>
                  <button
                    type="button"
                    onClick={() => setActiveTab("learning_needs")}
                    className="btn btn-primary"
                    style={{ padding: "8px 18px", fontSize: "14px" }}
                  >
                    Find Tutors
                  </button>
                </div>
              )}

              {!loadingBookings && bookings.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  {bookings.map((booking) => {
                    const statusConfig = {
                      PENDING: {
                        label: "Pending Tutor Confirmation",
                        bg: "rgba(245, 158, 11, 0.12)",
                        color: "#d97706",
                        border: "1px solid rgba(245, 158, 11, 0.3)"
                      },
                      CONFIRMED: {
                        label: "Confirmed",
                        bg: "rgba(16, 185, 129, 0.12)",
                        color: "var(--success-color)",
                        border: "1px solid rgba(16, 185, 129, 0.3)"
                      },
                      REJECTED: {
                        label: "Declined",
                        bg: "rgba(239, 68, 68, 0.12)",
                        color: "var(--error-color)",
                        border: "1px solid rgba(239, 68, 68, 0.3)"
                      },
                      CANCELLED: {
                        label: "Cancelled",
                        bg: "var(--border-color)",
                        color: "var(--text-muted)",
                        border: "1px solid var(--border-color)"
                      }
                    }[booking.status] || {
                      label: booking.status,
                      bg: "var(--border-color)",
                      color: "var(--text-color)",
                      border: "1px solid var(--border-color)"
                    };

                    const canCancel = booking.status === "PENDING" || booking.status === "CONFIRMED";

                    return (
                      <div
                        key={booking.id}
                        style={{
                          background: "var(--card-bg)",
                          border: "1px solid var(--border-color)",
                          borderRadius: "10px",
                          padding: "18px 20px",
                          boxShadow: "0 2px 6px rgba(0,0,0,0.02)"
                        }}
                      >
                        {/* Header: Tutor + Status Badge */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
                          <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                              <span style={{ fontSize: "20px" }}>👨‍🏫</span>
                              <div>
                                <h4 style={{ margin: 0, fontSize: "16px", fontWeight: "700" }}>
                                  {booking.tutor_name || "Tutor"}
                                </h4>
                                {booking.learning_need_title && (
                                  <div style={{ fontSize: "12px", color: "var(--primary-color)", marginTop: "2px", fontWeight: "500" }}>
                                    🎯 For: {booking.learning_need_title}
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
                              📅 {booking.scheduled_date}
                            </div>
                          </div>

                          <div>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                              Time & Duration
                            </div>
                            <div style={{ fontWeight: "600", color: "var(--text-h)" }}>
                              ⏰ {booking.start_time} ({booking.duration_minutes} mins)
                            </div>
                          </div>

                          <div>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                              Rate Snapshot
                            </div>
                            <div style={{ fontWeight: "600", color: "var(--text-h)" }}>
                              ₹{booking.hourly_rate} / hr
                            </div>
                          </div>

                          <div>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>
                              Est. Total Amount
                            </div>
                            <div style={{ fontWeight: "700", color: "var(--primary-color)" }}>
                              ₹{booking.total_amount ? Number(booking.total_amount).toFixed(2) : (booking.hourly_rate * (booking.duration_minutes / 60)).toFixed(2)}
                            </div>
                          </div>
                        </div>

                        {/* Student Note */}
                        {booking.student_message && (
                          <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "12px", background: "rgba(0,0,0,0.02)", padding: "8px 12px", borderRadius: "4px" }}>
                            <strong>Your Message:</strong> {booking.student_message}
                          </div>
                        )}

                        {/* Actions Footer */}
                        {canCancel && (
                          <div style={{ display: "flex", justifyContent: "flex-end", borderTop: "1px solid var(--border-color)", paddingTop: "10px", marginTop: "4px" }}>
                            <button
                              type="button"
                              onClick={() => handleCancelBooking(booking.id)}
                              className="btn btn-secondary"
                              disabled={cancellingBookingId === booking.id}
                              style={{ padding: "4px 12px", fontSize: "12px", color: "var(--error-color)", borderColor: "rgba(239, 68, 68, 0.3)" }}
                            >
                              {cancellingBookingId === booking.id ? "Cancelling..." : "Cancel Booking"}
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

          {/* TAB: MY SESSIONS */}
          {activeTab === "sessions" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
                <div>
                  <h2 style={{ margin: "0 0 4px 0", fontSize: "22px" }}>My Sessions</h2>
                  <p style={{ margin: 0, fontSize: "14px", color: "var(--text-muted)" }}>
                    Track your upcoming scheduled classes, active sessions, and completed learning history.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={loadSessions}
                  className="btn btn-secondary"
                  disabled={loadingSessions}
                  style={{ padding: "6px 14px", fontSize: "13px" }}
                >
                  {loadingSessions ? "Refreshing..." : "🔄 Refresh"}
                </button>
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
                  Loading your sessions...
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
                  <p style={{ margin: "0 0 16px 0", fontSize: "14px", color: "var(--text-muted)" }}>
                    Once a tutor accepts your booking request, a confirmed session will appear here.
                  </p>
                  <button
                    type="button"
                    onClick={() => setActiveTab("bookings")}
                    className="btn btn-primary"
                    style={{ padding: "8px 18px", fontSize: "14px" }}
                  >
                    View My Bookings
                  </button>
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
                    const isCompleted = session.status === "COMPLETED";
                    const isInProgress = session.status === "IN_PROGRESS";

                    return (
                      <div
                        key={session.id}
                        style={{
                          background: "var(--card-bg)",
                          border: isInProgress ? "1px solid var(--success-color)" : "1px solid var(--border-color)",
                          borderRadius: "10px",
                          padding: "18px 20px",
                          boxShadow: isInProgress ? "0 2px 10px rgba(16, 185, 129, 0.12)" : "0 2px 6px rgba(0,0,0,0.02)"
                        }}
                      >
                        {/* Header: Tutor + Status Badge */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
                          <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                              <span style={{ fontSize: "22px" }}>👨‍🏫</span>
                              <div>
                                <h4 style={{ margin: 0, fontSize: "16px", fontWeight: "700" }}>
                                  {session.tutor_name || "Tutor"}
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
                            <strong style={{ color: "var(--text-h)" }}>Tutor Summary:</strong> {session.completion_note}
                          </div>
                        )}

                        {/* Cancellation Reason */}
                        {session.status === "CANCELLED" && session.cancellation_reason && (
                          <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "10px", background: "rgba(239, 68, 68, 0.05)", padding: "8px 12px", borderRadius: "4px" }}>
                            <strong>Cancellation Reason:</strong> {session.cancellation_reason}
                          </div>
                        )}

                        {/* Review Status or Action for Completed Sessions */}
                        {isCompleted && (
                          <div style={{ marginTop: "12px", borderTop: "1px solid var(--border-color)", paddingTop: "12px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "8px" }}>
                            {sessionReviews[session.id] ? (
                              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                                <span style={{ fontSize: "12px", fontWeight: "700", color: "#16a34a", background: "rgba(22, 163, 74, 0.1)", padding: "3px 10px", borderRadius: "12px", border: "1px solid rgba(22, 163, 74, 0.25)" }}>
                                  ✓ Reviewed
                                </span>
                                <span style={{ fontSize: "14px", color: "#d97706", fontWeight: "700" }}>
                                  {"★".repeat(sessionReviews[session.id].rating)}{"☆".repeat(5 - sessionReviews[session.id].rating)} ({sessionReviews[session.id].rating}/5)
                                </span>
                                {sessionReviews[session.id].review_text && (
                                  <span style={{ fontSize: "12px", color: "var(--text-muted)", fontStyle: "italic" }}>
                                    "{sessionReviews[session.id].review_text}"
                                  </span>
                                )}
                              </div>
                            ) : (
                              <div style={{ display: "flex", justifyContent: "flex-end", width: "100%" }}>
                                <button
                                  type="button"
                                  onClick={() => setReviewModalSession(session)}
                                  className="btn btn-primary"
                                  style={{ padding: "6px 16px", fontSize: "12px", background: "#f59e0b", borderColor: "#f59e0b", color: "#ffffff" }}
                                >
                                  ⭐ Rate Your Session / Leave a Review
                                </button>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Actions Footer */}
                        {isScheduled && (
                          <div style={{ display: "flex", justifyContent: "flex-end", borderTop: "1px solid var(--border-color)", paddingTop: "10px", marginTop: "4px" }}>
                            <button
                              type="button"
                              onClick={() => handleCancelSession(session.id)}
                              className="btn btn-secondary"
                              disabled={cancellingSessionId === session.id}
                              style={{ padding: "4px 12px", fontSize: "12px", color: "var(--error-color)", borderColor: "rgba(239, 68, 68, 0.3)" }}
                            >
                              {cancellingSessionId === session.id ? "Cancelling..." : "Cancel Session"}
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

          {/* TAB 2: PROFILE DETAILS & EDITING */}
          {activeTab === "profile" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                <h2 style={{ margin: 0, fontSize: "22px" }}>Student Profile</h2>
                {!isEditingProfile && (
                  <button
                    onClick={() => setIsEditingProfile(true)}
                    className="btn btn-primary"
                    style={{ padding: "8px 16px" }}
                  >
                    Edit Profile
                  </button>
                )}
              </div>

              {!isEditingProfile ? (
                <div className="review-section" style={{ borderBottom: "none" }}>
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
                    <div className="review-label">Preferred Languages:</div>
                    <div className="review-value">
                      {profile.preferred_tutor_languages && profile.preferred_tutor_languages.length > 0
                        ? profile.preferred_tutor_languages.join(", ")
                        : "None specified"}
                    </div>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSaveProfile}>
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
                    <label className="form-label">Preferred Languages for Tutoring</label>
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

                  <div className="btn-container">
                    <button type="button" onClick={() => setIsEditingProfile(false)} className="btn btn-secondary">
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
        </div>
      </div>

      {/* CREATE / EDIT LEARNING NEED MODAL */}
      {isNeedModalOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.6)",
            backdropFilter: "blur(3px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "20px"
          }}
          onClick={() => setIsNeedModalOpen(false)}
        >
          <div
            style={{
              background: "var(--card-bg, #ffffff)",
              color: "var(--text-color, #1f2937)",
              borderRadius: "12px",
              width: "100%",
              maxWidth: "600px",
              maxHeight: "90vh",
              overflowY: "auto",
              padding: "28px",
              position: "relative",
              border: "1px solid var(--border-color, #e5e7eb)",
              boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1)"
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setIsNeedModalOpen(false)}
              style={{
                position: "absolute",
                top: "16px",
                right: "16px",
                background: "transparent",
                border: "none",
                fontSize: "20px",
                cursor: "pointer",
                color: "var(--text-muted)"
              }}
            >
              ✕
            </button>

            <h3 style={{ margin: "0 0 6px 0", fontSize: "18px", color: "var(--text-h)" }}>
              {editingNeed ? "Edit Learning Need" : "Create New Learning Need"}
            </h3>
            <p style={{ margin: "0 0 20px 0", fontSize: "13px", color: "var(--text-muted)" }}>
              Specify the subject, specific concepts, goals, and schedule for matching.
            </p>

            {needFormError && <div className="alert alert-error">{needFormError}</div>}

            <form onSubmit={handleSaveLearningNeed}>
              <div className="form-group">
                <label className="form-label">Learning Need Title *</label>
                <input
                  type="text"
                  className="form-input"
                  value={needTitle}
                  onChange={(e) => setNeedTitle(e.target.value)}
                  placeholder="e.g. Data Structures & Algorithms Exam Prep"
                  required
                />
              </div>

              {/* Subjects */}
              <div className="form-group">
                <label className="form-label">Subjects *</label>
                <div style={{ display: "flex", gap: "8px", marginBottom: "6px" }}>
                  <input
                    type="text"
                    className="form-input"
                    value={needSubjectInput}
                    onChange={(e) => setNeedSubjectInput(e.target.value)}
                    placeholder="Add a subject (e.g. Computer Science)"
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addNeedSubject())}
                  />
                  <button type="button" onClick={addNeedSubject} className="btn btn-secondary" style={{ padding: "0 14px" }}>
                    Add
                  </button>
                </div>
                <div className="chip-container">
                  {needSubjects.map((sub) => (
                    <span key={sub} className="chip selected">
                      {sub} <span style={{ marginLeft: "6px", cursor: "pointer" }} onClick={() => removeNeedSubject(sub)}>×</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Topics */}
              <div className="form-group">
                <label className="form-label">Specific Topics / Concepts</label>
                <div style={{ display: "flex", gap: "8px", marginBottom: "6px" }}>
                  <input
                    type="text"
                    className="form-input"
                    value={needTopicInput}
                    onChange={(e) => setNeedTopicInput(e.target.value)}
                    placeholder="Add topic (e.g. Binary Trees, Dynamic Programming)"
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addNeedTopic())}
                  />
                  <button type="button" onClick={addNeedTopic} className="btn btn-secondary" style={{ padding: "0 14px" }}>
                    Add
                  </button>
                </div>
                <div className="chip-container">
                  {needTopics.map((top) => (
                    <span key={top} className="chip selected" style={{ backgroundColor: "#10b981" }}>
                      {top} <span style={{ marginLeft: "6px", cursor: "pointer" }} onClick={() => removeNeedTopic(top)}>×</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Goals */}
              <div className="form-group">
                <label className="form-label">Learning Goals</label>
                <textarea
                  className="form-textarea"
                  value={needGoals}
                  onChange={(e) => setNeedGoals(e.target.value)}
                  placeholder="Describe your learning objectives, exam targets, or assignments..."
                  style={{ minHeight: "65px" }}
                />
              </div>

              {/* Schedule & Tutor Style */}
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Preferred Availability</label>
                  <input
                    type="text"
                    className="form-input"
                    value={needAvailability}
                    onChange={(e) => setNeedAvailability(e.target.value)}
                    placeholder="e.g. Weekday evenings, Saturday 10am"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Tutor Style / Preference</label>
                  <input
                    type="text"
                    className="form-input"
                    value={needCharacteristics}
                    onChange={(e) => setNeedCharacteristics(e.target.value)}
                    placeholder="e.g. Patient, problem-solving focused"
                  />
                </div>
              </div>

              {/* Hourly Budget Range */}
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Minimum Hourly Budget (₹/hour)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={needBudgetMin}
                    onChange={(e) => setNeedBudgetMin(e.target.value)}
                    placeholder="e.g. 400"
                    min="0"
                    step="10"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Maximum Hourly Budget (₹/hour)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={needBudgetMax}
                    onChange={(e) => setNeedBudgetMax(e.target.value)}
                    placeholder="e.g. 700"
                    min="0"
                    step="10"
                  />
                </div>
              </div>

              {/* Set Active Checkbox */}
              <div className="form-group" style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "10px" }}>
                <input
                  type="checkbox"
                  id="need_is_active"
                  checked={needIsActive}
                  onChange={(e) => setNeedIsActive(e.target.checked)}
                  style={{ width: "16px", height: "16px", cursor: "pointer" }}
                />
                <label htmlFor="need_is_active" style={{ fontSize: "14px", cursor: "pointer", userSelect: "none" }}>
                  Set as my primary active learning need
                </label>
              </div>

              {/* Modal Buttons */}
              <div className="btn-container" style={{ marginTop: "24px" }}>
                <button
                  type="button"
                  onClick={() => setIsNeedModalOpen(false)}
                  className="btn btn-secondary"
                  disabled={submittingNeed}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submittingNeed}
                >
                  {submittingNeed ? "Saving..." : editingNeed ? "Save Changes" : "Create Learning Need"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PRODUCTION TUTOR DETAIL MODAL */}
      {activeRecommendationForModal && (
        <ProductionTutorDetailModal
          recommendation={activeRecommendationForModal}
          onClose={() => setActiveRecommendationForModal(null)}
          onBookingCreated={() => {
            loadBookings();
            setActiveTab("bookings");
          }}
        />
      )}

      {/* SESSION REVIEW MODAL */}
      {reviewModalSession && (
        <ReviewModal
          session={reviewModalSession}
          onClose={() => setReviewModalSession(null)}
          onReviewSuccess={handleReviewSuccess}
        />
      )}
    </div>
  );
}
