import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  DEMO_STUDENT_NEED,
  getRankedDemoTutors,
  computeTutorScores
} from "../demo/demoData";
import TutorDetailModal from "../demo/TutorDetailModal";
import "../demo/demo.css";

export default function DemoRecommendations() {
  const navigate = useNavigate();

  // Controlled budget state for counterfactual simulation
  const [budget, setBudget] = useState(700);
  const [selectedTutorForModal, setSelectedTutorForModal] = useState(null);
  const [activeStep, setActiveStep] = useState(3); // 1: Profile, 2: Need, 3: Recommendations, 4: Explainability, 5: Counterfactual

  // Compute live ranking based on current budget
  const rankedTutors = getRankedDemoTutors(budget);
  const topTutor = rankedTutors[0];

  // Specific candidate C analysis (for static / dynamic comparison in Why This Tutor)
  const tutorC = rankedTutors.find((t) => t.id === "tutor-c") || topTutor;
  const tutorA = rankedTutors.find((t) => t.id === "tutor-a");

  const handlePresetBudget = (newBudget) => {
    setBudget(newBudget);
  };

  return (
    <div className="demo-wrapper">
      {/* 1. DEMO MODE HEADER & DISCLAIMER */}
      <div className="demo-banner">
        <div className="demo-banner-content">
          <span className="demo-banner-badge">DEMO MODE</span>
          <div className="demo-banner-text">
            <h1>TutorLinkAI — Intelligent Recommendation Engine</h1>
            <p>
              Academic Review Demo • Using controlled synthetic data to demonstrate multi-criteria semantic matching and explainability.
            </p>
          </div>
        </div>
        <div className="demo-banner-actions">
          <button
            onClick={() => navigate("/")}
            className="btn btn-secondary"
            style={{ color: "#ffffff", borderColor: "rgba(255,255,255,0.4)", padding: "6px 14px", fontSize: "13px" }}
          >
            ← Back to Home
          </button>
          <button
            onClick={() => {
              setBudget(700);
              setActiveStep(3);
            }}
            className="btn btn-secondary"
            style={{ color: "#ffffff", borderColor: "rgba(255,255,255,0.4)", padding: "6px 14px", fontSize: "13px" }}
          >
            🔄 Reset Demo
          </button>
        </div>
      </div>

      {/* 2. STEP FLOW BREADCRUMBS */}
      <div className="demo-flow-steps">
        <div className={`flow-step-item ${activeStep >= 1 ? "active" : ""}`} onClick={() => setActiveStep(1)} style={{ cursor: "pointer" }}>
          <span className="flow-step-circle">1</span>
          <span>Student Dashboard</span>
        </div>
        <span className="flow-step-arrow">→</span>

        <div className={`flow-step-item ${activeStep >= 2 ? "active" : ""}`} onClick={() => setActiveStep(2)} style={{ cursor: "pointer" }}>
          <span className="flow-step-circle">2</span>
          <span>Learning Need</span>
        </div>
        <span className="flow-step-arrow">→</span>

        <div className={`flow-step-item ${activeStep >= 3 ? "active" : ""}`} onClick={() => setActiveStep(3)} style={{ cursor: "pointer" }}>
          <span className="flow-step-circle">3</span>
          <span>AI Tutor Recommendations</span>
        </div>
        <span className="flow-step-arrow">→</span>

        <div className={`flow-step-item ${activeStep >= 4 ? "active" : ""}`} onClick={() => setActiveStep(4)} style={{ cursor: "pointer" }}>
          <span className="flow-step-circle">4</span>
          <span>Why This Tutor?</span>
        </div>
        <span className="flow-step-arrow">→</span>

        <div className={`flow-step-item ${activeStep >= 5 ? "active" : ""}`} onClick={() => setActiveStep(5)} style={{ cursor: "pointer" }}>
          <span className="flow-step-circle">5</span>
          <span>Counterfactual Lab</span>
        </div>
      </div>

      {/* 3. MAIN WORKSPACE GRID */}
      <div className="demo-main-grid">
        {/* LEFT COLUMN: Student Profile & Active Learning Need Context */}
        <div>
          {/* Student Profile Card */}
          <div className="demo-card">
            <div className="demo-card-header">
              <h3>🎓 Student Context</h3>
              <span className="demo-pill primary">Undergraduate</span>
            </div>

            <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "16px" }}>
              <div style={{
                width: "46px",
                height: "46px",
                borderRadius: "50%",
                background: "var(--social-bg, #f3f4f6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "22px",
                border: "1px solid var(--border-color, #e5e7eb)"
              }}>
                👨‍🎓
              </div>
              <div>
                <div style={{ fontWeight: "700", fontSize: "15px", color: "var(--text-h)" }}>
                  {DEMO_STUDENT_NEED.student_name}
                </div>
                <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  {DEMO_STUDENT_NEED.course}
                </div>
              </div>
            </div>

            <div className="need-prop-group">
              <div className="need-prop-label">Institution & Level</div>
              <div className="need-prop-value">{DEMO_STUDENT_NEED.student_level} (Year 2)</div>
            </div>

            <div className="need-prop-group">
              <div className="need-prop-label">Location / Mode</div>
              <div className="need-prop-value">{DEMO_STUDENT_NEED.location}</div>
            </div>
          </div>

          {/* Active Learning Need Card */}
          <div className="demo-card" style={{ border: "2px solid #6366f1" }}>
            <div className="demo-card-header">
              <h3>🎯 Active Learning Need</h3>
              <span className="demo-pill success">MATCH TARGET</span>
            </div>

            <div style={{ marginBottom: "14px" }}>
              <div style={{ fontWeight: "700", fontSize: "16px", color: "#4f46e5", marginBottom: "4px" }}>
                {DEMO_STUDENT_NEED.title}
              </div>
              <span className="demo-pill primary">Subject: {DEMO_STUDENT_NEED.subject}</span>
            </div>

            <div className="need-prop-group">
              <div className="need-prop-label">Target Topics</div>
              <div className="need-tag-cloud">
                {DEMO_STUDENT_NEED.topics.map((t) => (
                  <span key={t} className="demo-pill success" style={{ fontWeight: "700" }}>
                    ✓ {t}
                  </span>
                ))}
              </div>
            </div>

            <div className="need-prop-group">
              <div className="need-prop-label">Learning Goal (Semantic Query)</div>
              <div className="need-prop-value" style={{ fontSize: "13px", background: "var(--code-bg, #f9fafb)", padding: "8px 10px", borderRadius: "6px" }}>
                "{DEMO_STUDENT_NEED.learning_goal}"
              </div>
            </div>

            <div className="need-prop-group">
              <div className="need-prop-label">Pedagogy Preferences</div>
              <div className="need-tag-cloud">
                {DEMO_STUDENT_NEED.preferred_skills.map((s) => (
                  <span key={s} className="demo-pill">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            <div style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "10px",
              marginTop: "16px",
              borderTop: "1px solid var(--border-color, #e5e7eb)",
              paddingTop: "14px"
            }}>
              <div>
                <div className="need-prop-label">Maximum Budget</div>
                <div style={{ fontSize: "16px", fontWeight: "800", color: "#059669" }}>
                  ₹{budget} / hr
                </div>
              </div>
              <div>
                <div className="need-prop-label">Preferred Mode</div>
                <div style={{ fontSize: "14px", fontWeight: "600", color: "var(--text-h)" }}>
                  {DEMO_STUDENT_NEED.preferred_learning_mode}
                </div>
              </div>
            </div>
          </div>

          {/* Quick Academic Evaluation Notes */}
          <div className="demo-card" style={{ background: "var(--social-bg, #f8fafc)" }}>
            <div className="demo-card-header">
              <h3 style={{ fontSize: "14px" }}>🔬 Multi-Criteria Model</h3>
            </div>
            <p style={{ fontSize: "12px", color: "var(--text-muted)", lineHeight: "1.5" }}>
              The multi-criteria ranking model evaluates candidates using:
            </p>
            <ul style={{ paddingLeft: "18px", margin: "8px 0 0", fontSize: "12px", color: "var(--text-color)", lineHeight: "1.6" }}>
              <li><strong>45%</strong> Learning Need (S-BERT Semantic + Topic Overlap)</li>
              <li><strong>20%</strong> Fee / Budget Alignment</li>
              <li><strong>20%</strong> Location / Mode Suitability</li>
              <li><strong>15%</strong> Availability / Time Fit</li>
            </ul>
          </div>
        </div>

        {/* RIGHT COLUMN: Recommendations & Deep-Dives */}
        <div>
          {/* Recommendations Header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
            <div>
              <h2 style={{ fontSize: "22px", margin: "0 0 4px", fontWeight: "700", color: "var(--text-h)" }}>
                AI Tutor Recommendations
              </h2>
              <p style={{ fontSize: "14px", color: "var(--text-muted)", margin: 0 }}>
                Showing {rankedTutors.length} synthetic candidates ranked for <em>{DEMO_STUDENT_NEED.title}</em>
              </p>
            </div>
            <span className="demo-pill primary" style={{ fontSize: "12px", padding: "6px 12px" }}>
              Current Budget: ₹{budget}/hr
            </span>
          </div>

          {/* TUTOR CARDS LIST */}
          {rankedTutors.map((tutor, index) => {
            const isTop = index === 0;
            const { breakdown } = tutor;

            let scoreColorClass = "green";
            if (tutor.overall_percentage < 60) scoreColorClass = "gray";
            else if (tutor.overall_percentage < 80) scoreColorClass = "amber";

            return (
              <div
                key={tutor.id}
                className={`tutor-card ${isTop ? "is-top-pick" : ""}`}
              >
                {/* Top Bar */}
                <div className="tutor-card-topbar">
                  <div className="tutor-info-group">
                    <div className="tutor-avatar-circle">
                      {tutor.avatar}
                    </div>
                    <div className="tutor-meta">
                      <h3>
                        <span>#{index + 1} {tutor.name}</span>
                        {isTop && (
                          <span className="demo-pill primary" style={{ fontSize: "11px", fontWeight: "700" }}>
                            ⭐ TOP MATCH
                          </span>
                        )}
                        {!isTop && tutor.badge && (
                          <span className="demo-pill" style={{ fontSize: "10px" }}>
                            {tutor.badge}
                          </span>
                        )}
                      </h3>
                      <p className="tutor-subtitle">{tutor.title}</p>
                    </div>
                  </div>

                  <div className="score-badge">
                    <div className={`score-badge-number ${scoreColorClass}`}>
                      {tutor.overall_percentage}%
                    </div>
                    <div className="score-badge-label">Overall Match</div>
                  </div>
                </div>

                {/* Bio */}
                <p style={{ fontSize: "13px", color: "var(--text-color)", margin: "0 0 10px", lineHeight: "1.4" }}>
                  {tutor.bio}
                </p>

                {/* Topic Overlap Chips */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "12px" }}>
                  {tutor.matched_topics.map((t) => (
                    <span key={t} className="demo-pill success" style={{ fontSize: "11px" }}>
                      ✓ Topic Match: {t}
                    </span>
                  ))}
                  {tutor.unmatched_topics.map((t) => (
                    <span key={t} className="demo-pill" style={{ fontSize: "11px", opacity: 0.75 }}>
                      {t}
                    </span>
                  ))}
                </div>

                {/* Multi-Criteria Progress Bars */}
                <div className="criteria-breakdown-grid">
                  <div className="criteria-cell">
                    <div className="criteria-cell-label">
                      <span>Learning Need (45%)</span>
                      <span>{breakdown.learning_need_percentage}%</span>
                    </div>
                    <div className="criteria-progress-track">
                      <div className="criteria-progress-fill" style={{ width: `${breakdown.learning_need_percentage}%`, background: "#4f46e5" }} />
                    </div>
                  </div>

                  <div className="criteria-cell">
                    <div className="criteria-cell-label">
                      <span>Topic Match</span>
                      <span>{breakdown.topic_percentage}%</span>
                    </div>
                    <div className="criteria-progress-track">
                      <div className="criteria-progress-fill" style={{ width: `${breakdown.topic_percentage}%`, background: "#059669" }} />
                    </div>
                  </div>

                  <div className="criteria-cell">
                    <div className="criteria-cell-label">
                      <span>Budget Fit (20%)</span>
                      <span>{breakdown.fee_percentage}%</span>
                    </div>
                    <div className="criteria-progress-track">
                      <div
                        className="criteria-progress-fill"
                        style={{
                          width: `${breakdown.fee_percentage}%`,
                          background: breakdown.fee_percentage >= 80 ? "#059669" : "#f59e0b"
                        }}
                      />
                    </div>
                  </div>

                  <div className="criteria-cell">
                    <div className="criteria-cell-label">
                      <span>Availability (15%)</span>
                      <span>{breakdown.time_percentage}%</span>
                    </div>
                    <div className="criteria-progress-track">
                      <div className="criteria-progress-fill" style={{ width: `${breakdown.time_percentage}%`, background: "#3b82f6" }} />
                    </div>
                  </div>
                </div>

                {/* Explanation Callout Snippet */}
                <div className="tutor-explanation-box">
                  <strong>Recommendation Signal:</strong> {tutor.explanation_summary}
                </div>

                {/* Card Actions & Fee */}
                <div className="tutor-card-actions">
                  <div className="rate-display">
                    <span className="rate-amount">₹{tutor.hourly_rate}</span>
                    <span className="rate-unit">/ hour</span>
                    {tutor.hourly_rate <= budget ? (
                      <span style={{ fontSize: "12px", color: "#059669", fontWeight: "600", marginLeft: "6px" }}>
                        ✓ Within Budget
                      </span>
                    ) : (
                      <span style={{ fontSize: "12px", color: "#dc2626", fontWeight: "600", marginLeft: "6px" }}>
                        ⚠️ Exceeds Budget
                      </span>
                    )}
                  </div>

                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      onClick={() => setSelectedTutorForModal(tutor)}
                      className="btn btn-secondary"
                      style={{ padding: "8px 16px", fontSize: "13px" }}
                    >
                      View Tutor Details
                    </button>
                    <button
                      onClick={() => setSelectedTutorForModal(tutor)}
                      className="btn btn-primary"
                      style={{ padding: "8px 16px", fontSize: "13px" }}
                    >
                      Inspect Scores
                    </button>
                  </div>
                </div>
              </div>
            );
          })}

          {/* 4. "WHY THIS TUTOR?" EXPLAINABILITY DEEP DIVE SECTION */}
          <div className="explain-section" id="why-this-tutor">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h2 style={{ fontSize: "20px", margin: 0, color: "var(--text-h)", fontWeight: "700" }}>
                🔍 WHY THIS TUTOR? — Explainable AI Analysis
              </h2>
              <span className="demo-pill success">
                Focus: {topTutor.name}
              </span>
            </div>

            <p style={{ fontSize: "14px", color: "var(--text-muted)", margin: "0 0 16px", lineHeight: "1.5" }}>
              Our transparent matching architecture provides verifiable evidence for why <strong>{topTutor.name}</strong> was ranked highest for <em>{DEMO_STUDENT_NEED.title}</em>.
            </p>

            {/* Explainability Signals Checkmarks Grid */}
            <div className="explain-reasons-list">
              {topTutor.match_reasons.map((reason, idx) => (
                <div key={idx} className="explain-reason-item">
                  <span className="explain-reason-icon">✓</span>
                  <span>{reason}</span>
                </div>
              ))}
            </div>

            {/* Score Breakdown Table */}
            <div style={{
              background: "var(--code-bg, #f9fafb)",
              border: "1px solid var(--border-color, #e5e7eb)",
              borderRadius: "8px",
              padding: "16px",
              marginBottom: "18px"
            }}>
              <h4 style={{ margin: "0 0 12px", fontSize: "14px", color: "var(--text-h)" }}>
                Quantitative Score Decomposition
              </h4>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "12px" }}>
                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Learning Need</div>
                  <div style={{ fontSize: "18px", fontWeight: "700", color: "#4f46e5" }}>
                    {topTutor.breakdown.learning_need_percentage}%
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Topic Compatibility</div>
                  <div style={{ fontSize: "18px", fontWeight: "700", color: "#059669" }}>
                    {topTutor.breakdown.topic_percentage}%
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Budget Fit</div>
                  <div style={{ fontSize: "18px", fontWeight: "700", color: topTutor.breakdown.fee_percentage >= 80 ? "#059669" : "#f59e0b" }}>
                    {topTutor.breakdown.fee_percentage}%
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Availability</div>
                  <div style={{ fontSize: "18px", fontWeight: "700", color: "#3b82f6" }}>
                    {topTutor.breakdown.time_percentage}%
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Overall Match</div>
                  <div style={{ fontSize: "18px", fontWeight: "800", color: "#4f46e5" }}>
                    {topTutor.overall_percentage}%
                  </div>
                </div>
              </div>
            </div>

            {/* Mathematical Formulation */}
            <div className="formula-box">
              <div>// Production Weighting Formulation:</div>
              <div>Overall Score = (0.45 * LearningNeed) + (0.20 * Location) + (0.20 * Fee) + (0.15 * Time)</div>
              <div>LearningNeed = (0.50 * S-BERT Semantic Similarity) + (0.50 * Exact Topic Overlap)</div>
              <div style={{ color: "#a5b4fc", marginTop: "6px" }}>
                // Current Evaluation for {topTutor.name}: (0.45 * {topTutor.learning_need_score.toFixed(3)}) + (0.20 * {topTutor.location_score.toFixed(2)}) + (0.20 * {topTutor.current_fee_score.toFixed(2)}) + (0.15 * {topTutor.time_score.toFixed(2)}) = {topTutor.overall_score.toFixed(4)} ({topTutor.overall_percentage}%)
              </div>
            </div>
          </div>

          {/* 5. "COUNTERFACTUAL RECOMMENDATION" INTERACTIVE LAB */}
          <div className="counterfactual-lab" id="counterfactual-lab">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <h2 style={{ fontSize: "20px", margin: 0, color: "#92400e", fontWeight: "700" }}>
                🧪 Counterfactual Recommendation Lab
              </h2>
              <span className="demo-pill warning">Interactive Simulation</span>
            </div>

            <h3 style={{ fontSize: "15px", margin: "0 0 10px", color: "var(--text-h)" }}>
              "What would change your recommendation?"
            </h3>

            <p style={{ fontSize: "13px", color: "var(--text-color)", margin: "0 0 16px", lineHeight: "1.5" }}>
              Evaluate system sensitivity to student constraints. Adjust the budget slider below to simulate how financial constraints dynamically shift the top recommendation:
            </p>

            {/* Interactive Slider & Controls */}
            <div className="cf-controls">
              <div className="cf-slider-container">
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                  <span style={{ fontSize: "13px", fontWeight: "700" }}>Simulated Maximum Budget:</span>
                  <span style={{ fontSize: "15px", fontWeight: "800", color: "#d97706" }}>₹{budget} / hour</span>
                </div>
                <input
                  type="range"
                  min="350"
                  max="900"
                  step="50"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  className="cf-slider"
                />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                  <span>₹350/hr (Tight)</span>
                  <span>₹700/hr (Default)</span>
                  <span>₹900/hr (Flexible)</span>
                </div>
              </div>

              {/* Scenario Preset Buttons */}
              <div className="cf-preset-buttons">
                <button
                  type="button"
                  className={`cf-btn ${budget === 700 ? "active" : ""}`}
                  onClick={() => handlePresetBudget(700)}
                >
                  Default (₹700/hr)
                </button>
                <button
                  type="button"
                  className={`cf-btn ${budget === 500 ? "active" : ""}`}
                  onClick={() => handlePresetBudget(500)}
                >
                  Constrained (₹500/hr)
                </button>
                <button
                  type="button"
                  className={`cf-btn ${budget === 800 ? "active" : ""}`}
                  onClick={() => handlePresetBudget(800)}
                >
                  Higher Budget (₹800/hr)
                </button>
              </div>
            </div>

            {/* Dynamic Counterfactual Outcome Explanation */}
            {budget <= 500 ? (
              <div className="cf-result-banner">
                <strong>⚡ Counterfactual Shift Observed:</strong><br />
                When your maximum budget is reduced to <strong>₹{budget}/hour</strong>, <strong>Demo Physics Tutor A (₹500/hr)</strong> surpasses Dr. A. Ramanathan (Demo C, ₹650/hr) and becomes the <strong>#1 strongest recommendation</strong>. This happens because Tutor C incurs a fee overage penalty, whereas Tutor A satisfies all rotational dynamics topic constraints within the ₹500/hr threshold.
              </div>
            ) : budget >= 750 ? (
              <div className="cf-result-banner" style={{ background: "rgba(79, 70, 229, 0.08)", borderColor: "rgba(79, 70, 229, 0.3)", color: "#3730a3" }}>
                <strong>⚡ Counterfactual Sensitivity:</strong><br />
                At a higher budget of <strong>₹{budget}/hour</strong>, <strong>Dr. A. Ramanathan (Demo C)</strong> remains the decisive top recommendation (97% match) with maximum fee score headroom.
              </div>
            ) : (
              <div className="cf-result-banner">
                <strong>Standard Recommendation Scenario:</strong><br />
                At the default budget of <strong>₹700/hour</strong>, <strong>Dr. A. Ramanathan (Demo C, ₹650/hr)</strong> is the #1 candidate due to superior semantic topic alignment (100% topic match in Rotational Dynamics and dedicated exam prep).
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 6. MODAL FOR TUTOR DETAILS */}
      {selectedTutorForModal && (
        <TutorDetailModal
          tutor={selectedTutorForModal}
          currentBudget={budget}
          onClose={() => setSelectedTutorForModal(null)}
        />
      )}
    </div>
  );
}
