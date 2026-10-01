"""
Publication Figure Generator for TutorLinkAI Research Evaluation.
Generates academic vector (SVG) and high-resolution raster (PNG, 300 DPI) figures for:
1. Model Ablation Metrics Comparison
2. Bayesian Cold-Start Shrinkage and Confidence Dynamics
3. Feedback-Weight Sensitivity and Ranking-Flip Trajectories
"""
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from evaluation.research.config import (
    RESULTS_DIR,
    FEEDBACK_SCENARIOS_PATH,
    ALL_MODELS,
    FEEDBACK_WEIGHT_SWEEP,
)
from evaluation.matching.evaluate_feedback_scenarios import (
    load_scenarios,
    run_scenario,
    run_ranking_flip_analysis,
)
from backend.app.services.feedback_score import calculate_feedback_signal

FIGURES_DIR = RESULTS_DIR / "figures"


def setup_matplotlib_style():
    """Configures clean, modern publication style."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 14,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.edgecolor": "#CCCCCC",
        "axes.linewidth": 0.8,
        "grid.color": "#E5E5E5",
        "grid.linestyle": "--",
        "grid.alpha": 0.7,
    })


def generate_ablation_figure() -> Dict[str, Path]:
    """
    Generates Model Ablation comparison chart (P@1, MRR, NDCG@3, NDCG@5, Pairwise Acc).
    """
    comp_json_path = RESULTS_DIR / "model_comparison.json"
    if not comp_json_path.exists():
        from evaluation.research.run_all_evaluations import run_all_research_evaluations
        run_all_research_evaluations()

    with open(comp_json_path, "r", encoding="utf-8") as f:
        model_rows = json.load(f)

    labels = ["Legacy Base", "Dense Semantic", "Topic Overlap", "Full Hybrid (Prod)", "Hybrid + Feedback"]
    p1 = [r["precision@1"] for r in model_rows]
    mrr = [r["mrr"] for r in model_rows]
    ndcg3 = [r["ndcg@3"] for r in model_rows]
    ndcg5 = [r["ndcg@5"] for r in model_rows]
    pw_acc = [r["pairwise_accuracy"] for r in model_rows]

    x = np.arange(len(labels))
    width = 0.16

    fig, ax = plt.subplots(figsize=(11, 6))

    rects1 = ax.bar(x - 2 * width, p1, width, label="Precision@1", color="#2563EB", alpha=0.9)
    rects2 = ax.bar(x - width, mrr, width, label="MRR", color="#059669", alpha=0.9)
    rects3 = ax.bar(x, ndcg3, width, label="NDCG@3", color="#D97706", alpha=0.9)
    rects4 = ax.bar(x + width, ndcg5, width, label="NDCG@5", color="#7C3AED", alpha=0.9)
    rects5 = ax.bar(x + 2 * width, pw_acc, width, label="Pairwise Accuracy", color="#DC2626", alpha=0.9)

    ax.set_ylabel("Evaluation Metric Score [0.0 - 1.0]")
    ax.set_title("Model Component Ablation & Retrieval Ranking Performance", pad=15, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontweight="bold")
    ax.set_ylim(0.80, 1.03)
    ax.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#DDD")

    # Add numeric labels on top of bars
    for rects in [rects1, rects2, rects3, rects4, rects5]:
        for bar in rects:
            height = bar.get_height()
            ax.annotate(
                f"{height:.2f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7,
                rotation=45,
            )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png_path = FIGURES_DIR / "ablation_metrics.png"
    svg_path = FIGURES_DIR / "ablation_metrics.svg"

    plt.savefig(png_path)
    plt.savefig(svg_path)
    plt.close(fig)

    return {"png": png_path, "svg": svg_path}


def generate_cold_start_figure() -> Dict[str, Path]:
    """
    Generates 2-panel Cold Start figure:
    Panel A: Rating Shrinkage curves toward prior mu=3.5 across review counts.
    Panel B: Evidence Confidence scaling across different smoothing m values.
    """
    counts = np.arange(0, 51)
    ratings = [5.0, 4.5, 4.0, 3.0, 2.0]
    smoothing_ms = [1.0, 5.0, 10.0, 20.0]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # --- Panel A: Rating Shrinkage (m=5.0, prior=3.5) ---
    colors = ["#1E40AF", "#0284C7", "#059669", "#D97706", "#DC2626"]
    for r, col in zip(ratings, colors):
        adj = []
        for n in counts:
            sig = calculate_feedback_signal(average_rating=r, review_count=n, smoothing_m=5.0, global_prior=3.5)
            adj.append(sig["adjusted_rating"])
        ax1.plot(counts, adj, label=f"Raw $\\bar{{r}} = {r:.1f}$ stars", color=col, linewidth=2)

    ax1.axhline(3.5, color="#6B7280", linestyle=":", label="Global Prior $\\mu = 3.5$ stars", linewidth=1.5)
    ax1.set_xlabel("Completed Review Count ($n$)")
    ax1.set_ylabel("Bayesian Adjusted Rating ($r_{\\text{adj}}$)")
    ax1.set_title("(A) Rating Shrinkage Dynamics ($m=5.0$)", fontweight="bold")
    ax1.set_xlim(0, 50)
    ax1.set_ylim(1.8, 5.2)
    ax1.legend(loc="center right", frameon=True, facecolor="white")

    # Annotate cold start point
    ax1.scatter([0], [3.5], color="#111827", zorder=5, s=40)
    ax1.annotate("Cold Start ($n=0$, $\\mu=3.5$)", xy=(0, 3.5), xytext=(5, 3.2),
                 arrowprops=dict(arrowstyle="->", color="#111827", lw=1), fontsize=8)

    # --- Panel B: Evidence Confidence Growth ---
    m_colors = ["#2563EB", "#059669", "#D97706", "#7C3AED"]
    for m, col in zip(smoothing_ms, m_colors):
        conf = [n / (n + m) for n in counts]
        ax2.plot(counts, conf, label=f"Smoothing $m = {m:.0f}$", color=col, linewidth=2)

    ax2.set_xlabel("Completed Review Count ($n$)")
    ax2.set_ylabel("Feedback Evidence Confidence ($C_{\\text{feedback}} \\in [0, 1)$)")
    ax2.set_title("(B) Review Evidence Confidence Scaling", fontweight="bold")
    ax2.set_xlim(0, 50)
    ax2.set_ylim(-0.02, 1.02)
    ax2.legend(loc="lower right", frameon=True, facecolor="white")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png_path = FIGURES_DIR / "cold_start_shrinkage.png"
    svg_path = FIGURES_DIR / "cold_start_shrinkage.svg"

    plt.savefig(png_path)
    plt.savefig(svg_path)
    plt.close(fig)

    return {"png": png_path, "svg": svg_path}


def generate_feedback_sensitivity_figure() -> Dict[str, Path]:
    """
    Generates 2-panel Sensitivity & Ranking Flip figure:
    Panel A: Score trajectories across weights for S1 (Quality vs Compat) & S2 (Cold Start vs Established).
    Panel B: Score trajectories across weights for S4 (Dominant Compat) & S5 (Similar Compat).
    """
    scenarios = load_scenarios(FEEDBACK_SCENARIOS_PATH)
    sc_map = {sc["scenario_id"]: sc for sc in scenarios}

    weights = np.array(FEEDBACK_WEIGHT_SWEEP)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # --- Panel A: Flip Scenarios (S1 & S2) ---
    s1 = sc_map.get("scenario_1_quality_vs_compatibility")
    if s1:
        s1_evals = [run_scenario(s1, w, 5.0) for w in weights]
        t1a_scores = [next(item["experimental_score"] for item in r if item["tutor_id"] == "tutor_1a") for r in s1_evals]
        t1b_scores = [next(item["experimental_score"] for item in r if item["tutor_id"] == "tutor_1b") for r in s1_evals]

        ax1.plot(weights, t1a_scores, "o-", color="#2563EB", label="S1 Tutor A (0.94 compat, 4.8 stars, n=30)", linewidth=2)
        ax1.plot(weights, t1b_scores, "s--", color="#DC2626", label="S1 Tutor B (0.96 compat, 3.2 stars, n=30)", linewidth=2)

    s2 = sc_map.get("scenario_2_cold_start_vs_established")
    if s2:
        s2_evals = [run_scenario(s2, w, 5.0) for w in weights]
        t2a_scores = [next(item["experimental_score"] for item in r if item["tutor_id"] == "tutor_2a") for r in s2_evals]
        t2b_scores = [next(item["experimental_score"] for item in r if item["tutor_id"] == "tutor_2b") for r in s2_evals]

        ax1.plot(weights, t2a_scores, "^-.", color="#D97706", label="S2 Tutor A (0.94 compat, 5.0 stars, n=1)", linewidth=1.8)
        ax1.plot(weights, t2b_scores, "d-", color="#059669", label="S2 Tutor B (0.93 compat, 4.7 stars, n=40)", linewidth=1.8)

    # Annotate flip threshold
    ax1.axvline(0.10, color="#6B7280", linestyle=":", alpha=0.8)
    ax1.annotate("S1 Flip ($w^*=0.10$)", xy=(0.10, 0.936), xytext=(0.14, 0.948),
                 arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.2), fontsize=8, color="#2563EB")

    ax1.set_xlabel("Feedback Weight ($w_{\\text{feedback}}$)")
    ax1.set_ylabel("Composite Experimental Score")
    ax1.set_title("(A) Ranking Flip Scenarios (S1 & S2)", fontweight="bold")
    ax1.legend(loc="lower left", frameon=True, facecolor="white", fontsize=8)

    # --- Panel B: Stability vs Dominance (S4 & S5) ---
    s4 = sc_map.get("scenario_4_strong_compat_vs_strong_feedback")
    if s4:
        s4_evals = [run_scenario(s4, w, 5.0) for w in weights]
        t4a_scores = [next(item["experimental_score"] for item in r if item["tutor_id"] == "tutor_4a") for r in s4_evals]
        t4b_scores = [next(item["experimental_score"] for item in r if item["tutor_id"] == "tutor_4b") for r in s4_evals]

        ax2.plot(weights, t4a_scores, "o-", color="#7C3AED", label="S4 Tutor A (0.98 compat, 3.5 stars, n=30)", linewidth=2)
        ax2.plot(weights, t4b_scores, "s--", color="#DB2777", label="S4 Tutor B (0.88 compat, 4.9 stars, n=30)", linewidth=2)

    s5 = sc_map.get("scenario_5_similar_compat_different_feedback")
    if s5:
        s5_evals = [run_scenario(s5, w, 5.0) for w in weights]
        t5a_scores = [next(item["experimental_score"] for item in r if item["tutor_id"] == "tutor_5a") for r in s5_evals]
        t5b_scores = [next(item["experimental_score"] for item in r if item["tutor_id"] == "tutor_5b") for r in s5_evals]

        ax2.plot(weights, t5a_scores, "^-", color="#059669", label="S5 Tutor A (0.91 compat, 4.9 stars, n=50)", linewidth=1.8)
        ax2.plot(weights, t5b_scores, "v-.", color="#EA580C", label="S5 Tutor B (0.90 compat, 3.8 stars, n=50)", linewidth=1.8)

    ax2.set_xlabel("Feedback Weight ($w_{\\text{feedback}}$)")
    ax2.set_ylabel("Composite Experimental Score")
    ax2.set_title("(B) Robustness vs Late Flip Scenarios (S4 & S5)", fontweight="bold")
    ax2.legend(loc="center left", frameon=True, facecolor="white", fontsize=8)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png_path = FIGURES_DIR / "feedback_sensitivity.png"
    svg_path = FIGURES_DIR / "feedback_sensitivity.svg"

    plt.savefig(png_path)
    plt.savefig(svg_path)
    plt.close(fig)

    return {"png": png_path, "svg": svg_path}


def generate_all_figures() -> Dict[str, Dict[str, Path]]:
    """Generates all publication-ready figures."""
    print("Generating publication figures in evaluation/research/results/figures/...")
    setup_matplotlib_style()

    fig_ablation = generate_ablation_figure()
    fig_cold = generate_cold_start_figure()
    fig_sens = generate_feedback_sensitivity_figure()

    outputs = {
        "ablation_metrics": fig_ablation,
        "cold_start_shrinkage": fig_cold,
        "feedback_sensitivity": fig_sens,
    }

    for name, paths in outputs.items():
        print(f"  - {paths['png'].name} (PNG 300 DPI) & {paths['svg'].name} (Vector SVG)")

    return outputs


def main():
    generate_all_figures()


if __name__ == "__main__":
    main()
