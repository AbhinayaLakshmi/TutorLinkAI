import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api, { API_BASE_URL } from "../services/api";
import "../onboarding.css";

const LANGUAGES_OPTIONS = ["English", "Spanish", "French", "German", "Mandarin", "Hindi", "Arabic", "Japanese"];
const MODES_OPTIONS = ["Online", "Offline", "Both"];
const DEGREES = ["Bachelor", "Master", "PhD", "Associate Degree", "Diploma", "High School"];
const LEVEL_OPTIONS = ["Primary", "Middle School", "High School", "University", "Adult"];
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function TutorOnboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [user, setUser] = useState(null);

  // STEP 1: Personal Details
  const [location, setLocation] = useState("");
  const [selectedLanguages, setSelectedLanguages] = useState([]);
  const [teachMode, setTeachMode] = useState("Online");
  const [profilePic, setProfilePic] = useState(null);
  const [profilePicUrl, setProfilePicUrl] = useState("");

  // STEP 2: Education
  const [highestDegree, setHighestDegree] = useState("Bachelor");
  const [degreeName, setDegreeName] = useState("");
  const [university, setUniversity] = useState("");
  const [specialization, setSpecialization] = useState("");
  const [graduationYear, setGraduationYear] = useState(new Date().getFullYear());

  // STEP 3: Expertise
  const [subjectInput, setSubjectInput] = useState("");
  const [subjects, setSubjects] = useState([]);
  const [topicInput, setTopicInput] = useState("");
  const [topics, setTopics] = useState([]);
  const [selectedLevels, setSelectedLevels] = useState([]);
  const [yearsExp, setYearsExp] = useState(0);
  const [prevExp, setPrevExp] = useState("");
  const [skillInput, setSkillInput] = useState("");
  const [skills, setSkills] = useState([]);

  // STEP 4: Availability & Pricing
  const [selectedDay, setSelectedDay] = useState("Monday");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");
  const [availabilities, setAvailabilities] = useState([]);
  const [duration, setDuration] = useState(60);
  const [hourlyRate, setHourlyRate] = useState(30.0);

  // STEP 5: Certificate Upload
  const [certFile, setCertFile] = useState(null);
  const [uploadedCerts, setUploadedCerts] = useState([]);
  const [uploadingCert, setUploadingCert] = useState(false);

  // Parse validation error responses safely
  const parseErrorMessage = (err) => {
    if (!err.response?.data?.detail) {
      return "An unexpected error occurred. Please try again.";
    }
    const detail = err.response.data.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      // Pydantic validation errors list
      return detail.map((e) => {
        const fieldName = e.loc ? e.loc[e.loc.length - 1] : "field";
        return `${fieldName}: ${e.msg}`;
      }).join(", ");
    }
    return "Validation error occurred.";
  };

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

    // Load initial profile values
    api.get("/api/onboarding/tutor/me")
      .then((res) => {
        const d = res.data;
        if (d.location) setLocation(d.location);
        if (d.languages_spoken) setSelectedLanguages(d.languages_spoken);
        if (d.preferred_teaching_mode) setTeachMode(d.preferred_teaching_mode);
        if (d.profile_picture_path) setProfilePicUrl(`${API_BASE_URL}/uploads/${d.profile_picture_path}`);
        
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
          if (exp.subjects_taught) setSubjects(exp.subjects_taught);
          if (exp.topics_expertise) setTopics(exp.topics_expertise);
          if (exp.student_levels) setSelectedLevels(exp.student_levels);
          setYearsExp(exp.years_of_experience);
          if (exp.previous_experience) setPrevExp(exp.previous_experience);
          if (exp.skills) setSkills(exp.skills);
        }

        if (d.availability && d.availability.length > 0) {
          const formatted = d.availability.map(a => {
            const range = a.time_ranges && a.time_ranges.length > 0 ? a.time_ranges[0] : {start: "09:00", end: "17:00"};
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

        if (d.certificates) {
          setUploadedCerts(d.certificates);
        }
      })
      .catch((err) => {
        setError("Failed to load tutor onboarding data.");
      });
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

  // Upload Profile Picture
  const handleProfilePicChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      setError("Profile picture exceeds 2MB limit.");
      return;
    }

    setError("");
    setProfilePic(file);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post("/api/onboarding/tutor/me/profile-picture", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setProfilePicUrl(`${API_BASE_URL}/uploads/${res.data.profile_picture_path}`);
      setSuccess("Profile picture uploaded successfully.");
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(parseErrorMessage(err));
    }
  };

  // Upload Certificate
  const handleCertUpload = async (e) => {
    e.preventDefault();
    if (!certFile) {
      setError("Please select a file to upload.");
      return;
    }

    if (certFile.size > 5 * 1024 * 1024) {
      setError("Certificate file exceeds 5MB limit.");
      return;
    }

    setError("");
    setUploadingCert(true);

    const formData = new FormData();
    formData.append("file", certFile);

    try {
      const res = await api.post("/api/onboarding/tutor/me/certificate", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setUploadedCerts([...uploadedCerts, res.data]);
      setCertFile(null);
      setSuccess("Certificate uploaded successfully.");
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(parseErrorMessage(err));
    } finally {
      setUploadingCert(false);
    }
  };

  const saveTutorData = async () => {
    setError("");
    
    // BUILD STEP-CONDITIONAL PAYLOAD
    const payload = {
      location,
      languages_spoken: selectedLanguages,
      preferred_teaching_mode: teachMode
    };

    if (step >= 2) {
      payload.education = [
        {
          highest_degree: highestDegree,
          degree_name: degreeName,
          university,
          specialization,
          graduation_year: parseInt(graduationYear)
        }
      ];
    }

    if (step >= 3) {
      payload.expertise = {
        subjects_taught: subjects,
        topics_expertise: topics,
        student_levels: selectedLevels,
        years_of_experience: parseInt(yearsExp) || 0,
        previous_experience: prevExp,
        skills,
        languages_can_teach_in: selectedLanguages  // Aligning languages they can teach in
      };
    }

    if (step >= 4) {
      payload.availability = availabilities.map((av) => ({
        day_of_week: av.day_of_week,
        time_ranges: [{ start: av.start, end: av.end }],
        preferred_session_duration: av.duration,
        hourly_rate: av.rate
      }));
    }

    try {
      await api.put("/api/onboarding/tutor/me", payload);
      return true;
    } catch (err) {
      setError(parseErrorMessage(err));
      return false;
    }
  };

  const handleNext = async () => {
    if (step === 1) {
      if (!location) {
        setError("Location is required.");
        return;
      }
    }
    if (step === 2) {
      if (!degreeName || !university) {
        setError("Please enter degree name and university/institution.");
        return;
      }
    }
    if (step === 3) {
      if (subjects.length === 0) {
        setError("Please add at least one subject you teach.");
        return;
      }
    }
    if (step === 4) {
      if (availabilities.length === 0) {
        setError("Please add at least one availability slot.");
        return;
      }
    }
    if (step === 5) {
      if (uploadedCerts.length === 0) {
        setError("Please upload your degree certificate to proceed.");
        return;
      }
    }

    const saved = await saveTutorData();
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

    const saved = await saveTutorData();
    if (!saved) {
      setSubmitting(false);
      return;
    }

    try {
      await api.post("/api/onboarding/tutor/complete");
      setSuccess("Onboarding completed successfully! Redirecting...");
      setTimeout(() => {
        navigate("/dashboard/tutor");
      }, 1500);
    } catch (err) {
      setError(parseErrorMessage(err));
      setSubmitting(false);
    }
  };

  return (
    <div className="onboard-container">
      <div className="onboard-card" style={{ maxWidth: "750px" }}>
        <h2 className="onboard-title">Tutor Onboarding</h2>
        <p className="onboard-subtitle">Fill in details to start your vetting process.</p>

        {/* Step Indicator */}
        <div className="step-indicator" style={{ marginBottom: "35px" }}>
          {[1, 2, 3, 4, 5, 6].map((num) => (
            <div
              key={num}
              className={`step-item ${step >= num ? "active" : ""} ${step > num ? "completed" : ""}`}
            >
              {num}
            </div>
          ))}
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {/* STEP 1: Personal Details */}
        {step === 1 && (
          <div>
            <h3 style={{ fontSize: "18px", marginBottom: "20px", fontWeight: "600" }}>Step 1 — Personal Details</h3>
            
            <div style={{ display: "flex", gap: "24px", marginBottom: "24px", alignItems: "center" }}>
              <div className="sidebar-avatar" style={{ margin: 0 }}>
                {profilePicUrl ? <img src={profilePicUrl} alt="Avatar Preview" /> : "👤"}
              </div>
              <div>
                <label className="form-label" style={{ marginBottom: "8px" }}>Profile Picture (Max 2MB)</label>
                <input
                  type="file"
                  accept="image/png, image/jpeg, image/jpg"
                  onChange={handleProfilePicChange}
                  style={{ fontSize: "14px" }}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Location (City, Area) *</label>
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
                <label className="form-label">Preferred Teaching Mode *</label>
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

            <div className="btn-container" style={{ justifyContent: "flex-end" }}>
              <button onClick={handleNext} className="btn btn-primary">
                Next Step
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Education */}
        {step === 2 && (
          <div>
            <h3 style={{ fontSize: "18px", marginBottom: "20px", fontWeight: "600" }}>Step 2 — Highest Academic Degree</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Degree Level *</label>
                <select
                  className="form-select"
                  value={highestDegree}
                  onChange={(e) => setHighestDegree(e.target.value)}
                >
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
                  placeholder="e.g. B.Sc. Physics"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">University / Institution *</label>
              <input
                type="text"
                className="form-input"
                value={university}
                onChange={(e) => setUniversity(e.target.value)}
                placeholder="e.g. IIT Madras"
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
                  placeholder="e.g. Quantum Mechanics"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Graduation Year *</label>
                <input
                  type="number"
                  className="form-input"
                  value={graduationYear}
                  min={1900}
                  max={2100}
                  onChange={(e) => setGraduationYear(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="btn-container">
              <button onClick={handleBack} className="btn btn-secondary">Back</button>
              <button onClick={handleNext} className="btn btn-primary">Next Step</button>
            </div>
          </div>
        )}

        {/* STEP 3: Expertise */}
        {step === 3 && (
          <div>
            <h3 style={{ fontSize: "18px", marginBottom: "20px", fontWeight: "600" }}>Step 3 — Teaching Expertise</h3>
            
            <div className="form-group">
              <label className="form-label">Subjects Taught *</label>
              <div style={{ display: "flex", gap: "10px", marginBottom: "8px" }}>
                <input
                  type="text"
                  className="form-input"
                  value={subjectInput}
                  onChange={(e) => setSubjectInput(e.target.value)}
                  placeholder="e.g. Physics"
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
              <label className="form-label">Topics / Focus Areas</label>
              <div style={{ display: "flex", gap: "10px", marginBottom: "8px" }}>
                <input
                  type="text"
                  className="form-input"
                  value={topicInput}
                  onChange={(e) => setTopicInput(e.target.value)}
                  placeholder="e.g. Electromagnetism"
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
                  min={0}
                  value={yearsExp}
                  onChange={(e) => setYearsExp(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Student Levels</label>
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

            <div className="form-group">
              <label className="form-label">Previous Teaching Experience</label>
              <textarea
                className="form-textarea"
                value={prevExp}
                onChange={(e) => setPrevExp(e.target.value)}
                placeholder="List any institutional teaching or previous tutoring roles..."
              />
            </div>

            <div className="form-group">
              <label className="form-label">Skills / Specializations</label>
              <div style={{ display: "flex", gap: "10px", marginBottom: "8px" }}>
                <input
                  type="text"
                  className="form-input"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  placeholder="e.g. Exam Prep"
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addSkill())}
                />
                <button type="button" onClick={addSkill} className="btn btn-secondary">Add</button>
              </div>
              <div className="chip-container">
                {skills.map((sk) => (
                  <span key={sk} className="chip selected" style={{ backgroundColor: "#8b5cf6" }}>
                    {sk} <span style={{ marginLeft: "6px", cursor: "pointer" }} onClick={() => removeSkill(sk)}>×</span>
                  </span>
                ))}
              </div>
            </div>

            <div className="btn-container">
              <button onClick={handleBack} className="btn btn-secondary">Back</button>
              <button onClick={handleNext} className="btn btn-primary">Next Step</button>
            </div>
          </div>
        )}

        {/* STEP 4: Availability & Pricing */}
        {step === 4 && (
          <div>
            <h3 style={{ fontSize: "18px", marginBottom: "20px", fontWeight: "600" }}>Step 4 — Availability and Pricing</h3>
            
            <div style={{ border: "1px solid var(--border-color)", padding: "16px", borderRadius: "6px", marginBottom: "24px" }}>
              <h4 style={{ margin: "0 0 12px 0", fontSize: "15px" }}>Add Availability Slots</h4>
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
                  <label className="form-label">Start Time</label>
                  <input type="time" className="form-input" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                </div>
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label">End Time</label>
                  <input type="time" className="form-input" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
                </div>
              </div>
              <button type="button" onClick={addAvailability} className="btn btn-secondary" style={{ width: "100%", marginTop: "15px", padding: "8px" }}>
                Add Availability Slot
              </button>
            </div>

            {availabilities.length > 0 && (
              <div style={{ marginBottom: "24px" }}>
                <h4 style={{ margin: "0 0 8px 0", fontSize: "14px" }}>Configured Slots</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {availabilities.map((av, index) => (
                    <div key={index} style={{ display: "flex", justifyContent: "space-between", background: "var(--bg-color)", padding: "8px 12px", borderRadius: "4px", fontSize: "14px" }}>
                      <span><strong>{av.day_of_week}</strong>: {av.start} - {av.end}</span>
                      <span style={{ color: "var(--error-color)", cursor: "pointer", fontWeight: "600" }} onClick={() => removeAvailability(index)}>Delete</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Preferred Session Duration</label>
                <select className="form-select" value={duration} onChange={(e) => setDuration(e.target.value)}>
                  <option value={30}>30 Minutes</option>
                  <option value={45}>45 Minutes</option>
                  <option value={60}>60 Minutes</option>
                  <option value={90}>90 Minutes</option>
                  <option value={120}>120 Minutes</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Hourly / Session Rate ($) *</label>
                <input
                  type="number"
                  className="form-input"
                  min={0}
                  step={5}
                  value={hourlyRate}
                  onChange={(e) => setHourlyRate(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="btn-container">
              <button onClick={handleBack} className="btn btn-secondary">Back</button>
              <button onClick={handleNext} className="btn btn-primary">Next Step</button>
            </div>
          </div>
        )}

        {/* STEP 5: Certificate Upload */}
        {step === 5 && (
          <div>
            <h3 style={{ fontSize: "18px", marginBottom: "20px", fontWeight: "600" }}>Step 5 — Degree / Education Certificate Upload</h3>
            <p style={{ fontSize: "14px", color: "var(--text-muted)", marginBottom: "20px" }}>
              Please upload a scanned copy of your highest degree (PDF, PNG, JPG). Max size: 5MB.
            </p>

            <form onSubmit={handleCertUpload} className="file-upload-zone" style={{ marginBottom: "20px" }}>
              <input
                type="file"
                accept="application/pdf, image/png, image/jpeg, image/jpg"
                onChange={(e) => setCertFile(e.target.files[0])}
                style={{ marginBottom: "15px", fontSize: "14px" }}
              />
              {certFile && (
                <div style={{ fontSize: "13px", marginBottom: "15px", color: "var(--primary-color)" }}>
                  Selected file: {certFile.name} ({(certFile.size / (1024 * 1024)).toFixed(2)}MB)
                </div>
              )}
              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: "100%", padding: "10px" }}
                disabled={uploadingCert || !certFile}
              >
                {uploadingCert ? "Uploading..." : "Upload Certificate"}
              </button>
            </form>

            {uploadedCerts.length > 0 && (
              <div style={{ marginBottom: "25px" }}>
                <h4 style={{ margin: "0 0 8px 0", fontSize: "14px" }}>Uploaded Documents</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {uploadedCerts.map((cert) => (
                    <div key={cert.id} style={{ padding: "10px 12px", border: "1px solid var(--border-color)", borderRadius: "4px", fontSize: "14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <span style={{ fontWeight: "500" }}>📄 {cert.original_filename}</span>
                        <span style={{ fontSize: "12px", color: "var(--text-muted)", marginLeft: "10px" }}>
                          ({(cert.file_size / (1024 * 1024)).toFixed(2)}MB)
                        </span>
                      </div>
                      <span className="chip" style={{ backgroundColor: "#fef3c7", color: "#d97706", fontSize: "11px", margin: 0 }}>
                        {cert.verification_status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="btn-container">
              <button onClick={handleBack} className="btn btn-secondary">Back</button>
              <button onClick={handleNext} className="btn btn-primary">Next Step</button>
            </div>
          </div>
        )}

        {/* STEP 6: Review & Submit */}
        {step === 6 && (
          <div>
            <h3 style={{ fontSize: "18px", marginBottom: "20px", fontWeight: "600" }}>Step 6 — Review & Submit for Verification</h3>
            
            <div className="review-section">
              <h3>Personal Details</h3>
              <div className="review-item">
                <div className="review-label">Location:</div>
                <div className="review-value">{location}</div>
              </div>
              <div className="review-item">
                <div className="review-label">Teachable Languages:</div>
                <div className="review-value">{selectedLanguages.join(", ") || "None"}</div>
              </div>
              <div className="review-item">
                <div className="review-label">Teaching Mode:</div>
                <div className="review-value">{teachMode}</div>
              </div>
            </div>

            <div className="review-section">
              <h3>Education</h3>
              <div className="review-item">
                <div className="review-label">Degree:</div>
                <div className="review-value">{highestDegree} ({degreeName})</div>
              </div>
              <div className="review-item">
                <div className="review-label">University:</div>
                <div className="review-value">{university}</div>
              </div>
              <div className="review-item">
                <div className="review-label">Specialization:</div>
                <div className="review-value">{specialization || "None"}</div>
              </div>
              <div className="review-item">
                <div className="review-label">Graduation Year:</div>
                <div className="review-value">{graduationYear}</div>
              </div>
            </div>

            <div className="review-section">
              <h3>Teaching details</h3>
              <div className="review-item">
                <div className="review-label">Subjects:</div>
                <div className="review-value">{subjects.join(", ")}</div>
              </div>
              <div className="review-item">
                <div className="review-label">Experience:</div>
                <div className="review-value">{yearsExp} Years</div>
              </div>
              <div className="review-item">
                <div className="review-label">Hourly Rate:</div>
                <div className="review-value">${hourlyRate} / Hr</div>
              </div>
              <div className="review-item">
                <div className="review-label">Certificates:</div>
                <div className="review-value">
                  {uploadedCerts.map((c) => c.original_filename).join(", ") || "None"}
                </div>
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
                {submitting ? "Submitting..." : "Submit for Verification"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
