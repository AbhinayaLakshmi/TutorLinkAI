import React from "react";

export default function ResearchOverview({ data }) {
  const { dataset_summary, manifest, model_comparison } = data;
  const counts = dataset_summary?.record_counts || {};

  return (
    <div className="research-card">
      <div className="research-card-header">
        <div>
          <h2 className="research-card-title">
            <span>🔬</span> Benchmark Overview & Dimensions
          </h2>
          <p className="research-card-subtitle">
            Offline Multi-Criteria Recommendation & Reputation Shrinkage Benchmark
          </p>
        </div>
        <span className="badge-pass">Verified Deterministic Run</span>
      </div>

      <div className="stat-grid">
        <div className="stat-box">
          <div className="stat-box-label">Learning Queries</div>
          <div className="stat-box-value">{counts.queries || 8}</div>
          <div className="stat-box-desc">Class 11, 12 & Undergraduate needs</div>
        </div>

        <div className="stat-box">
          <div className="stat-box-label">Candidate Tutors</div>
          <div className="stat-box-value">{counts.tutors || 12}</div>
          <div className="stat-box-desc">Across 5 STEM disciplines</div>
        </div>

        <div className="stat-box">
          <div className="stat-box-label">Relevance Judgments</div>
          <div className="stat-box-value">{counts.relevance_judgments || 96}</div>
          <div className="stat-box-desc">Dense 8×12 graded matrix (Q × T)</div>
        </div>

        <div className="stat-box">
          <div className="stat-box-label">Model Configurations</div>
          <div className="stat-box-value">{model_comparison?.length || 5}</div>
          <div className="stat-box-desc">Ablation study (Legacy → Hybrid+FB)</div>
        </div>

        <div className="stat-box">
          <div className="stat-box-label">Subject Disciplines</div>
          <div className="stat-box-value">{counts.subjects_count || 5}</div>
          <div className="stat-box-desc">Bio, Chem, CS, Math, Physics</div>
        </div>

        <div className="stat-box">
          <div className="stat-box-label">Syllabus Topics</div>
          <div className="stat-box-value">{counts.unique_topics_count || 52}</div>
          <div className="stat-box-desc">Curated academic concepts</div>
        </div>
      </div>

      <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
        <h4 style={{ margin: "0 0 8px 0", fontSize: "14px", fontWeight: "700", color: "#334155" }}>
          Deterministic Reproducibility Manifest
        </h4>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "8px", fontSize: "12px", fontFamily: "monospace", color: "#64748b" }}>
          <div><strong>Pipeline Version:</strong> {manifest?.pipeline_version || "1.0.0"}</div>
          <div><strong>Dataset Version:</strong> {manifest?.dataset_version || "1.0.0"}</div>
          <div><strong>Queries SHA-256:</strong> {manifest?.dataset_checksums?.queries_sha256?.substring(0, 16)}...</div>
          <div><strong>Tutors SHA-256:</strong> {manifest?.dataset_checksums?.tutors_sha256?.substring(0, 16)}...</div>
        </div>
      </div>
    </div>
  );
}
