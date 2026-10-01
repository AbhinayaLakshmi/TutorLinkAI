import React from "react";
import { useNavigate } from "react-router-dom";
import "../onboarding.css";

export default function LandingPage() {
  const navigate = useNavigate();

  const handleRoleSelect = (role) => {
    navigate(`/register?role=${role}`);
  };

  return (
    <div className="onboard-container">
      <div className="onboard-card" style={{ textAlign: "center", padding: "50px 30px" }}>
        <h1 style={{ fontSize: "36px", marginBottom: "12px", color: "var(--text-color)" }}>TutorLinkAI</h1>
        <p className="onboard-subtitle" style={{ fontSize: "16px", marginBottom: "40px" }}>
          Connecting students with skilled local tutors.
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "16px", maxWidth: "320px", margin: "0 auto 40px" }}>
          <button
            onClick={() => handleRoleSelect("STUDENT")}
            className="btn btn-primary"
            style={{ padding: "14px", fontSize: "16px" }}
          >
            I am a Student
          </button>
          <button
            onClick={() => handleRoleSelect("TUTOR")}
            className="btn btn-primary"
            style={{ padding: "14px", fontSize: "16px", backgroundColor: "#10b981" }}
          >
            I am a Tutor
          </button>
        </div>

        <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "24px" }}>
          <p style={{ fontSize: "14px", color: "var(--text-muted)", marginBottom: "12px" }}>
            Already have an account?
          </p>
          <button
            onClick={() => navigate("/login")}
            className="btn btn-secondary"
            style={{ padding: "8px 24px", fontSize: "14px", marginBottom: "16px" }}
          >
            Log In
          </button>
          
          <div style={{ marginTop: "12px", display: "flex", flexDirection: "column", gap: "10px", alignItems: "center" }}>
            <button
              onClick={() => navigate("/demo/recommendations")}
              className="btn"
              style={{
                width: "100%",
                maxWidth: "320px",
                padding: "10px 16px",
                fontSize: "14px",
                fontWeight: "600",
                background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
                color: "#ffffff",
                borderRadius: "6px",
                cursor: "pointer",
                boxShadow: "0 4px 10px rgba(79, 70, 229, 0.25)"
              }}
            >
              🚀 Launch AI Matching Demo (Academic Review)
            </button>

            <button
              onClick={() => navigate("/research")}
              className="btn"
              style={{
                width: "100%",
                maxWidth: "320px",
                padding: "10px 16px",
                fontSize: "14px",
                fontWeight: "600",
                background: "#0f172a",
                color: "#38bdf8",
                border: "1px solid #1e293b",
                borderRadius: "6px",
                cursor: "pointer",
                boxShadow: "0 4px 10px rgba(15, 23, 42, 0.2)"
              }}
            >
              📊 ML Research Evaluation Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
