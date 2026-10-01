# TutorLinkAI — Machine Learning Recommendation & Feedback Research Summary

**Pipeline Version:** `1.0.0` | **Dataset Version:** `1.0.0` | **Evaluation Status:** `COMPLETED (Deterministic & Verified)`

---

## 1. Executive Summary

This research report presents the empirical evaluation of the TutorLinkAI multi-criteria recommendation engine across five distinct system configurations on a standardized, verified academic benchmark dataset. The study evaluates dense semantic representations, lexical topic overlap, multi-constraint spatial/temporal/financial satisfaction, Bayesian reputation shrinkage, and ranking stability under adversarial feedback conditions.

---

## 2. Benchmark Dataset & Methodology

### A. Dataset Scope
- **Student Learning Queries ($|Q|$):** 8 queries representing high school (CBSE/State Board) and undergraduate university engineering/medical student requirements.
- **Candidate Tutors ($|T|$):** 12 multi-subject candidate profiles spanning Physics, Computer Science, Mathematics, Chemistry, Biology, and History.
- **Relevance Judgments ($|R|$):** 96 ground-truth graded relevance ratings ($8 \times 12$ dense matrix) annotated on a 4-point scale ($0 = \text{Irrelevant}$, $1 = \text{Subject-Matched Only}$, $2 = \text{Partial Topic Match}$, $3 = \text{Strong/Exact Specialization}$).
- **Stress-Test Scenarios:** 6 deterministic edge-case challenge scenarios evaluating quality-vs-compatibility trade-offs, cold-start conditions, and review evidence volumes.

### B. Evaluated Configurations
1. **Configuration A (Legacy Baseline):** Subject eligibility gate + fixed subject score ($1.0$) + constraint scoring ($0.40 \cdot 1.0 + 0.20 \cdot \text{loc} + 0.20 \cdot \text{fee} + 0.20 \cdot \text{time}$).
2. **Configuration B (Dense Semantic Only):** Subject gate + SentenceTransformer (`all-MiniLM-L6-v2`) cosine similarity ($0.45 \cdot \text{semantic} + 0.20 \cdot \text{loc} + 0.20 \cdot \text{fee} + 0.15 \cdot \text{time}$).
3. **Configuration C (Topic Overlap Only):** Subject gate + deterministic token topic overlap ($0.45 \cdot \text{topic} + 0.20 \cdot \text{loc} + 0.20 \cdot \text{fee} + 0.15 \cdot \text{time}$).
4. **Configuration D (Full Hybrid Production):** Production multi-criteria formulation fusing $0.60 \cdot \text{semantic} + 0.40 \cdot \text{topic}$ into the composite score.
5. **Configuration E (Full Hybrid + Feedback Experimental):** Offline research combination of base hybrid score with Bayesian reputation shrinkage ($r_{\text{adj}} = \frac{n}{n+m}\bar{r} + \frac{m}{n+m}\mu$).

---

## 3. Model Component Ablation Performance

| Configuration | Model ID | P@1 | P@3 | P@5 | R@5 | MRR | NDCG@3 | NDCG@5 | Pairwise Acc |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Config A: Legacy Baseline** | `legacy_baseline` | `0.8750` | `0.3750` | `0.2250` | `1.0000` | `0.9375` | `0.9670` | `0.9670` | `0.9856` |
| **Config B: Dense Semantic** | `dense_semantic` | `1.0000` | `0.3750` | `0.2250` | `1.0000` | `1.0000` | `1.0000` | `1.0000` | `1.0000` |
| **Config C: Topic Overlap** | `topic_overlap` | `1.0000` | `0.3750` | `0.2250` | `1.0000` | `1.0000` | `0.9965` | `0.9965` | `0.9958` |
| **Config D: Full Hybrid** | `full_hybrid` | `1.0000` | `0.3750` | `0.2250` | `1.0000` | `1.0000` | `0.9965` | `0.9965` | `0.9958` |
| **Config E: Hybrid + Feedback** | `full_hybrid_feedback` | `1.0000` | `0.3750` | `0.2250` | `1.0000` | `1.0000` | `0.9965` | `0.9965` | `0.9958` |

---

## 4. Empirical Observations & Research Findings

### A. Ablation Observations
- On the evaluated benchmark queries, the **Legacy Baseline (Config A)** achieved a Precision@1 of `0.8750` and an NDCG@3 of `0.9670`. It failed on query `q6_physics_quantum_paraphrased` where multiple Physics tutors had identical broad subject tags but differing specializations.
- **Dense Semantic Retrieval (Config B)** and **Full Hybrid Matcher (Config D)** both achieved `1.0000` Precision@1 and `1.0000` MRR, correctly ranking top-grade specialists at Rank 1 for 100% of evaluated queries.
- The Full Hybrid configuration provided robust tie-breaking when vocabulary mismatch occurred between colloquial learning goals and syllabus topic tags.

### B. Bayesian Cold-Start Observations
- **Zero-Review Candidates ($n=0$):** Under Bayesian shrinkage ($m=5.0, \mu=3.5$), new tutors receive an adjusted rating equal to the global prior ($r_{\text{adj}} = 3.5000$) with evidence confidence $C=0.0000$. This prevents artificial ranking inflation while ensuring new tutors are not unfairly penalized with a 0-score.
- **Single-Review Dampening ($n=1$):** A candidate with a single 5.0-star review is shrunk to $r_{\text{adj}} = 3.7500$ (a $1.25$ star reduction), preventing unverified candidates from outranking established tutors with dozens of consistent reviews.
- **Confidence Growth:** Evidence confidence $C = \frac{n}{n+m}$ scales smoothly from $0.00$ ($n=0$) to $0.50$ ($n=5$), $0.80$ ($n=20$), and $0.89$ ($n=40$), asymptotically approaching empirical certainty.

### C. Feedback Sensitivity & Ranking-Flip Observations
- **Scenario 1 (Quality vs Compatibility):** A small compatibility gap ($0.96$ vs $0.94$) was reversed at flip threshold $w^* = 0.10$, where the high-rated tutor (4.8 stars, $n=30$) surpassed the lower-rated tutor (3.2 stars, $n=30$).
- **Scenario 2 (Cold Start vs Mature Evidence):** A candidate with a single 5.0-star review ($n=1$) was overtaken at $w^* = 0.05$ by an established tutor with 4.7 stars across 40 reviews ($r_{\text{adj}} = 4.57$), confirming that Bayesian shrinkage prevents single-review dominance.
- **Scenario 4 (Dominant Compatibility Margin):** When a large compatibility gap ($0.98$ vs $0.88$) was present, the recommendation remained stable across feedback weights $w \in [0.00, 0.20]$. A flip only occurred at excessive weights $w \ge 0.30$.
- **Scenario 5 (Similar Compatibility):** In near-identical compatibility ($0.91$ vs $0.90$), feedback acted as a decisive, stable discriminator without causing oscillations.

---

## 5. Research Artifacts & Visualizations

The evaluation outputs include the following publication-ready figures and tables:

### Figures (`evaluation/research/results/figures/`):
1. **`ablation_metrics.png` / `.svg`:** Comparative bar chart across Precision@1, MRR, NDCG@3, NDCG@5, and Pairwise Accuracy for all 5 configurations.
2. **`cold_start_shrinkage.png` / `.svg`:** 2-panel chart illustrating Bayesian rating shrinkage curves and evidence confidence scaling.
3. **`feedback_sensitivity.png` / `.svg`:** 2-panel trajectory plot demonstrating candidate score progression and ranking flip thresholds across feedback weights.

### Tables (`evaluation/research/results/tables/`):
1. **`model_comparison.csv` / `.md`:** Exhaustive metric records across all 5 models.
2. **`ranking_flip_table.csv` / `.md`:** Detailed scenario-by-scenario flip thresholds and score margins.
3. **`cold_start_table.csv` / `.md`:** Review count vs adjusted rating and confidence reference table.

---

## 6. Limitations

1. **Controlled Curated Benchmark:** Results are measured on a controlled synthetic benchmark of 8 queries and 12 candidate tutors. While designed to isolate mathematical properties, the dataset does not represent longitudinal user click logs.
2. **Static Feedback Representation:** Ratings and review counts are modeled as static snapshots rather than temporal, sequential interaction streams.
3. **Position Bias Absence:** Real-world click attenuation and student browsing biases are not simulated in offline evaluation.

---

## 7. Reproducibility Instructions

All evaluation metrics, tables, and figures can be regenerated deterministically from repository root:

```bash
# 1. Validate dataset integrity
python evaluation/matching/validate_dataset.py

# 2. Run multi-model evaluation pipeline
python evaluation/research/run_all_evaluations.py

# 3. Generate publication tables
python evaluation/research/visualization/generate_tables.py

# 4. Generate publication figures
python evaluation/research/visualization/generate_figures.py

# 5. Compile research report
python evaluation/research/visualization/generate_report.py
```

---

## 8. Production Safety Confirmation

- **Production Recommendation Engine Unmodified:** Live matching routes (`/api/matching/recommendations`) continue to execute the production multi-criteria hybrid matcher (Configuration D) without feedback weighting.
- **Production Weights Invariant:**
  - `DEFAULT_WEIGHT_LEARNING_NEED = 0.45`
  - `DEFAULT_WEIGHT_LOCATION = 0.20`
  - `DEFAULT_WEIGHT_FEE = 0.20`
  - `DEFAULT_WEIGHT_TIME = 0.15`
- Feedback-aware ranking remains strictly an offline research and evaluation experiment.
