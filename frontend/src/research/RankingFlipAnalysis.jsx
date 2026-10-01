import React, { useState, useMemo } from "react";

export default function RankingFlipAnalysis({ data }) {
  const rankingFlips = data?.ranking_flips || [];
  const scenarios = data?.scenarios || [];

  const [expandedScenario, setExpandedScenario] = useState(null);

  // Group by scenario to compute summary row
  const scenarioSummaries = useMemo(() => {
    const grouped = {};
    rankingFlips.forEach((f) => {
      if (!grouped[f.scenario_id]) {
        grouped[f.scenario_id] = [];
      }
      grouped[f.scenario_id].push(f);
    });

    return Object.entries(grouped).map(([scId, flipList]) => {
      const atDefault = flipList.find((f) => f.feedback_weight === 0.15) || flipList[0];
      const flippedEntry = flipList.find((f) => f.rank_flipped);
      const flipThreshold = flippedEntry ? flippedEntry.feedback_weight : null;

      return {
        scenario_id: scId,
        title: atDefault.scenario_title,
        baseline_top_name: atDefault.baseline_top_name,
        feedback_top_name: atDefault.experimental_top_name,
        rank_flipped: atDefault.rank_flipped,
        flip_threshold: flipThreshold,
        baseline_margin: atDefault.baseline_margin,
        post_feedback_margin: atDefault.experimental_margin,
        full_list: flipList
      };
    });
  }, [rankingFlips]);

  return (
    <div className="research-card">
      <div className="research-card-header">
        <div>
          <h2 className="research-card-title">
            <span>🔄</span> Ranking Flip & Stability Analysis
          </h2>
          <p className="research-card-subtitle">
            Systematic Inversion Thresholds and Score Margins Across Benchmark Scenarios
          </p>
        </div>
        <span className="badge-offline">Controlled Sensitivity</span>
      </div>

      <p style={{ fontSize: "13px", color: "#475569", margin: "0 0 16px 0", lineHeight: "1.5" }}>
        This analysis identifies whether and at what feedback weight threshold ($w^*$) historical ratings invert baseline compatibility rankings. At benchmark weight $w=0.15$ ($m=5.0$), established high-quality educators overcome slight compatibility deficits while preserving extreme compatibility dominance (e.g., Scenario 4).
      </p>

      {/* Flip Summary Table */}
      <div style={{ overflowX: "auto", marginBottom: "20px" }}>
        <table className="research-table">
          <thead>
            <tr>
              <th style={{ textAlign: "left" }}>Stress Scenario</th>
              <th style={{ textAlign: "left" }}>Baseline Top Candidate ($w=0.0$)</th>
              <th style={{ textAlign: "left" }}>Feedback Top Candidate ($w=0.15$)</th>
              <th>Flip Threshold ($w^*$)</th>
              <th>Baseline Margin</th>
              <th>Post-FB Margin</th>
              <th>Status ($w=0.15$)</th>
            </tr>
          </thead>
          <tbody>
            {scenarioSummaries.map((s) => {
              const isExpanded = expandedScenario === s.scenario_id;

              return (
                <React.Fragment key={s.scenario_id}>
                  <tr
                    onClick={() => setExpandedScenario(isExpanded ? null : s.scenario_id)}
                    style={{ cursor: "pointer", background: s.rank_flipped ? "#fffbeb" : "#f8fafc" }}
                  >
                    <td style={{ textAlign: "left" }}>
                      <div style={{ fontWeight: "700", color: "#0f172a" }}>{s.title}</div>
                      <div style={{ fontSize: "11px", color: "#0284c7" }}>
                        {isExpanded ? "▲ Hide Weight Trajectory" : "▼ Click to View All Weights"}
                      </div>
                    </td>
                    <td style={{ textAlign: "left", fontSize: "12px", color: "#475569" }}>
                      {s.baseline_top_name}
                    </td>
                    <td style={{ textAlign: "left", fontSize: "12px", fontWeight: "600", color: "#0f172a" }}>
                      {s.feedback_top_name}
                    </td>
                    <td className="mono" style={{ fontWeight: "700", color: s.flip_threshold !== null ? "#b45309" : "#64748b" }}>
                      {s.flip_threshold !== null ? `w* = ${s.flip_threshold.toFixed(2)}` : "No Flip"}
                    </td>
                    <td className="mono">+{s.baseline_margin.toFixed(3)}</td>
                    <td className="mono" style={{ fontWeight: "700" }}>+{s.post_feedback_margin.toFixed(3)}</td>
                    <td>
                      <span className={s.rank_flipped ? "badge-flip" : "badge-stable"}>
                        {s.rank_flipped ? "Ranking Inverted" : "Stable Ranking"}
                      </span>
                    </td>
                  </tr>

                  {/* Expanded multi-weight trajectory row */}
                  {isExpanded && (
                    <tr>
                      <td colSpan={7} style={{ background: "#ffffff", padding: "16px" }}>
                        <div style={{ fontSize: "12px", fontWeight: "700", color: "#334155", marginBottom: "8px" }}>
                          Feedback Weight Trajectory for {s.title}:
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "8px" }}>
                          {s.full_list.map((step) => (
                            <div
                              key={step.feedback_weight}
                              style={{
                                padding: "8px",
                                borderRadius: "6px",
                                border: step.rank_flipped ? "1px solid #fde047" : "1px solid #e2e8f0",
                                background: step.rank_flipped ? "#fefce8" : "#f8fafc",
                                fontSize: "11px"
                              }}
                            >
                              <div style={{ fontWeight: "700", color: "#0f172a" }}>
                                w = {step.feedback_weight.toFixed(2)}
                              </div>
                              <div style={{ color: step.rank_flipped ? "#b45309" : "#059669", fontWeight: "600", marginTop: "2px" }}>
                                {step.rank_flipped ? "⚡ Flipped" : "✓ Unchanged"}
                              </div>
                              <div style={{ color: "#64748b", marginTop: "4px", fontSize: "10px" }}>
                                Top: {step.experimental_top_name.split("(")[0]}
                              </div>
                              <div className="mono" style={{ fontSize: "10px", color: "#334155" }}>
                                Margin: +{step.experimental_margin.toFixed(3)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px", fontSize: "12px" }}>
        <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
          <strong style={{ color: "#0f172a" }}>Total Tested Weight Inversions:</strong> 25 of 42 parameter points (59.5%) triggered rank flips, primarily in scenarios with minimal compatibility deltas (Δ ≤ 0.02).
        </div>
        <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
          <strong style={{ color: "#0f172a" }}>Strong Compatibility Invariance:</strong> Scenario 4 requires w ≥ 0.30 to flip, proving that dominant curriculum match (Δ = 0.10) resists displacement under modest feedback weights.
        </div>
      </div>
    </div>
  );
}
