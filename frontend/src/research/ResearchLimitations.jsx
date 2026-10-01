import React from "react";

export default function ResearchLimitations({ data }) {
  const limitations = data?.limitations || [];

  const coreAcademicDisclaimers = [
    {
      title: "Controlled Synthetic Benchmark",
      badge: "Methodology Constraint",
      color: "#f59e0b",
      body: "The current evaluation dataset comprises 8 curated student queries and 12 candidate tutors. This dataset was constructed specifically to isolate and mathematically stress-test dense semantic retrieval, Jaccard curriculum matching, and Bayesian shrinkage dynamics under controlled conditions. It does not reflect the messy variance of uncurated production user logs."
    },
    {
      title: "Curated Ground-Truth Relevance Labels",
      badge: "Label Fidelity",
      color: "#3b82f6",
      body: "The 96 relevance judgments (Q × T) were systematically assigned according to formal CBSE/State Board and university curriculum rubrics. While rigorous and deterministic, human learning satisfaction in live tutoring depends on nuanced pedagogical rapport and real-time interaction quality that offline graded labels cannot fully capture."
    },
    {
      title: "Experimental Feedback Mechanism (Offline Only)",
      badge: "Production Boundary",
      color: "#8b5cf6",
      body: "Configuration E (Hybrid + Bayesian Feedback) is strictly an offline research experiment. The active TutorLinkAI production recommendation engine (Configuration D) does not incorporate historical ratings into candidate ranking scores. Production matching evaluates pure learner-tutor compatibility (needs, location, fee, schedule)."
    },
    {
      title: "Scope of Generalizability & Future Research",
      badge: "Future Work",
      color: "#10b981",
      body: "These empirical findings should not be directly generalized to entire multi-tier tutor populations without extensive live A/B testing. Future work will expand the benchmark to larger corpora ($N > 1000$), simulate temporal review arrival processes, and evaluate position-bias correction under online bandit learning."
    }
  ];

  return (
    <div className="research-card">
      <div className="research-card-header">
        <div>
          <h2 className="research-card-title">
            <span>⚠️</span> Research Limitations & Methodological Disclaimers
          </h2>
          <p className="research-card-subtitle">
            Academic Transparency, Evaluation Scope, and Production Isolation Boundaries
          </p>
        </div>
        <span className="badge-offline">Academic Disclosure</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px", marginBottom: "20px" }}>
        {coreAcademicDisclaimers.map((item, idx) => (
          <div
            key={idx}
            style={{
              background: "#ffffff",
              padding: "16px",
              borderRadius: "8px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 1px 3px rgba(0,0,0,0.05)"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>
                {item.title}
              </h4>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "700",
                  padding: "2px 8px",
                  borderRadius: "4px",
                  background: `${item.color}15`,
                  color: item.color
                }}
              >
                {item.badge}
              </span>
            </div>
            <p style={{ margin: 0, fontSize: "13px", color: "#475569", lineHeight: "1.5" }}>
              {item.body}
            </p>
          </div>
        ))}
      </div>

      {/* Structured Limitations from research data */}
      {limitations.length > 0 && (
        <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
          <h4 style={{ margin: "0 0 10px 0", fontSize: "13px", fontWeight: "700", color: "#334155" }}>
            Dataset & Pipeline Limitations Register (Step 7A/7B Data Dict):
          </h4>
          <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "12px", color: "#475569", display: "flex", flexDirection: "column", gap: "6px" }}>
            {limitations.map((lim, i) => (
              <li key={i}>
                <strong>{lim.category}:</strong> {lim.description}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
