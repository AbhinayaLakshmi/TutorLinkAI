import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../services/auth";
import "../onboarding.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const { user } = await login(email, password);
      
      // Check onboarding completion state
      if (user.onboarding_status === "COMPLETED") {
        if (user.role === "STUDENT") {
          navigate("/dashboard/student");
        } else {
          navigate("/dashboard/tutor");
        }
      } else {
        if (user.role === "STUDENT") {
          navigate("/onboard/student");
        } else {
          navigate("/onboard/tutor");
        }
      }
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        "Incorrect email or password. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="onboard-container">
      <div className="onboard-card" style={{ maxWidth: "450px" }}>
        <h2 className="onboard-title">Log In</h2>
        <p className="onboard-subtitle">Sign in to manage your profile or requirements.</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jane@example.com"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <div className="btn-container" style={{ flexDirection: "column", gap: "12px" }}>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: "100%" }}
              disabled={loading}
            >
              {loading ? "Logging in..." : "Log In"}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ width: "100%" }}
              onClick={() => navigate("/register")}
              disabled={loading}
            >
              Create an Account
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
