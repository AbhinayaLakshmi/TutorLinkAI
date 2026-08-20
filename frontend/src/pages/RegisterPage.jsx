import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { register } from "../services/auth";
import "../onboarding.css";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [role, setRole] = useState("STUDENT");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const roleParam = searchParams.get("role");
    if (roleParam && (roleParam.toUpperCase() === "STUDENT" || roleParam.toUpperCase() === "TUTOR")) {
      setRole(roleParam.toUpperCase());
    }
  }, [searchParams]);

  const validateForm = () => {
    // 1. Password Strength
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return false;
    }
    if (!/[A-Z]/.test(password)) {
      setError("Password must contain at least one uppercase letter.");
      return false;
    }
    if (!/[a-z]/.test(password)) {
      setError("Password must contain at least one lowercase letter.");
      return false;
    }
    if (!/\d/.test(password)) {
      setError("Password must contain at least one number.");
      return false;
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      setError("Password must contain at least one special character.");
      return false;
    }

    // 2. Phone Digit Count
    const digitsOnly = phoneNumber.replace(/\D/g, "");
    if (digitsOnly.length !== 10) {
      setError("Phone number must contain exactly 10 digits.");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email || !password || !fullName || !phoneNumber) {
      setError("Please fill out all required fields.");
      return;
    }

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // 1. Register base account
      await register(email, password, fullName, phoneNumber, role);
      
      // 2. Redirect to OTP verification page
      navigate(`/verify-otp?email=${encodeURIComponent(email)}`);
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        "Something went wrong during registration. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="onboard-container">
      <div className="onboard-card">
        <h2 className="onboard-title">Create Account</h2>
        <p className="onboard-subtitle">Register to begin onboarding.</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Full Name *</label>
            <input
              type="text"
              className="form-input"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="e.g. Jane Doe"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Email Address *</label>
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. jane@example.com"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password *</label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
            <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "block", marginTop: "4px" }}>
              Must contain min 8 characters, 1 uppercase, 1 lowercase, 1 number, and 1 special symbol.
            </span>
          </div>

          <div className="form-group">
            <label className="form-label">Phone Number *</label>
            <input
              type="tel"
              className="form-input"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="e.g. 123-456-7890 (Exactly 10 digits)"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Registering as *</label>
            <div className="chip-container">
              <div
                className={`chip ${role === "STUDENT" ? "selected" : ""}`}
                onClick={() => setRole("STUDENT")}
              >
                Student
              </div>
              <div
                className={`chip ${role === "TUTOR" ? "selected" : ""}`}
                onClick={() => setRole("TUTOR")}
              >
                Tutor
              </div>
            </div>
          </div>

          <div className="btn-container">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate("/")}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? "Registering..." : "Create Account"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
