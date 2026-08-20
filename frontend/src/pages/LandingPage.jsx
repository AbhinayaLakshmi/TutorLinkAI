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
            style={{ padding: "8px 24px", fontSize: "14px" }}
          >
            Log In
          </button>
        </div>
      </div>
    </div>
  );
}
