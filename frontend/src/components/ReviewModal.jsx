import React, { useState } from "react";
import api from "../services/api";

export default function ReviewModal({ session, onClose, onReviewSuccess }) {
  if (!session) return null;

  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [reviewText, setReviewText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!rating || rating < 1 || rating > 5) {
      setError("Please select a rating between 1 and 5 stars.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        rating: parseInt(rating, 10),
        review_text: reviewText.trim() || null,
      };

      const res = await api.post(`/api/reviews/${session.id}`, payload);
      if (onReviewSuccess) {
        onReviewSuccess(session.id, res.data);
      }
      onClose();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to submit review. Please try again."
      );
    } finally {
      setSubmitting(false);
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
        background: "rgba(15, 23, 42, 0.65)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        padding: "16px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !submitting) onClose();
      }}
    >
      <div
        style={{
          background: "var(--card-bg, #ffffff)",
          border: "1px solid var(--border-color, #e2e8f0)",
          borderRadius: "14px",
          width: "100%",
          maxWidth: "480px",
          padding: "24px 28px",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
          position: "relative",
          animation: "fadeIn 0.2s ease-out",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h3 style={{ margin: 0, fontSize: "18px", fontWeight: "700", color: "var(--text-h, #0f172a)" }}>
              How was your session?
            </h3>
            <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "var(--text-muted, #64748b)" }}>
              With <strong>{session.tutor_name || "your tutor"}</strong>
              {session.learning_need_title ? ` for ${session.learning_need_title}` : ""}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            style={{
              background: "transparent",
              border: "none",
              fontSize: "20px",
              cursor: submitting ? "not-allowed" : "pointer",
              color: "var(--text-muted, #64748b)",
              padding: "4px 8px",
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        {error && (
          <div
            style={{
              background: "rgba(239, 68, 68, 0.1)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              color: "#dc2626",
              padding: "10px 14px",
              borderRadius: "8px",
              fontSize: "13px",
              marginBottom: "16px",
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Star Rating Selection */}
          <div style={{ marginBottom: "20px", textAlign: "center" }}>
            <div style={{ fontSize: "12px", color: "var(--text-muted, #64748b)", textTransform: "uppercase", fontWeight: "600", marginBottom: "8px", letterSpacing: "0.5px" }}>
              Select Rating
            </div>
            <div style={{ display: "flex", justifyContent: "center", gap: "8px" }}>
              {[1, 2, 3, 4, 5].map((star) => {
                const isFilled = (hoverRating || rating) >= star;
                return (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    onMouseEnter={() => setHoverRating(star)}
                    onMouseLeave={() => setHoverRating(0)}
                    style={{
                      background: "transparent",
                      border: "none",
                      fontSize: "32px",
                      cursor: "pointer",
                      color: isFilled ? "#f59e0b" : "#cbd5e1",
                      transition: "transform 0.15s ease, color 0.15s ease",
                      transform: (hoverRating || rating) === star ? "scale(1.15)" : "scale(1)",
                      padding: "2px 4px",
                    }}
                    title={`${star} star${star > 1 ? "s" : ""}`}
                  >
                    ★
                  </button>
                );
              })}
            </div>
            <div style={{ fontSize: "13px", fontWeight: "600", color: "#d97706", marginTop: "4px" }}>
              {
                {
                  1: "Poor (1/5)",
                  2: "Fair (2/5)",
                  3: "Good (3/5)",
                  4: "Very Good (4/5)",
                  5: "Excellent (5/5)",
                }[hoverRating || rating]
              }
            </div>
          </div>

          {/* Feedback Textarea */}
          <div style={{ marginBottom: "20px" }}>
            <label
              style={{
                display: "block",
                fontSize: "13px",
                fontWeight: "600",
                color: "var(--text-h, #0f172a)",
                marginBottom: "6px",
              }}
            >
              Tell us about your experience <span style={{ fontSize: "11px", fontWeight: "normal", color: "var(--text-muted, #64748b)" }}>(optional)</span>
            </label>
            <textarea
              className="form-input"
              rows={4}
              placeholder="What went well? Was the tutor helpful and knowledgeable?"
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              maxLength={2000}
              style={{
                width: "100%",
                padding: "10px 12px",
                fontSize: "13px",
                borderRadius: "8px",
                border: "1px solid var(--border-color, #cbd5e1)",
                background: "var(--bg-color, #f8fafc)",
                resize: "vertical",
                boxSizing: "border-box",
                fontFamily: "inherit",
              }}
            />
          </div>

          {/* Footer Controls */}
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="btn btn-secondary"
              style={{ padding: "8px 18px", fontSize: "13px" }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="btn btn-primary"
              style={{ padding: "8px 22px", fontSize: "13px" }}
            >
              {submitting ? "Submitting..." : "Submit Review"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
