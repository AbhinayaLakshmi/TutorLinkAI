import React, { useState, useMemo } from "react";

export default function FeedbackSensitivity({ data }) {
  const scenarios = data?.scenarios || [];
  const rankingFlips = data?.ranking_flips || [];

  const [activeScenarioId, setActiveScenarioId] = useState(
    scenarios[0]?.scenario_id || "scenario_1_quality_vs_compatibility"
  );
  const [weight, setWeight] = useState(0.15);
  const smoothingM = 5.0;
  const globalPrior = 3.5;

  const currentScenario = useMemo(() => {
    return scenarios.find((s) => s.scenario_id === activeScenarioId) || scenarios[0];
  }, [scenarios, activeScenarioId]);

  // Compute live candidates ranking under current weight
  const candidateScores = useMemo(() => {
    if (!currentScenario || !currentScenario.candidates) return [];

    return currentScenario.candidates.map((c) => {
      const n = c.review_count;
      const raw = c.rating;
      let adjRating = globalPrior;

      if (n > 0 && raw !== null && raw !== undefined) {
        adjRating = (n * raw + smoothingM * globalPrior) / (n + smoothingM);
      }

      const fbScore = Math.max(0, Math.min(1, (adjRating - 1.0) / 4.0));
      const finalScore = (1 - weight) * c.hybrid_score + weight * fbScore;
      const baselineScore = c.hybrid_score;

      return {
        ...c,
        adjRating,
        fbScore,
        finalScore,
        baselineScore,
        hybridComponent: (1 - weight) * c.hybrid_score,
        fbComponent: weight * fbScore
      };
    }).sort((a, b) => b.finalScore - a.finalScore);
  }, [currentScenario, weight]);

  // Find flip point from ranking_flips data
  const scenarioFlips = useMemo(() => {
    return rankingFlips.filter((f) => f.scenario_id === activeScenarioId);
  }, [rankingFlips, activeScenarioId]);

  const flipThreshold = useMemo(() => {
    const flippedItem = scenarioFlips.find((f) => f.rank_flipped);
    return flippedItem ? flippedItem.feedback_weight : "No Flip";
  }, [scenarioFlips]);

  // Baseline top candidate
  const baselineWinner = useMemo(() => {
    if (!currentScenario || !currentScenario.candidates) return null;
    return [...currentScenario.candidates].sort((a, b) => b.hybrid_score - a.hybrid_score)[0];
  }, [currentScenario]);

  const currentWinner = candidateScores[0];
  const isCurrentlyFlipped = currentWinner && baselineWinner && currentWinner.tutor_id !== baselineWinner.tutor_id;

  return (
    <div className="research-card">
      <div className="research-card-header">
        <div>
          <h2 className="research-card-title">
            <span>⚖️</span> Feedback Sensitivity & Interactive Ranking Simulator
          </h2>
          <p className="research-card-subtitle">
            Dynamic Interpolation: S_comb = (1 - w) · S_hybrid + w · S_feedback
          </p>
        </div>
        <span className={isCurrentlyFlipped ? "badge-flip" : "badge-pass"}>
          {isCurrentlyFlipped ? "Rank Flipped (Quality Dominant)" : "Baseline Ranking Maintained"}
        </span>
      </div>

      {/* Scenario Selector */}
      <div style={{ marginBottom: "20px" }}>
        <div style={{ fontSize: "13px", fontWeight: "700", color: "#334155", marginBottom: "8px" }}>
          Select Stress-Test Scenario:
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "8px" }}>
          {scenarios.map((sc) => {
            const isSelected = sc.scenario_id === activeScenarioId;
            return (
              <button
                key={sc.scenario_id}
                onClick={() => setActiveScenarioId(sc.scenario_id)}
                style={{
                  textAlign: "left",
                  padding: "10px 14px",
                  borderRadius: "6px",
                  background: isSelected ? "#0f172a" : "#ffffff",
                  color: isSelected ? "#ffffff" : "#334155",
                  border: isSelected ? "1px solid #0f172a" : "1px solid #cbd5e1",
                  cursor: "pointer",
                  transition: "all 0.15s ease"
                }}
              >
                <div style={{ fontSize: "13px", fontWeight: "700" }}>{sc.title}</div>
                <div style={{ fontSize: "11px", color: isSelected ? "#cbd5e1" : "#64748b", marginTop: "2px" }}>
                  {sc.category}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Scenario Details & Weight Slider */}
      <div style={{ background: "#f8fafc", padding: "18px", borderRadius: "8px", border: "1px solid #e2e8f0", marginBottom: "20px" }}>
        <div style={{ marginBottom: "16px" }}>
          <h4 style={{ margin: "0 0 4px 0", fontSize: "15px", fontWeight: "700", color: "#0f172a" }}>
            {currentScenario?.title}
          </h4>
          <p style={{ margin: 0, fontSize: "13px", color: "#475569" }}>
            <strong>Evaluation Objective:</strong> {currentScenario?.purpose}
          </p>
        </div>

        {/* Feedback Weight Slider */}
        <div style={{ background: "#ffffff", padding: "14px 18px", borderRadius: "6px", border: "1px solid #cbd5e1" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <span style={{ fontSize: "13px", fontWeight: "700", color: "#0f172a" }}>
              Feedback Weight ($w$): <span className="mono" style={{ color: "#0284c7" }}>{weight.toFixed(2)}</span>
            </span>
            <span style={{ fontSize: "12px", color: "#64748b" }}>
              Hybrid Share: <strong>{((1 - weight) * 100).toFixed(0)}%</strong> | Feedback Share: <strong>{(weight * 100).toFixed(0)}%</strong>
            </span>
          </div>

          <input
            type="range"
            min="0.00"
            max="0.40"
            step="0.01"
            value={weight}
            onChange={(e) => setWeight(parseFloat(e.target.value))}
            style={{ width: "100%", cursor: "pointer", accentColor: "#0284c7" }}
          />

          <div style={{ display: "flex", justifyContent: "space-between", marginTop: "6px", fontSize: "11px", color: "#64748b" }}>
            <span>w = 0.00 (Pure Baseline)</span>
            <span>w = 0.05</span>
            <span>w = 0.10 (Flip Point S1, S3)</span>
            <span>w = 0.15 (Balanced)</span>
            <span>w = 0.20</span>
            <span>w = 0.30 (Flip Point S4)</span>
            <span>w = 0.40 (Heavy FB)</span>
          </div>

          {/* Quick preset buttons */}
          <div style={{ display: "flex", gap: "6px", marginTop: "10px" }}>
            {[0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4].map((preset) => (
              <button
                key={preset}
                onClick={() => setWeight(preset)}
                style={{
                  padding: "3px 8px",
                  borderRadius: "4px",
                  fontSize: "11px",
                  background: weight === preset ? "#0284c7" : "#f1f5f9",
                  color: weight === preset ? "#ffffff" : "#475569",
                  border: "1px solid #cbd5e1",
                  cursor: "pointer"
                }}
              >
                w={preset.toFixed(2)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Dynamic Ranking Comparison */}
      <h4 style={{ margin: "0 0 12px 0", fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>
        Simulated Candidate Ranking (At $w = {weight.toFixed(2)}$)
      </h4>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "14px", marginBottom: "20px" }}>
        {candidateScores.map((cand, rankIdx) => {
          const isWinner = rankIdx === 0;
          return (
            <div
              key={cand.tutor_id}
              style={{
                background: isWinner ? "#f0f9ff" : "#ffffff",
                padding: "16px",
                borderRadius: "8px",
                border: isWinner ? "2px solid #0284c7" : "1px solid #e2e8f0",
                boxShadow: isWinner ? "0 4px 6px -1px rgba(2, 132, 199, 0.1)" : "none"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                <div>
                  <span
                    style={{
                      display: "inline-block",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontWeight: "700",
                      background: isWinner ? "#0284c7" : "#64748b",
                      color: "#ffffff",
                      marginBottom: "4px"
                    }}
                  >
                    Rank #{rankIdx + 1} {isWinner ? "• Top Candidate" : ""}
                  </span>
                  <div style={{ fontSize: "14px", fontWeight: "700", color: "#0f172a" }}>{cand.name}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div className="mono" style={{ fontSize: "18px", fontWeight: "800", color: isWinner ? "#0284c7" : "#334155" }}>
                    {cand.finalScore.toFixed(4)}
                  </div>
                  <div style={{ fontSize: "11px", color: "#64748b" }}>Final Score</div>
                </div>
              </div>

              {/* Score Breakdown Bar */}
              <div style={{ margin: "10px 0" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#64748b", marginBottom: "2px" }}>
                  <span>Hybrid: {(cand.hybridComponent).toFixed(3)}</span>
                  <span>Feedback: {(cand.fbComponent).toFixed(3)}</span>
                </div>
                <div style={{ display: "flex", height: "8px", borderRadius: "4px", overflow: "hidden", background: "#e2e8f0" }}>
                  <div style={{ width: `${(cand.hybridComponent / cand.finalScore) * 100}%`, background: "#3b82f6" }} title="Hybrid Component"></div>
                  <div style={{ width: `${(cand.fbComponent / cand.finalScore) * 100}%`, background: "#8b5cf6" }} title="Feedback Component"></div>
                </div>
              </div>

              {/* Profile Stats */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px", fontSize: "11px", background: "#f8fafc", padding: "8px", borderRadius: "6px" }}>
                <div>
                  <span style={{ color: "#64748b" }}>Raw Rating:</span><br />
                  <strong>{cand.rating !== null ? `${cand.rating.toFixed(1)} ★` : "0 (Cold)"}</strong>
                </div>
                <div>
                  <span style={{ color: "#64748b" }}>Reviews ($n$):</span><br />
                  <strong>{cand.review_count}</strong>
                </div>
                <div>
                  <span style={{ color: "#64748b" }}>Shrunk Rating (R̂):</span><br />
                  <strong>{cand.adjRating.toFixed(2)} ★</strong>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Flip summary note */}
      <div style={{ background: "#f8fafc", padding: "12px 16px", borderRadius: "6px", border: "1px solid #e2e8f0", fontSize: "12px", color: "#475569" }}>
        <strong>Scenario Theoretical Threshold:</strong> {typeof flipThreshold === "number" ? `Rank inversion threshold occurs at feedback weight w* = ${flipThreshold.toFixed(2)}.` : "Ranking remains stable across all tested weights w ∈ [0.00, 0.40]."}
      </div>
    </div>
  );
}
