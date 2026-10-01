import React, { useState } from "react";
import { Link } from "react-router-dom";
import researchData from "../research/data/researchData.json";
import "../research/research.css";

import ResearchOverview from "../research/ResearchOverview";
import DatasetSummary from "../research/DatasetSummary";
import ModelComparison from "../research/ModelComparison";
import AblationStudy from "../research/AblationStudy";
import ColdStartAnalysis from "../research/ColdStartAnalysis";
import FeedbackSensitivity from "../research/FeedbackSensitivity";
import RankingFlipAnalysis from "../research/RankingFlipAnalysis";
import ResearchLimitations from "../research/ResearchLimitations";

export default function ResearchEvaluation() {
  const [activeTab, setActiveTab] = useState("all");
  const [copiedCitation, setCopiedCitation] = useState(false);

  const bibtex = `@article{tutorlinkai2026research,
  title={TutorLinkAI: Offline Multi-Criteria Recommender Evaluation and Bayesian Reputation Shrinkage for Educational Matchmaking},
  author={TutorLinkAI Research Group},
  year={2026},
  publisher={Local Academic Benchmark Archive}
}`;

  const copyCitation = () => {
    navigator.clipboard.writeText(bibtex);
    setCopiedCitation(true);
    setTimeout(() => setCopiedCitation(false), 3000);
  };

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(researchData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "tutorlinkai_research_data.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const navTabs = [
    { id: "all", label: "📄 Full Report" },
    { id: "overview", label: "🔬 Overview" },
    { id: "dataset", label: "📊 Dataset (7A)" },
    { id: "models", label: "📈 Model Comparison (7B)" },
    { id: "ablation", label: "🧩 Ablation Study" },
    { id: "coldstart", label: "❄️ Cold-Start Shrinkage (6B)" },
    { id: "sensitivity", label: "⚖️ Feedback Simulator" },
    { id: "flips", label: "🔄 Ranking Flips" },
    { id: "limitations", label: "⚠️ Limitations" },
  ];

  return (
    <div className="research-page">
      {/* Header Banner */}
      <header className="research-header">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
              <span className="badge-offline">Offline Research Evaluation</span>
              <span style={{ fontSize: "12px", color: "#64748b" }}>Deterministic Snapshot (Steps 7A–7C)</span>
            </div>
            <h1 className="research-title">TutorLinkAI Research Evaluation Dashboard</h1>
            <p className="research-subtitle">
              Formal IR Evaluation of Multi-Criteria Tutor Matching, Hybrid Embeddings & Bayesian Shrinkage Dynamics
            </p>
          </div>

          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <button
              onClick={copyCitation}
              style={{
                background: "#ffffff",
                border: "1px solid #cbd5e1",
                padding: "8px 14px",
                borderRadius: "6px",
                fontSize: "13px",
                fontWeight: "600",
                color: "#334155",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px"
              }}
            >
              📋 {copiedCitation ? "Citation Copied!" : "Cite Benchmark"}
            </button>

            <button
              onClick={downloadJson}
              style={{
                background: "#0284c7",
                border: "none",
                padding: "8px 14px",
                borderRadius: "6px",
                fontSize: "13px",
                fontWeight: "600",
                color: "#ffffff",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px"
              }}
            >
              💾 Export JSON Dataset
            </button>

            <Link
              to="/"
              style={{
                background: "#f1f5f9",
                border: "1px solid #cbd5e1",
                padding: "8px 14px",
                borderRadius: "6px",
                fontSize: "13px",
                fontWeight: "600",
                color: "#334155",
                textDecoration: "none"
              }}
            >
              ← Back to Home
            </Link>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="research-nav" style={{ marginTop: "20px" }}>
          {navTabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`research-nav-tab ${isActive ? "active" : ""}`}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="research-main">
        {(activeTab === "all" || activeTab === "overview") && (
          <section id="overview" style={{ marginBottom: "28px" }}>
            <ResearchOverview data={researchData} />
          </section>
        )}

        {(activeTab === "all" || activeTab === "dataset") && (
          <section id="dataset" style={{ marginBottom: "28px" }}>
            <DatasetSummary data={researchData} />
          </section>
        )}

        {(activeTab === "all" || activeTab === "models") && (
          <section id="models" style={{ marginBottom: "28px" }}>
            <ModelComparison data={researchData} />
          </section>
        )}

        {(activeTab === "all" || activeTab === "ablation") && (
          <section id="ablation" style={{ marginBottom: "28px" }}>
            <AblationStudy data={researchData} />
          </section>
        )}

        {(activeTab === "all" || activeTab === "coldstart") && (
          <section id="coldstart" style={{ marginBottom: "28px" }}>
            <ColdStartAnalysis data={researchData} />
          </section>
        )}

        {(activeTab === "all" || activeTab === "sensitivity") && (
          <section id="sensitivity" style={{ marginBottom: "28px" }}>
            <FeedbackSensitivity data={researchData} />
          </section>
        )}

        {(activeTab === "all" || activeTab === "flips") && (
          <section id="flips" style={{ marginBottom: "28px" }}>
            <RankingFlipAnalysis data={researchData} />
          </section>
        )}

        {(activeTab === "all" || activeTab === "limitations") && (
          <section id="limitations" style={{ marginBottom: "28px" }}>
            <ResearchLimitations data={researchData} />
          </section>
        )}
      </main>

      {/* Footer */}
      <footer style={{ marginTop: "40px", padding: "24px 0", borderTop: "1px solid #e2e8f0", textAlign: "center", fontSize: "12px", color: "#64748b" }}>
        <p style={{ margin: "0 0 6px 0" }}>
          TutorLinkAI ML Recommender Systems Offline Evaluation • Step 7D Research Dashboard
        </p>
        <p style={{ margin: 0, fontFamily: "monospace" }}>
          Deterministic Evaluation Engine • Zero Live API / Backend Dependencies Required
        </p>
      </footer>
    </div>
  );
}
