import React from "react";

export default function AblationStudy({ data }) {
  const models = data?.model_comparison || [];

  const components = [
    { key: "subject_gate", label: "Subject Hard Gate", desc: "Filters out candidate tutors from unrelated academic disciplines" },
    { key: "semantic_embeddings", label: "Semantic Embeddings", desc: "Dense sentence-transformer representations of student goals vs tutor bio" },
    { key: "topic_overlap", label: "Topic Overlap (Jaccard)", desc: "Exact and substring matching across syllabus-level concept tags" },
    { key: "location_scoring", label: "Geographic Proximity", desc: "Spatial decay scoring based on city/locality alignment" },
    { key: "fee_scoring", label: "Budget Affinity", desc: "Linear affordability decay if tutor rate exceeds student budget limit" },
    { key: "time_scoring", label: "Time Slot Overlap", desc: "Availability match across weekday/weekend morning/evening slots" },
    { key: "bayesian_feedback", label: "Bayesian Feedback Shrinkage", desc: "Evidence-weighted reputation score shrunk towards global mean" }
  ];

  const architectures = [
    {
      id: "legacy_baseline",
      name: "Configuration A: Legacy Baseline",
      badge: "Rule-Based",
      badgeColor: "#64748b",
      summary: "Constraint-oriented baseline using strict subject filtering, price affinity, and spatial distance without semantic NLP.",
      strengths: "Fast computation, high recall on broad constraints.",
      weaknesses: "Fails to distinguish specific subtopic competence or conceptual nuances within a subject."
    },
    {
      id: "dense_semantic_only",
      name: "Configuration B: Dense Semantic Only",
      badge: "Embedding NLP",
      badgeColor: "#3b82f6",
      summary: "Pure dense vector similarity ($S_{emb}$) between student query descriptions and tutor qualification embeddings.",
      strengths: "Captures nuanced student needs and free-text intent effectively.",
      weaknesses: "Can drift across subject boundaries if embeddings overlap conceptually (e.g. math concepts in economics)."
    },
    {
      id: "topic_overlap_only",
      name: "Configuration C: Topic Overlap Only",
      badge: "Lexical Overlap",
      badgeColor: "#06b6d4",
      summary: "Discrete token and Jaccard topic-set intersection between syllabus topics tagged by student and tutor.",
      strengths: "High precision for exact curriculum topics (e.g., 'Thermodynamics', 'Organic Chemistry').",
      weaknesses: "Brittle against synonyms, paraphrasing, or varying syllabus naming conventions."
    },
    {
      id: "full_hybrid_production",
      name: "Configuration D: Full Hybrid Matcher",
      badge: "Production Engine",
      badgeColor: "#0284c7",
      summary: "Production engine combining Subject Gate + Dense Semantic (45%) + Location (20%) + Fee (20%) + Time Availability (15%).",
      strengths: "Optimal balance of semantic intent matching, hard curriculum alignment, and real-world logistics constraints.",
      weaknesses: "Evaluates compatibility only; does not factor historical student ratings or pedagogical reputation."
    },
    {
      id: "full_hybrid_feedback_experimental",
      name: "Configuration E: Hybrid + Bayesian Feedback",
      badge: "Experimental",
      badgeColor: "#8b5cf6",
      summary: "Experimental model blending Full Hybrid Compatibility ($1-w$) with Bayesian-shrunk Feedback Quality Score ($w$).",
      strengths: "Promotes proven high-quality tutors while regularizing low-evidence ratings to protect cold-start tutors.",
      weaknesses: "Introduces quality-vs-compatibility trade-offs; high reputation can occasionally outrank closer geographic matches."
    }
  ];

  return (
    <div className="research-card">
      <div className="research-card-header">
        <div>
          <h2 className="research-card-title">
            <span>🧩</span> Recommendation Ablation Study
          </h2>
          <p className="research-card-subtitle">
            Component-by-Component Architectural Dissection & Feature Matrix
          </p>
        </div>
        <span className="badge-offline">Ablation Analysis</span>
      </div>

      {/* Architectural Component Matrix */}
      <h4 style={{ margin: "0 0 12px 0", fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>
        Feature Matrix Across Configurations
      </h4>
      <div style={{ overflowX: "auto", marginBottom: "24px" }}>
        <table className="research-table">
          <thead>
            <tr>
              <th style={{ textAlign: "left", width: "240px" }}>Architectural Component</th>
              <th>Config A<br /><span style={{ fontSize: "11px", fontWeight: "normal" }}>Legacy</span></th>
              <th>Config B<br /><span style={{ fontSize: "11px", fontWeight: "normal" }}>Semantic</span></th>
              <th>Config C<br /><span style={{ fontSize: "11px", fontWeight: "normal" }}>Topic</span></th>
              <th style={{ background: "#e0f2fe" }}>Config D<br /><span style={{ fontSize: "11px", fontWeight: "normal", color: "#0284c7" }}>Production</span></th>
              <th style={{ background: "#f3e8ff" }}>Config E<br /><span style={{ fontSize: "11px", fontWeight: "normal", color: "#7e22ce" }}>Hybrid+FB</span></th>
            </tr>
          </thead>
          <tbody>
            {components.map((c) => (
              <tr key={c.key}>
                <td style={{ textAlign: "left" }}>
                  <div style={{ fontWeight: "600", color: "#0f172a" }}>{c.label}</div>
                  <div style={{ fontSize: "11px", color: "#64748b" }}>{c.desc}</div>
                </td>
                {models.map((m) => {
                  const active = m[c.key];
                  const isProd = m.model_id === "full_hybrid_production";
                  const isExp = m.model_id === "full_hybrid_feedback_experimental";
                  return (
                    <td
                      key={m.model_id}
                      style={{
                        background: isProd ? "#f0f9ff" : isExp ? "#faf5ff" : undefined,
                        color: active ? "#10b981" : "#cbd5e1",
                        fontSize: "16px",
                        fontWeight: "700"
                      }}
                    >
                      {active ? "✓" : "—"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Model Descriptions */}
      <h4 style={{ margin: "0 0 12px 0", fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>
        Component Rationale & Trade-Off Analysis
      </h4>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px" }}>
        {architectures.map((arch) => (
          <div
            key={arch.id}
            style={{
              background: "#ffffff",
              padding: "16px",
              borderRadius: "8px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 1px 3px rgba(0,0,0,0.05)"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <h5 style={{ margin: 0, fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>{arch.name}</h5>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "700",
                  padding: "2px 8px",
                  borderRadius: "4px",
                  background: `${arch.badgeColor}15`,
                  color: arch.badgeColor
                }}
              >
                {arch.badge}
              </span>
            </div>
            <p style={{ margin: "0 0 12px 0", fontSize: "13px", color: "#475569", lineHeight: "1.4" }}>
              {arch.summary}
            </p>
            <div style={{ fontSize: "12px", display: "flex", flexDirection: "column", gap: "4px" }}>
              <div><strong style={{ color: "#166534" }}>Strengths:</strong> <span style={{ color: "#475569" }}>{arch.strengths}</span></div>
              <div><strong style={{ color: "#991b1b" }}>Trade-offs:</strong> <span style={{ color: "#475569" }}>{arch.weaknesses}</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
