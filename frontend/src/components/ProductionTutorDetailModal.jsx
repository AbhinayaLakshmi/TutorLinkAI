import React, { useState } from "react";
import api, { API_BASE_URL } from "../services/api";

export default function ProductionTutorDetailModal({ recommendation, onClose, onBookingSuccess }) {
  if (!recommendation) return null;

  const rec = recommendation;
  const breakdown = rec.breakdown || {};
  const availability = rec.availability || [];
  const matchedTopics = rec.matched_topics || [];
  const matchReasons = rec.match_reasons || [];
  const subjects = rec.subjects || [];

  // Booking Form State
  const todayStr = new Date().toISOString().split("T")[0];
  const [showBookingForm, setShowBookingForm] = useState(false);
  const [scheduledDate, setScheduledDate] = useState(todayStr);
  const [startTime, setStartTime] = useState("10:00");
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [studentMessage, setStudentMessage] = useState("");
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState("");
  const [bookingSuccess, setBookingSuccess] = useState("");

  const estimatedTotal = ((rec.hourly_rate || 500) * (durationMinutes / 60)).toFixed(2);

  const handleCreateBooking = async (e) => {
    e.preventDefault();
    setBookingError("");
    setBookingSuccess("");
    setBookingLoading(true);

    try {
      const payload = {
        tutor_id: rec.id,
        learning_need_id: rec.learning_need_id,
        scheduled_date: scheduledDate,
        start_time: startTime,
        duration_minutes: parseInt(durationMinutes, 10),
        student_message: studentMessage.trim() || null,
      };

      const res = await api.post("/api/booking", payload);
      setBookingSuccess("Booking request sent successfully to tutor! Status: PENDING");
      if (onBookingSuccess) {
        onBookingSuccess(res.data);
      }
      setTimeout(() => {
        onClose();
      }, 1800);
    } catch (err) {
      setBookingError(err.response?.data?.detail || "Failed to create booking request. Please check details.");
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.6)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "20px",
        overflowY: "auto"
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "var(--card-bg, #ffffff)",
          color: "var(--text-color, #1f2937)",
          borderRadius: "12px",
          width: "100%",
          maxWidth: "680px",
          maxHeight: "90vh",
          overflowY: "auto",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
          border: "1px solid var(--border-color, #e5e7eb)",
          padding: "28px",
          position: "relative"
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: "18px",
            right: "18px",
            background: "transparent",
            border: "none",
            fontSize: "22px",
            lineHeight: 1,
            cursor: "pointer",
            color: "var(--text-muted, #6b7280)",
            padding: "6px"
          }}
          aria-label="Close modal"
        >
          ✕
        </button>

        {/* Header: Avatar, Name, Role, Match Badge */}
        <div style={{ display: "flex", gap: "18px", alignItems: "center", marginBottom: "22px" }}>
          <div
            style={{
              width: "72px",
              height: "72px",
              borderRadius: "50%",
              background: "var(--border-color, #e5e7eb)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              overflow: "hidden",
              fontSize: "28px",
              fontWeight: "600",
              color: "var(--text-muted, #6b7280)",
              border: "3px solid var(--border-color, #e5e7eb)",
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
            <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
              <h2 style={{ margin: 0, fontSize: "20px", fontWeight: "700", color: "var(--text-h, #111827)" }}>
                {rec.name}
              </h2>
              <div
                style={{
                  background:
                    rec.overall_percentage >= 80
                      ? "rgba(16, 185, 129, 0.12)"
                      : "rgba(59, 130, 246, 0.12)",
                  color:
                    rec.overall_percentage >= 80
                      ? "var(--success-color, #10b981)"
                      : "var(--primary-color, #3b82f6)",
                  padding: "4px 12px",
                  borderRadius: "20px",
                  fontSize: "12px",
                  fontWeight: "700",
                  border:
                    rec.overall_percentage >= 80
                      ? "1px solid rgba(16, 185, 129, 0.3)"
                      : "1px solid rgba(59, 130, 246, 0.3)"
                }}
              >
                {rec.overall_percentage}% Match
              </div>
            </div>

            <div style={{ display: "flex", gap: "16px", marginTop: "6px", fontSize: "13px", color: "var(--text-muted, #6b7280)", flexWrap: "wrap" }}>
              <span>📍 {rec.location || "Location not provided"}</span>
              <span style={{ color: "#eab308" }}>
                ★ {rec.rating ? rec.rating.toFixed(1) : "4.5"}
              </span>
              <span style={{ fontWeight: "600", color: "var(--text-color, #1f2937)" }}>
                ₹{rec.hourly_rate} / hr
              </span>
            </div>
          </div>
        </div>

        {/* AI Match Explanation / Summary */}
        {rec.explanation_summary && (
          <div
            style={{
              background: "rgba(59, 130, 246, 0.06)",
              border: "1px solid rgba(59, 130, 246, 0.2)",
              borderRadius: "8px",
              padding: "14px 16px",
              marginBottom: "20px"
            }}
          >
            <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--primary-color, #3b82f6)", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "4px" }}>
              💡 AI Match Explanation
            </div>
            <p style={{ margin: 0, fontSize: "13px", lineHeight: "1.5", color: "var(--text-color, #1f2937)" }}>
              {rec.explanation_summary}
            </p>
          </div>
        )}

        {/* Match Reasons */}
        {matchReasons.length > 0 && (
          <div style={{ marginBottom: "20px" }}>
            <h4 style={{ fontSize: "14px", fontWeight: "600", margin: "0 0 8px 0", color: "var(--text-h, #111827)" }}>
              Why this tutor was recommended:
            </h4>
            <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "13px", color: "var(--text-color, #374151)", lineHeight: "1.6" }}>
              {matchReasons.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Bio */}
        <div style={{ marginBottom: "20px" }}>
          <h4 style={{ fontSize: "14px", fontWeight: "600", margin: "0 0 6px 0", color: "var(--text-h, #111827)" }}>
            About Tutor
          </h4>
          <p style={{ margin: 0, fontSize: "13px", color: "var(--text-muted, #6b7280)", lineHeight: "1.5" }}>
            {rec.bio || "No biography provided."}
          </p>
        </div>

        {/* Subjects & Matched Topics */}
        <div style={{ marginBottom: "20px" }}>
          <h4 style={{ fontSize: "14px", fontWeight: "600", margin: "0 0 8px 0", color: "var(--text-h, #111827)" }}>
            Subjects & Topics
          </h4>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "8px" }}>
            {subjects.map((sub) => (
              <span
                key={sub}
                style={{
                  fontSize: "12px",
                  background: "var(--border-color, #e5e7eb)",
                  color: "var(--text-color, #1f2937)",
                  padding: "3px 10px",
                  borderRadius: "4px",
                  fontWeight: "500"
                }}
              >
                {sub}
              </span>
            ))}
          </div>
          {matchedTopics.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", alignItems: "center", marginTop: "6px" }}>
              <span style={{ fontSize: "11px", color: "var(--text-muted, #6b7280)", fontWeight: "600" }}>
                Targeted Topics:
              </span>
              {matchedTopics.map((top) => (
                <span
                  key={top}
                  style={{
                    fontSize: "11px",
                    background: "rgba(16, 185, 129, 0.12)",
                    color: "var(--success-color, #10b981)",
                    border: "1px solid rgba(16, 185, 129, 0.25)",
                    padding: "2px 8px",
                    borderRadius: "4px",
                    fontWeight: "600"
                  }}
                >
                  ✓ {top}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Detailed Score Breakdown */}
        {breakdown && Object.keys(breakdown).length > 0 && (
          <div
            style={{
              background: "var(--bg-color, #f9fafb)",
              border: "1px solid var(--border-color, #e5e7eb)",
              borderRadius: "8px",
              padding: "14px",
              marginBottom: "20px"
            }}
          >
            <h4 style={{ fontSize: "13px", fontWeight: "600", margin: "0 0 10px 0", color: "var(--text-h, #111827)" }}>
              Matching Score Breakdown
            </h4>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "12px" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted, #6b7280)" }}>Subject Compatibility:</span>
                <span style={{ fontWeight: "600" }}>{Math.round((breakdown.subject_score || 0) * 100)}%</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted, #6b7280)" }}>Budget Compatibility:</span>
                <span style={{ fontWeight: "600" }}>{Math.round((breakdown.fee_score || 0) * 100)}%</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted, #6b7280)" }}>Schedule Compatibility:</span>
                <span style={{ fontWeight: "600" }}>{Math.round((breakdown.time_score || 0) * 100)}%</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted, #6b7280)" }}>Location Distance:</span>
                <span style={{ fontWeight: "600" }}>
                  {breakdown.distance_km > 0 ? `${breakdown.distance_km.toFixed(1)} km` : "Nearby"}
                </span>
              </div>
              {breakdown.topic_score !== null && breakdown.topic_score !== undefined && (
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--text-muted, #6b7280)" }}>Topic Coverage:</span>
                  <span style={{ fontWeight: "600" }}>{Math.round(breakdown.topic_score * 100)}%</span>
                </div>
              )}
              {rec.pedagogy_compatibility !== null && rec.pedagogy_compatibility !== undefined && (
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--text-muted, #6b7280)" }}>Pedagogy Match:</span>
                  <span style={{ fontWeight: "600" }}>{Math.round(rec.pedagogy_compatibility * 100)}%</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Availability Schedule */}
        {availability.length > 0 && (
          <div style={{ marginBottom: "24px" }}>
            <h4 style={{ fontSize: "14px", fontWeight: "600", margin: "0 0 8px 0", color: "var(--text-h, #111827)" }}>
              Weekly Availability
            </h4>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {availability.map((slot, index) => (
                <div
                  key={index}
                  style={{
                    background: "var(--bg-color, #f9fafb)",
                    border: "1px solid var(--border-color, #e5e7eb)",
                    borderRadius: "6px",
                    padding: "6px 10px",
                    fontSize: "12px"
                  }}
                >
                  <span style={{ fontWeight: "600" }}>{slot.day}: </span>
                  <span style={{ color: "var(--text-muted, #6b7280)" }}>{slot.start_time} - {slot.end_time}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Booking Form Section */}
        {showBookingForm && (
          <div
            style={{
              background: "rgba(59, 130, 246, 0.04)",
              border: "1px solid var(--primary-color, #3b82f6)",
              borderRadius: "8px",
              padding: "20px",
              marginBottom: "24px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <h4 style={{ fontSize: "15px", fontWeight: "700", margin: 0, color: "var(--primary-color, #3b82f6)" }}>
                📅 Schedule Session with {rec.name}
              </h4>
              <span style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-muted, #6b7280)" }}>
                Rate: ₹{rec.hourly_rate}/hr
              </span>
            </div>

            {rec.learning_need_title && (
              <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "14px" }}>
                Target Learning Need: <strong>{rec.learning_need_title}</strong>
              </div>
            )}

            {bookingError && (
              <div className="alert alert-error" style={{ fontSize: "13px", marginBottom: "12px" }}>
                {bookingError}
              </div>
            )}
            {bookingSuccess && (
              <div className="alert alert-success" style={{ fontSize: "13px", marginBottom: "12px" }}>
                {bookingSuccess}
              </div>
            )}

            <form onSubmit={handleCreateBooking}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "14px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                    Date
                  </label>
                  <input
                    type="date"
                    required
                    min={todayStr}
                    value={scheduledDate}
                    onChange={(e) => setScheduledDate(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px",
                      borderRadius: "6px",
                      border: "1px solid var(--border-color, #d1d5db)",
                      fontSize: "13px",
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                    Start Time
                  </label>
                  <input
                    type="time"
                    required
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px",
                      borderRadius: "6px",
                      border: "1px solid var(--border-color, #d1d5db)",
                      fontSize: "13px",
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                    Duration
                  </label>
                  <select
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(parseInt(e.target.value, 10))}
                    style={{
                      width: "100%",
                      padding: "8px",
                      borderRadius: "6px",
                      border: "1px solid var(--border-color, #d1d5db)",
                      fontSize: "13px",
                      boxSizing: "border-box",
                    }}
                  >
                    <option value={30}>30 mins</option>
                    <option value={45}>45 mins</option>
                    <option value={60}>60 mins (1 hr)</option>
                    <option value={90}>90 mins (1.5 hrs)</option>
                    <option value={120}>120 mins (2 hrs)</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>
                  Session Goals / Note (Optional)
                </label>
                <textarea
                  rows={2}
                  maxLength={500}
                  value={studentMessage}
                  onChange={(e) => setStudentMessage(e.target.value)}
                  placeholder="e.g. Would like to review calculus integration concepts and practice exam problems."
                  style={{
                    width: "100%",
                    padding: "8px",
                    borderRadius: "6px",
                    border: "1px solid var(--border-color, #d1d5db)",
                    fontSize: "13px",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  background: "rgba(0,0,0,0.03)",
                  padding: "10px 14px",
                  borderRadius: "6px",
                  marginBottom: "14px",
                }}
              >
                <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>Estimated Total:</span>
                <span style={{ fontSize: "16px", fontWeight: "700", color: "var(--primary-color)" }}>
                  ₹{estimatedTotal}
                </span>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                <button
                  type="button"
                  onClick={() => setShowBookingForm(false)}
                  disabled={bookingLoading}
                  className="btn btn-secondary"
                  style={{ padding: "7px 14px", fontSize: "12px" }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={bookingLoading || !rec.learning_need_id}
                  className="btn btn-primary"
                  style={{ padding: "7px 18px", fontSize: "12px", fontWeight: "600" }}
                >
                  {bookingLoading ? "Sending Request..." : "Send Booking Request"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Footer Actions */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderTop: "1px solid var(--border-color, #e5e7eb)",
            paddingTop: "18px",
            marginTop: "10px"
          }}
        >
          <button
            type="button"
            onClick={onClose}
            className="btn btn-secondary"
            style={{ padding: "8px 18px", fontSize: "13px" }}
          >
            Close
          </button>

          {!showBookingForm && (
            <button
              type="button"
              onClick={() => setShowBookingForm(true)}
              className="btn btn-primary"
              style={{
                padding: "10px 22px",
                fontSize: "13px",
                fontWeight: "600",
                cursor: "pointer"
              }}
            >
              📅 Book Tutor (₹{rec.hourly_rate}/hr)
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
