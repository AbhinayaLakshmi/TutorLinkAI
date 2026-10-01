import React, { useState, useMemo } from "react";

export default function ColdStartAnalysis({ data }) {
  const coldStartData = data?.cold_start || [];

  const [selectedM, setSelectedM] = useState(5.0);
  const [selectedRawRating, setSelectedRawRating] = useState(5.0);

  const availableM = [1.0, 5.0, 10.0, 20.0];
  const availableRatings = [5.0, 4.5, 4.0, 3.0, 2.0];

  // Filter trajectory for selected m and selected raw rating
  const activeTrajectory = useMemo(() => {
    return coldStartData.filter(
      (item) =>
        item.smoothing_m === selectedM &&
        (item.raw_rating === selectedRawRating || item.review_count === 0)
    );
  }, [coldStartData, selectedM, selectedRawRating]);

  return (
    <div className="research-card">
      <div className="research-card-header">
        <div>
          <h2 className="research-card-title">
            <span>❄️</span> Cold-Start Robustness & Bayesian Shrinkage Analysis
          </h2>
          <p className="research-card-subtitle">
            Controlled Stress-Test of Reputation Regularization (Step 6B / 7C)
          </p>
        </div>
        <span className="badge-pass">Empirical Evidence Regularization</span>
      </div>

      {/* Mathematical Formulation Card */}
      <div style={{ background: "#f8fafc", padding: "18px", borderRadius: "8px", border: "1px solid #e2e8f0", marginBottom: "20px" }}>
        <h4 style={{ margin: "0 0 8px 0", fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>
          Bayesian M-Estimate Shrinkage Formulation
        </h4>
        <p style={{ margin: "0 0 12px 0", fontSize: "13px", color: "#475569", lineHeight: "1.5" }}>
          To prevent low-sample distortion (e.g. 1 review of 5.0 stars dominating established tutors), raw ratings (r̄) are regularized towards a global academic prior (μ = 3.5) weighted by pseudo-review prior evidence strength (m):
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px", fontFamily: "monospace", fontSize: "13px" }}>
          <div style={{ background: "#ffffff", padding: "12px", borderRadius: "6px", border: "1px solid #cbd5e1" }}>
            <strong style={{ color: "#0369a1" }}>Adjusted Rating:</strong><br />
            R̂(n, r̄) = (n · r̄ + m · μ) / (n + m)
          </div>
          <div style={{ background: "#ffffff", padding: "12px", borderRadius: "6px", border: "1px solid #cbd5e1" }}>
            <strong style={{ color: "#0369a1" }}>Feedback Confidence:</strong><br />
            Conf(n) = n / (n + m) ∈ [0.0, 1.0)
          </div>
        </div>
      </div>

      {/* Interactive Controls */}
      <div style={{ display: "flex", gap: "24px", flexWrap: "wrap", marginBottom: "20px", background: "#f1f5f9", padding: "14px 18px", borderRadius: "8px" }}>
        <div>
          <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "#334155", marginBottom: "6px" }}>
            Prior Smoothing Strength (m):
          </label>
          <div style={{ display: "flex", gap: "6px" }}>
            {availableM.map((mVal) => (
              <button
                key={mVal}
                onClick={() => setSelectedM(mVal)}
                style={{
                  padding: "4px 12px",
                  borderRadius: "4px",
                  fontSize: "12px",
                  fontWeight: selectedM === mVal ? "700" : "500",
                  background: selectedM === mVal ? "#0284c7" : "#ffffff",
                  color: selectedM === mVal ? "#ffffff" : "#334155",
                  border: "1px solid #cbd5e1",
                  cursor: "pointer"
                }}
              >
                m = {mVal} {mVal === 5.0 ? "(Default)" : ""}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "#334155", marginBottom: "6px" }}>
            Simulated Raw Rating (r̄):
          </label>
          <div style={{ display: "flex", gap: "6px" }}>
            {availableRatings.map((rVal) => (
              <button
                key={rVal}
                onClick={() => setSelectedRawRating(rVal)}
                style={{
                  padding: "4px 12px",
                  borderRadius: "4px",
                  fontSize: "12px",
                  fontWeight: selectedRawRating === rVal ? "700" : "500",
                  background: selectedRawRating === rVal ? "#0f172a" : "#ffffff",
                  color: selectedRawRating === rVal ? "#ffffff" : "#334155",
                  border: "1px solid #cbd5e1",
                  cursor: "pointer"
                }}
              >
                {rVal.toFixed(1)} ★
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Trajectory Visual Chart */}
      <div style={{ background: "#ffffff", padding: "18px", borderRadius: "8px", border: "1px solid #e2e8f0", marginBottom: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "14px" }}>
          <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>
            Shrinkage Convergence Trajectory (m={selectedM}, Raw = {selectedRawRating}★)
          </h4>
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            Global Mean μ = 3.50
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {activeTrajectory.map((pt) => {
            const adj = pt.adjusted_rating;
            // Scale bar between 1.0 and 5.0
            const pct = Math.max(0, Math.min(100, ((adj - 1.0) / 4.0) * 100));
            const confPct = (pt.confidence * 100).toFixed(0);

            return (
              <div key={pt.review_count} style={{ display: "grid", gridTemplateColumns: "80px 1fr 140px 100px", alignItems: "center", gap: "12px", fontSize: "12px" }}>
                <span style={{ fontWeight: "600", color: "#334155" }}>
                  {pt.review_count === 0 ? "0 (Cold)" : `${pt.review_count} reviews`}
                </span>
                <div>
                  <div className="metric-bar-bg" style={{ height: "10px" }}>
                    <div
                      className="metric-bar-fill"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: adj >= 4.0 ? "#10b981" : adj >= 3.0 ? "#3b82f6" : "#f59e0b",
                        height: "10px"
                      }}
                    ></div>
                  </div>
                </div>
                <div className="mono" style={{ fontWeight: "700", color: "#0f172a" }}>
                  Adjusted: {adj.toFixed(2)} ★
                </div>
                <div style={{ color: "#64748b" }}>
                  Conf: {confPct}%
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Trajectory Table */}
      <h4 style={{ margin: "0 0 10px 0", fontSize: "13px", fontWeight: "700", color: "#0f172a" }}>
        Numerical Shrinkage Table
      </h4>
      <div style={{ overflowX: "auto" }}>
        <table className="research-table">
          <thead>
            <tr>
              <th>Reviews (n)</th>
              <th>Raw Rating (r̄)</th>
              <th>Prior (m, μ)</th>
              <th>Adjusted Rating (R̂)</th>
              <th>Feedback Score (S_fb ∈ [0,1])</th>
              <th>Confidence (Conf)</th>
              <th>Shrinkage Distance (|r̄ - R̂|)</th>
            </tr>
          </thead>
          <tbody>
            {activeTrajectory.map((row) => (
              <tr key={row.review_count}>
                <td className="mono" style={{ fontWeight: "700" }}>{row.review_count}</td>
                <td>{typeof row.raw_rating === "number" ? `${row.raw_rating.toFixed(1)} ★` : row.raw_rating}</td>
                <td className="mono">m={row.smoothing_m}, μ={row.global_prior.toFixed(1)}</td>
                <td className="mono" style={{ fontWeight: "700", color: "#0369a1" }}>{row.adjusted_rating.toFixed(4)}</td>
                <td className="mono">{row.feedback_score.toFixed(4)}</td>
                <td className="mono">{(row.confidence * 100).toFixed(1)}%</td>
                <td className="mono">{row.distance_from_raw.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: "14px", background: "#f0fdf4", padding: "12px 16px", borderRadius: "6px", border: "1px solid #bbf7d0", fontSize: "12px", color: "#166534" }}>
        <strong>Key Research Insight:</strong> At n=0, a cold-start tutor is neither penalized nor artificially boosted; they receive default prior μ = 3.5 with Conf = 0%. At n=1 with a 5.0★ rating (m=5), adjusted score is shrunk to 3.75 (Conf=16.7%), ensuring that single-review anomalies cannot displace highly rated veteran educators.
      </div>
    </div>
  );
}
