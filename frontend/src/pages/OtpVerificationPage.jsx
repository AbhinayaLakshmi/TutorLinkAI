import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import api from "../services/api";
import "../onboarding.css";

export default function OtpVerificationPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const email = searchParams.get("email") || "";
  
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (!email) {
      navigate("/login");
    }
  }, [email, navigate]);

  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  const handleVerify = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    if (otp.length !== 6 || !/^\d+$/.test(otp)) {
      setError("Please enter a valid 6-digit numeric OTP.");
      setLoading(false);
      return;
    }

    try {
      const res = await api.post("/api/auth/verify-otp", {
        email,
        otp,
      });

      const { access_token, user } = res.data;
      localStorage.setItem("token", access_token);
      localStorage.setItem("user", JSON.stringify(user));

      setSuccess("Email verified successfully! Starting onboarding...");
      setTimeout(() => {
        if (user.role === "STUDENT") {
          navigate("/onboard/student");
        } else {
          navigate("/onboard/tutor");
        }
      }, 1500);
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        "Invalid or expired OTP. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError("");
    setSuccess("");
    
    try {
      await api.post("/api/auth/resend-otp", { email });
      setSuccess("A new OTP has been sent to your email.");
      setCooldown(60); // 60 seconds cooldown
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        "Failed to resend OTP. Please try again later."
      );
    }
  };

  return (
    <div className="onboard-container">
      <div className="onboard-card" style={{ maxWidth: "450px" }}>
        <h2 className="onboard-title">Email Verification</h2>
        <p className="onboard-subtitle">We sent a 6-digit verification code to:</p>
        <p style={{ fontWeight: "600", textAlign: "center", marginBottom: "20px" }}>{email}</p>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <form onSubmit={handleVerify}>
          <div className="form-group">
            <label className="form-label">Verification Code (OTP)</label>
            <input
              type="text"
              maxLength={6}
              className="form-input"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
              placeholder="e.g. 123456"
              style={{ fontSize: "20px", letterSpacing: "8px", textAlign: "center" }}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%", padding: "12px", marginTop: "10px" }}
            disabled={loading}
          >
            {loading ? "Verifying..." : "Verify & Continue"}
          </button>
        </form>

        <div style={{ marginTop: "24px", textAlign: "center", borderTop: "1px solid var(--border-color)", paddingTop: "20px" }}>
          <button
            onClick={handleResend}
            className="btn btn-secondary"
            disabled={cooldown > 0}
            style={{ width: "100%", padding: "10px" }}
          >
            {cooldown > 0 ? `Resend OTP (${cooldown}s)` : "Resend Verification Code"}
          </button>
        </div>
      </div>
    </div>
  );
}
