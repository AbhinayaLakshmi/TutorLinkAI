import React, { useState } from "react";

export default function ModelComparison({ data }) {
  const models = data?.model_comparison || [];
  const [selectedMetric, setSelectedMetric] = useState("ndcg@5");

  const metricMeta = {
    "precision@1": { label: "Precision@1", desc: "Fraction of queries with relevant top-1 recommendation" },
    "precision@3": { label: "Precision@3", desc: "Fraction of relevant items in top-3 cut-off" },
    "precision@5": { label: "Precision@5", desc: "Fraction of relevant items in top-5 cut-off" },
    "recall@5": { label: "Recall@5", desc: "Proportion of total relevant items retrieved in top-5" },
    "mrr": { label: "MRR", desc: "Mean Reciprocal Rank of first relevant item (1/rank)" },
    "ndcg@3": { label: "NDCG@3", desc: "Normalized Discounted Cumulative Gain at rank 3" },
    "ndcg@5": { label: "NDCG@5", desc: "Normalized Discounted Cumulative Gain at rank 5" },
    "pairwise_accuracy": { label: "Pairwise Accuracy", desc: "Concordance with graded ground-truth pairs" },
  };

  const metricKeys = Object.keys(metricMeta);

  // Helper to format float to 4 decimal places
  const fmt = (val) => (typeof val === "number" ? val.toFixed(4) : "—");
  const pct = (val) => (typeof val === "number" ? `${(val * 100).toFixed(1)}%` : "—");

  return (
    <div className="research-card">
      <div className="research-card-header">
        <div>
          <h2 className="research-card-title">
            <span>📈</span> Recommender Configurations Comparison
          </h2>
          <p className="research-card-subtitle">
            Offline Performance Across Standard Information Retrieval & Ranking Metrics
          </p>
        </div>
        <span className="badge-offline">5 Configurations Evaluated</span>
      </div>

      {/* Metric Selector Tabs */}
      <div style={{ marginBottom: "20px" }}>
        <div style={{ fontSize: "13px", fontWeight: "600", color: "#475569", marginBottom: "8px" }}>
          Select Metric to Compare Visually:
        </div>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {metricKeys.map((key) => {
            const isActive = selectedMetric === key;
            return (
              <button
                key={key}
                onClick={() => setSelectedMetric(key)}
                style={{
                  padding: "6px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: isActive ? "700" : "500",
                  backgroundColor: isActive ? "#1e293b" : "#f1f5f9",
                  color: isActive ? "#ffffff" : "#475569",
                  border: isActive ? "1px solid #0f172a" : "1px solid #cbd5e1",
                  cursor: "pointer",
                  transition: "all 0.15s ease"
                }}
              >
                {metricMeta[key].label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Visual Chart Comparison */}
      <div style={{ background: "#f8fafc", padding: "20px", borderRadius: "8px", border: "1px solid #e2e8f0", marginBottom: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "16px" }}>
          <div>
            <h4 style={{ margin: 0, fontSize: "15px", fontWeight: "700", color: "#0f172a" }}>
              {metricMeta[selectedMetric].label} Comparison
            </h4>
            <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#64748b" }}>
              {metricMeta[selectedMetric].desc}
            </p>
          </div>
          <span style={{ fontSize: "12px", color: "#64748b", fontFamily: "monospace" }}>Higher is better (0.00 – 1.00)</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {models.map((m, idx) => {
            const val = m[selectedMetric] || 0;
            const barWidth = `${Math.min(100, Math.max(2, val * 100))}%`;
            const isHybrid = m.model_id.includes("hybrid");
            const color = m.model_id === "full_hybrid_production" ? "#0284c7" : 
                          m.model_id === "full_hybrid_feedback_experimental" ? "#8b5cf6" : 
                          m.model_id === "dense_semantic_only" ? "#3b82f6" :
                          m.model_id === "topic_overlap_only" ? "#06b6d4" : "#64748b";

            return (
              <div key={m.model_id}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px", fontSize: "13px" }}>
                  <span style={{ fontWeight: isHybrid ? "700" : "500", color: isHybrid ? "#0f172a" : "#334155" }}>
                    {m.display_name}
                  </span>
                  <span style={{ fontWeight: "700", fontFamily: "monospace", color: color }}>
                    {fmt(val)} ({pct(val)})
                  </span>
                </div>
                <div className="metric-bar-bg" style={{ height: "12px" }}>
                  <div
                    className="metric-bar-fill"
                    style={{ width: barWidth, backgroundColor: color, height: "12px" }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Full Comparison Table */}
      <h4 style={{ margin: "0 0 12px 0", fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>
        Complete Offline Evaluation Metric Matrix
      </h4>
      <div style={{ overflowX: "auto" }}>
        <table className="research-table">
          <thead>
            <tr>
              <th style={{ textAlign: "left" }}>Configuration / Model</th>
              <th>P@1</th>
              <th>P@3</th>
              <th>P@5</th>
              <th>Recall@5</th>
              <th>MRR</th>
              <th>NDCG@3</th>
              <th>NDCG@5</th>
              <th>Pairwise Acc</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => {
              const isProduction = m.model_id === "full_hybrid_production";
              const isFeedback = m.model_id === "full_hybrid_feedback_experimental";
              
              return (
                <tr key={m.model_id} style={{ background: isProduction ? "#f0f9ff" : isFeedback ? "#faf5ff" : undefined }}>
                  <td style={{ textAlign: "left" }}>
                    <div style={{ fontWeight: "700", color: "#0f172a" }}>{m.display_name}</div>
                    <div style={{ fontSize: "11px", color: "#64748b" }}>
                      {m.subject_gate && "Subject Gate • "}
                      {m.semantic_embeddings && "Embeddings • "}
                      {m.topic_overlap && "Topic Overlap • "}
                      {m.location_scoring && "Location • "}
                      {m.fee_scoring && "Fee • "}
                      {m.time_scoring && "Time • "}
                      {m.bayesian_feedback ? `Bayesian Feedback (w=${m.feedback_weight})` : "No Feedback"}
                    </div>
                  </td>
                  <td className="mono">{fmt(m["precision@1"])}</td>
                  <td className="mono">{fmt(m["precision@3"])}</td>
                  <td className="mono">{fmt(m["precision@5"])}</td>
                  <td className="mono">{fmt(m["recall@5"])}</td>
                  <td className="mono">{fmt(m["mrr"])}</td>
                  <td className="mono">{fmt(m["ndcg@3"])}</td>
                  <td className="mono" style={{ fontWeight: "700", color: isProduction ? "#0284c7" : undefined }}>
                    {fmt(m["ndcg@5"])}
                  </td>
                  <td className="mono">{fmt(m["pairwise_accuracy"])}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: "12px", fontSize: "12px", color: "#64748b", fontStyle: "italic" }}>
        * Note: Models evaluated against 8 curated queries and 96 graded relevance judgments (Q × T). No arbitrary composite "AI Score" is computed; metrics follow standard IR evaluation definitions (TREC/CLEF).
      </div>
    </div>
  );
}
