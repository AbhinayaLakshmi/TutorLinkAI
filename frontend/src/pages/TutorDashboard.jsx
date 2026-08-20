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
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState("");

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
          setAvatarUrl(`${API_BASE_URL}/uploads/${d.profile_picture_path}`);
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

  useEffect(() => {
    loadData();
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
          <div className="sidebar-name">{user.full_name}</div>
          <div className="sidebar-role">Tutor</div>
          
          <ul className="sidebar-menu">
            <li className="sidebar-menu-item active" onClick={() => setIsEditing(false)}>My Profile</li>
            <li className="sidebar-menu-item" style={{ color: "var(--error-color)" }} onClick={handleLogout}>Log Out</li>
          </ul>
        </div>

        {/* Content area */}
        <div className="dashboard-content">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <h2 style={{ margin: 0 }}>Tutor Dashboard</h2>
            {!isEditing && (
              <button onClick={() => setIsEditing(true)} className="btn btn-primary" style={{ padding: "8px 16px" }}>
                Edit Profile
              </button>
            )}
          </div>

          {profile.verification_status === "PENDING" && (
            <div className="alert alert-warning">
              <strong>Verification Pending</strong> — Your uploaded degree certificate has been saved. We are currently verifying your credentials. You will be notified once the process is complete.
            </div>
          )}

          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

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
                  <div className="review-value">${hourlyRate} / Hr</div>
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
                  <label className="form-label">Hourly Rate ($) *</label>
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
      </div>
    </div>
  );
}
