import React, { useState } from "react";

export default function TutorDetailModal({ tutor, currentBudget, onClose }) {
  const [bookingConfirmed, setBookingConfirmed] = useState(false);

  if (!tutor) return null;

  const { breakdown } = tutor;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
          ✕
        </button>

        {/* Demo Disclaimer Tag */}
        <div className="demo-disclaimer-tag">
          ⚠️ DEMO CANDIDATE PROFILE • Controlled Synthetic Benchmark Data
        </div>

        {/* Profile Header */}
        <div style={{ display: "flex", gap: "16px", alignItems: "center", marginBottom: "20px" }}>
          <div className="tutor-avatar-circle" style={{ width: "64px", height: "64px", fontSize: "32px" }}>
            {tutor.avatar}
          </div>
          <div style={{ flex: 1 }}>
            <h2 style={{ margin: "0 0 4px", fontSize: "20px", fontWeight: "700", color: "var(--text-h)" }}>
              {tutor.name}
            </h2>
            <p style={{ margin: "0 0 6px", fontSize: "14px", color: "var(--text-muted)" }}>
              {tutor.title}
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
              <span className="demo-pill primary">
                {tutor.subjects.join(", ")}
              </span>
              <span className="demo-pill success">
                ★ {tutor.rating.toFixed(2)} ({tutor.total_reviews} reviews)
              </span>
              <span className="demo-pill">
                {tutor.teaching_mode} Mode
              </span>
            </div>
          </div>

          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "28px", fontWeight: "800", color: "#4f46e5" }}>
              {tutor.overall_percentage}%
            </div>
            <div style={{ fontSize: "11px", fontWeight: "700", textTransform: "uppercase", color: "var(--text-muted)" }}>
              Match Score
            </div>
          </div>
        </div>

        {/* Bio & Background */}
        <div className="need-prop-group" style={{ marginBottom: "18px" }}>
          <div className="need-prop-label">Expertise & Biography</div>
          <div className="need-prop-value" style={{ fontSize: "14px", color: "var(--text-color)" }}>
            {tutor.bio}
          </div>
        </div>

        {/* Key Attributes Grid */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "12px",
          background: "var(--code-bg, #f9fafb)",
          border: "1px solid var(--border-color, #e5e7eb)",
          borderRadius: "8px",
          padding: "14px",
          marginBottom: "20px"
        }}>
          <div>
            <div className="need-prop-label">Hourly Tutoring Fee</div>
            <div style={{ fontSize: "16px", fontWeight: "700", color: "var(--text-h)" }}>
              ₹{tutor.hourly_rate} / hour
              {tutor.hourly_rate <= currentBudget ? (
                <span style={{ fontSize: "11px", color: "#059669", marginLeft: "6px" }}>✓ Within Budget</span>
              ) : (
                <span style={{ fontSize: "11px", color: "#dc2626", marginLeft: "6px" }}>⚠️ Exceeds Budget</span>
              )}
            </div>
          </div>

          <div>
            <div className="need-prop-label">Student Levels</div>
            <div style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-h)" }}>
              {tutor.student_levels.join(", ")}
            </div>
          </div>

          <div>
            <div className="need-prop-label">Languages</div>
            <div style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-h)" }}>
              {tutor.languages.join(", ")}
            </div>
          </div>

          <div>
            <div className="need-prop-label">Teaching Skills</div>
            <div style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-h)" }}>
              {tutor.skills.join(", ")}
            </div>
          </div>
        </div>

        {/* Why Recommended Section */}
        <div style={{ marginBottom: "20px" }}>
          <div className="need-prop-label" style={{ color: "#4f46e5" }}>Why Recommended for Alex Kumar</div>
          <div className="tutor-explanation-box" style={{ margin: "6px 0 12px" }}>
            {tutor.explanation_summary}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
            {tutor.match_reasons.map((reason, idx) => (
              <div key={idx} style={{
                fontSize: "12px",
                display: "flex",
                gap: "6px",
                alignItems: "center",
                background: "var(--social-bg, #f3f4f6)",
                padding: "6px 10px",
                borderRadius: "6px"
              }}>
                <span style={{ color: "#059669", fontWeight: "bold" }}>✓</span>
                <span>{reason}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Topic Alignment Breakdown */}
        <div style={{ marginBottom: "20px" }}>
          <div className="need-prop-label">Topic Coverage & Overlap</div>
          <div style={{ display: "flex", gap: "14px", marginTop: "6px", flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: "220px" }}>
              <div style={{ fontSize: "12px", fontWeight: "600", color: "#059669", marginBottom: "4px" }}>
                ✓ Matched Topics ({tutor.matched_topics.length})
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {tutor.matched_topics.length > 0 ? (
                  tutor.matched_topics.map((t) => (
                    <span key={t} className="demo-pill success" style={{ fontSize: "12px" }}>
                      {t}
                    </span>
                  ))
                ) : (
                  <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>No exact topic overlap</span>
                )}
              </div>
            </div>

            <div style={{ flex: 1, minWidth: "220px" }}>
              <div style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-muted)", marginBottom: "4px" }}>
                Additional Tutor Topics
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {tutor.unmatched_topics.map((t) => (
                  <span key={t} className="demo-pill" style={{ fontSize: "12px" }}>
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Score Breakdown */}
        <div style={{ marginBottom: "24px" }}>
          <div className="need-prop-label">Evaluation Metric Decomposition</div>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
            gap: "10px",
            marginTop: "8px"
          }}>
            <div className="criteria-cell" style={{ background: "var(--code-bg, #f9fafb)", padding: "10px", borderRadius: "6px" }}>
              <div className="criteria-cell-label">
                <span>Learning Need (45%)</span>
                <strong>{breakdown.learning_need_percentage}%</strong>
              </div>
              <div className="criteria-progress-track">
                <div className="criteria-progress-fill" style={{ width: `${breakdown.learning_need_percentage}%`, background: "#4f46e5" }} />
              </div>
            </div>

            <div className="criteria-cell" style={{ background: "var(--code-bg, #f9fafb)", padding: "10px", borderRadius: "6px" }}>
              <div className="criteria-cell-label">
                <span>Topic Match</span>
                <strong>{breakdown.topic_percentage}%</strong>
              </div>
              <div className="criteria-progress-track">
                <div className="criteria-progress-fill" style={{ width: `${breakdown.topic_percentage}%`, background: "#059669" }} />
              </div>
            </div>

            <div className="criteria-cell" style={{ background: "var(--code-bg, #f9fafb)", padding: "10px", borderRadius: "6px" }}>
              <div className="criteria-cell-label">
                <span>Fee / Budget (20%)</span>
                <strong>{breakdown.fee_percentage}%</strong>
              </div>
              <div className="criteria-progress-track">
                <div className="criteria-progress-fill" style={{ width: `${breakdown.fee_percentage}%`, background: breakdown.fee_percentage >= 80 ? "#059669" : "#f59e0b" }} />
              </div>
            </div>

            <div className="criteria-cell" style={{ background: "var(--code-bg, #f9fafb)", padding: "10px", borderRadius: "6px" }}>
              <div className="criteria-cell-label">
                <span>Availability (15%)</span>
                <strong>{breakdown.time_percentage}%</strong>
              </div>
              <div className="criteria-progress-track">
                <div className="criteria-progress-fill" style={{ width: `${breakdown.time_percentage}%`, background: "#3b82f6" }} />
              </div>
            </div>
          </div>
        </div>

        {/* Footer & Actions */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderTop: "1px solid var(--border-color, #e5e7eb)",
          paddingTop: "18px"
        }}>
          <div>
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              Evaluation Status: Controlled Demo Candidate
            </span>
          </div>

          <div style={{ display: "flex", gap: "10px" }}>
            <button className="btn btn-secondary" onClick={onClose} style={{ padding: "8px 18px" }}>
              Close
            </button>
            <button
              className="btn btn-primary"
              onClick={() => setBookingConfirmed(true)}
              style={{ padding: "8px 22px", background: bookingConfirmed ? "#059669" : "#4f46e5" }}
            >
              {bookingConfirmed ? "✓ Demo Booking Requested" : "Simulate Booking"}
            </button>
          </div>
        </div>

        {bookingConfirmed && (
          <div className="alert alert-success" style={{ marginTop: "14px", marginBottom: 0 }}>
            🎉 <strong>Demo Action Successful:</strong> Simulated booking request sent for <strong>{tutor.name}</strong>. (No live database records were altered).
          </div>
        )}
      </div>
    </div>
  );
}
