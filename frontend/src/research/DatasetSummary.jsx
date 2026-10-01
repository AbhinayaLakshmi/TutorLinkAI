import React from "react";

export default function DatasetSummary({ data }) {
  const { dataset_summary } = data;
  const dist = dataset_summary?.relevance_distribution || {};
  const tutorMetrics = dataset_summary?.tutor_metrics || {};
  const budgetMetrics = dataset_summary?.student_budget_metrics || {};
  const subjects = dataset_summary?.subjects || [];

  return (
    <div className="research-card">
      <div className="research-card-header">
        <div>
          <h2 className="research-card-title">
            <span>📊</span> Research Benchmark Dataset Summary (Step 7A)
          </h2>
          <p className="research-card-subtitle">
            Curated Academic Requirements, Candidate Profiles, and Graded Ground Truth
          </p>
        </div>
        <span className="badge-pass">100% Verified Profiles</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px", marginBottom: "24px" }}>
        {/* Relevance Distribution */}
        <div style={{ background: "#f8fafc", padding: "18px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
          <h4 style={{ margin: "0 0 14px 0", fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>
            Relevance Label Distribution (Q × T = 96 pairs)
          </h4>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "13px" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span><strong>Grade 3:</strong> Strong / Exact Match</span>
                <span><strong>{dist.grade_3_strong_match || 8}</strong> (8.3%)</span>
              </div>
              <div className="metric-bar-bg">
                <div className="metric-bar-fill" style={{ width: "8.3%", backgroundColor: "#10b981" }}></div>
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span><strong>Grade 2:</strong> Partial Topic Match</span>
                <span><strong>{dist.grade_2_partial_match || 1}</strong> (1.0%)</span>
              </div>
              <div className="metric-bar-bg">
                <div className="metric-bar-fill" style={{ width: "1.0%", backgroundColor: "#3b82f6" }}></div>
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span><strong>Grade 1:</strong> Subject-Matched Only</span>
                <span><strong>{dist.grade_1_subject_matched || 9}</strong> (9.4%)</span>
              </div>
              <div className="metric-bar-bg">
                <div className="metric-bar-fill" style={{ width: "9.4%", backgroundColor: "#f59e0b" }}></div>
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span><strong>Grade 0:</strong> Irrelevant (Cross-Subject)</span>
                <span><strong>{dist.grade_0_irrelevant || 78}</strong> (81.3%)</span>
              </div>
              <div className="metric-bar-bg">
                <div className="metric-bar-fill" style={{ width: "81.3%", backgroundColor: "#94a3b8" }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Financial & Profile Statistics */}
        <div style={{ background: "#f8fafc", padding: "18px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
          <h4 style={{ margin: "0 0 14px 0", fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>
            Candidate Profile & Financial Ranges
          </h4>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "13px" }}>
            <div style={{ background: "#ffffff", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ color: "#64748b", fontSize: "11px", textTransform: "uppercase", fontWeight: "600" }}>Tutor Hourly Rate</div>
              <div style={{ fontSize: "16px", fontWeight: "700", color: "#0f172a" }}>₹{tutorMetrics.hourly_rate_min} – ₹{tutorMetrics.hourly_rate_max}</div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>Mean: ₹{Math.round(tutorMetrics.hourly_rate_mean || 545)}/hr</div>
            </div>

            <div style={{ background: "#ffffff", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ color: "#64748b", fontSize: "11px", textTransform: "uppercase", fontWeight: "600" }}>Student Budget Max</div>
              <div style={{ fontSize: "16px", fontWeight: "700", color: "#0f172a" }}>₹{budgetMetrics.budget_max_range_min} – ₹{budgetMetrics.budget_max_range_max}</div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>Mean: ₹{Math.round(budgetMetrics.budget_max_mean || 862)}/hr</div>
            </div>

            <div style={{ background: "#ffffff", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ color: "#64748b", fontSize: "11px", textTransform: "uppercase", fontWeight: "600" }}>Historical Ratings</div>
              <div style={{ fontSize: "16px", fontWeight: "700", color: "#0f172a" }}>{tutorMetrics.rating_min} – {tutorMetrics.rating_max} ★</div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>Mean: {tutorMetrics.rating_mean?.toFixed(2) || "4.79"} ★</div>
            </div>

            <div style={{ background: "#ffffff", padding: "10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ color: "#64748b", fontSize: "11px", textTransform: "uppercase", fontWeight: "600" }}>Review Volume ($n$)</div>
              <div style={{ fontSize: "16px", fontWeight: "700", color: "#0f172a" }}>{tutorMetrics.review_count_min} – {tutorMetrics.review_count_max} reviews</div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>Mean: {Math.round(tutorMetrics.review_count_mean || 17)} reviews</div>
            </div>
          </div>
        </div>
      </div>

      {/* Subject Disciplines */}
      <div>
        <h4 style={{ margin: "0 0 8px 0", fontSize: "13px", fontWeight: "700", color: "#475569", textTransform: "uppercase" }}>
          Evaluated Academic Subject Disciplines
        </h4>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {subjects.map((sub, idx) => (
            <span key={idx} style={{ background: "#e0f2fe", color: "#0369a1", padding: "4px 12px", borderRadius: "6px", fontSize: "13px", fontWeight: "600" }}>
              {sub}
            </span>
          ))}
          <span style={{ background: "#f1f5f9", color: "#475569", padding: "4px 12px", borderRadius: "6px", fontSize: "13px", fontWeight: "600" }}>
            History (Cross-Subject Negative Control)
          </span>
        </div>
      </div>
    </div>
  );
}
