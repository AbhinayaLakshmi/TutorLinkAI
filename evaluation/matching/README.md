# TutorLinkAI — Offline Matching Evaluation Harness & Feedback Signal Foundation

This directory contains the reproducible offline evaluation harness for the TutorLinkAI recommendation engine, supporting empirical ablation studies between the historical baseline, dense semantic matching, topic overlap, full hybrid matching, and experimental Bayesian feedback signals.

---

## 1. Purpose

The purpose of this framework is to provide a standardized, deterministic, and isolated offline benchmark for measuring tutor recommendation ranking quality. The harness operates strictly on local JSON dataset files without interacting with the active database, backend routes, or live networks.

---

## 2. Research Benchmark Data Notice

> [!IMPORTANT]
> **Dataset Provenance & Research Classification:**
> All queries, tutor profiles, review counts, and relevance judgments contained in `queries.json`, `tutors.json`, and `qrels.json` are **curated research benchmark data**. They are designed to model realistic academic scenarios (spanning Physics, Computer Science, Mathematics, Chemistry, and Biology) but do **not** represent production user click logs or real-world student identity data.
>
> Review volume and ratings annotated in `tutors.json` are controlled synthetic values representing distinct lifecycle conditions (cold-start $n=0$, sparse $n=1..5$, and mature feedback $n \ge 20$).

---

## 3. Data Format

### A. `queries.json`
Represents student learning needs with academic context and search constraints:
```json
{
  "query_id": "q1_physics_rotational",
  "subject": "Physics",
  "subjects_needed": "Physics",
  "topics": ["Rotational Motion", "Mechanics", "Angular Momentum"],
  "learning_goals": "Master rotational dynamics and problem solving",
  "preferred_tutor_characteristics": "Patient, step-by-step mathematical derivations",
  "student_level": "High School (Class 12)",
  "preferred_learning_mode": "Online",
  "preferred_tutor_languages": ["English"],
  "latitude": 13.0827,
  "longitude": 80.2707,
  "budget_min": 400.0,
  "budget_max": 800.0,
  "preferred_slots": [{"day": "Monday", "start_time": "16:00", "end_time": "18:00"}]
}
```

### B. `tutors.json`
Represents candidate tutor profiles with controlled capability and feedback descriptors:
```json
{
  "tutor_id": "t_phys_rotational_expert",
  "name": "Dr. Subhash (Physics)",
  "subjects": ["Physics"],
  "subjects_taught": ["Physics"],
  "topics_expertise": ["Rotational Motion", "Mechanics", "Angular Momentum"],
  "skills": ["Mathematical derivations", "Step-by-step problem solving"],
  "student_levels": ["High School (Class 12)", "Undergraduate"],
  "languages_can_teach_in": ["English"],
  "preferred_teaching_mode": "Online",
  "hourly_rate": 550.0,
  "latitude": 13.0827,
  "longitude": 80.2707,
  "location": "Chennai Central",
  "availability": [{"day": "Monday", "start_time": "15:00", "end_time": "19:00"}],
  "rating": 4.9,
  "review_count": 28,
  "years_of_experience": 8,
  "is_verified": true
}
```

### C. `qrels.json`
Ground-truth graded relevance matrix:
- **0 = Irrelevant:** Candidate is outside the requested subject domain (cross-subject).
- **1 = Subject-Matched Only:** Candidate teaches the requested subject, but has distinct or unrelated topic expertise.
- **2 = Partial Match:** Candidate covers related subfields or partially overlaps topic/goals.
- **3 = Strong / Exact Match:** Candidate specializes precisely in the requested topics, aligned pedagogical style, and requested mode/level.

---

## 4. Experimental Configurations & Formulas

The evaluation harness implements five distinct configurations:

### Configuration A: Legacy Baseline
Reconstructs the historical system without semantic or topic scoring:
1. Candidate passes Stage 1 Subject Eligibility Gate (`evaluate_subject_gate`).
2. Eligible candidates receive fixed $\text{subject\_score} = 1.0$.
3. Composite Score:
   $$\text{Score}_{\text{baseline}} = 0.40 \times 1.0 + 0.20 \times \text{location} + 0.20 \times \text{fee} + 0.20 \times \text{time}$$

### Configuration B: Dense Semantic Only
Measures the standalone contribution of dense SentenceTransformers (`all-MiniLM-L6-v2`) cosine similarity:
$$\text{Score}_{\text{semantic}} = 0.45 \times \text{semantic\_score} + 0.20 \times \text{location} + 0.20 \times \text{fee} + 0.15 \times \text{time}$$

### Configuration C: Deterministic Topic Overlap Only
Measures the standalone contribution of lexical/token topic overlap without dense embeddings:
$$\text{Score}_{\text{topic}} = 0.45 \times \text{topic\_score} + 0.20 \times \text{location} + 0.20 \times \text{fee} + 0.15 \times \text{time}$$

### Configuration D: Full Hybrid Matcher (Production Step 3C)
Evaluates the production multi-criteria formulation:
$$\text{learning\_need\_score} = \begin{cases} 0.60 \times \text{semantic\_score} + 0.40 \times \text{topic\_score}, & \text{if student provided topics} \\ \text{semantic\_score}, & \text{if no topics provided} \end{cases}$$
$$\text{Score}_{\text{hybrid}} = 0.45 \times \text{learning\_need\_score} + 0.20 \times \text{location} + 0.20 \times \text{fee} + 0.15 \times \text{time}$$

### Configuration E: Full Hybrid + Feedback Signal (Step 6A Research Experiment)
Combines the base hybrid score with a Bayesian-smoothed reputation signal:
$$\text{Score}_{\text{experimental}} = (1.0 - w_{\text{feedback}}) \times \text{Score}_{\text{hybrid}} + w_{\text{feedback}} \times S_{\text{feedback}}$$
Where $w_{\text{feedback}} \in [0.0, 1.0]$ is a configurable experimental weight (default provisional: $0.10$).

---

## 5. Bayesian Feedback & Reputation Formulation

### A. Motivation: Why Raw Average Rating Is Insufficient
Using raw arithmetic mean rating ($\overline{r}$) in matchmaking is flawed due to:
1. **The Cold-Start Dilemma:** New tutors with zero reviews cannot compute an average rating; assigning 0 unfairly penalizes them, while assigning 5.0 inflates unverified candidates.
2. **Sample Size Variance:** A single 5-star review ($n=1$) appears higher than a tutor with 4.8 stars from 50 reviews ($n=50$), despite the latter having substantially stronger evidence of consistent teaching quality.

### B. Bayesian Shrinkage Formulation
We apply Bayesian m-estimate smoothing toward a global prior $\mu_{\text{prior}}$:
$$r_{\text{adj}} = \left(\frac{n}{n + m}\right) \cdot \overline{r} + \left(\frac{m}{n + m}\right) \cdot \mu_{\text{prior}}$$
Where:
- $n$: Tutor completed-session review count ($n \ge 0$).
- $m$: Smoothing parameter / pseudocount weight (default $m = 5.0$).
- $\mu_{\text{prior}}$: Empirical dataset mean rating across all tutors, or neutral midpoint default ($3.5$).

### C. Feedback Score Normalization
The adjusted rating is normalized to $S_{\text{feedback}} \in [0.0, 1.0]$:
$$S_{\text{feedback}} = \frac{r_{\text{adj}} - r_{\min}}{r_{\max} - r_{\min}} = \frac{r_{\adj} - 1.0}{4.0}$$

### D. Feedback Evidence Confidence
We define review evidence strength monotonically as:
$$C_{\text{feedback}} = \frac{n}{n + m} \in [0, 1)$$
- At $n=0$: $C_{\text{feedback}} = 0.0$ (complete reliance on prior, zero evidence confidence).
- As $n \to \infty$: $C_{\text{feedback}} \to 1.0$ (asymptotically approaches empirical average).

---

## 6. Evaluation Metrics

1. **Precision@K ($P@K, K \in \{1, 3, 5\}$):** Proportion of top-$K$ recommendations with relevance grade $\ge 2$.
2. **Recall@5 ($R@5$):** Proportion of total relevant candidates retrieved in the top-5 ranking.
3. **Mean Reciprocal Rank (MRR):** Reciprocal rank $\frac{1}{\text{rank}_1}$ of the first retrieved item with grade $\ge 2$.
4. **NDCG@K ($K \in \{3, 5\}$):** Graded relevance ranking metric with logarithmic rank decay:
   $$\text{DCG}@K = \sum_{i=1}^K \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)}, \quad \text{NDCG}@K = \frac{\text{DCG}@K}{\text{IDCG}@K}$$
5. **Pairwise Ranking Accuracy:** Proportion of pairs $(T_A, T_B)$ where $\text{Grade}(T_A) > \text{Grade}(T_B)$ that satisfy $\text{Score}(T_A) > \text{Score}(T_B)$.

---

## 7. How to Run

```bash
# Execute evaluation from repository root
python evaluation/matching/evaluate_matcher.py --feedback-weight 0.10 --smoothing-m 5.0
```

Results are printed to the console and automatically exported to:
- `evaluation/matching/results/ablation_results.json`
- `evaluation/matching/results/ablation_results.csv`
- `evaluation/matching/results/feedback_weight_sensitivity.csv`

---

## 8. Step 6B — Feedback-Aware Stress Testing

### A. Motivation & Purpose
While Step 6A established the Bayesian shrinkage formulation on synthetic candidate sets, Step 6B investigates the **exact behavior of the feedback signal under controlled, adversarial, and edge-case ranking scenarios**. The goal is not to force an improvement, but to rigorously evaluate:
1. When feedback flips candidate rankings versus when compatibility dominates.
2. How cold-start tutors ($n=0, 1$) behave under Bayesian smoothing.
3. The sensitivity of rankings to feedback weight $w_{\text{feedback}} \in [0.00, 0.40]$ and smoothing parameter $m \in [1, 5, 10, 20]$.

### B. Controlled Benchmark Scenarios (`feedback_scenarios.json`)
The benchmark evaluates 6 deterministic challenge scenarios:
1. **Scenario 1 (Quality vs Compatibility):** Small compatibility advantage ($0.96$ vs $0.94$) paired with a substantial rating difference ($3.2$ vs $4.8$, $n=30$).
2. **Scenario 2 (Cold Start vs Established):** A 1-review 5.0-star candidate ($n=1$) competing with a mature 4.7-star candidate ($n=40$).
3. **Scenario 3 (New Tutor No Reviews):** A zero-review tutor ($n=0$, prior $\mu=3.5$) with high compatibility ($0.94$) versus an established 4.8-star tutor ($n=30$, compat $0.92$).
4. **Scenario 4 (Strong Compatibility vs Strong Feedback):** A large compatibility margin ($0.98$ vs $0.88$) tested against a large rating gap ($3.5$ vs $4.9$, $n=30$).
5. **Scenario 5 (Similar Compatibility, Different Feedback):** Near-identical compatibility ($0.91$ vs $0.90$) tested with high vs moderate ratings ($4.9$ vs $3.8$, $n=50$).
6. **Scenario 6 (Same Rating, Different Evidence):** Identical raw ratings ($5.0$) with sparse evidence ($n=1$, $C=0.17$) versus mature evidence ($n=40$, $C=0.89$).

### C. Key Findings from Stress Testing
- **Ranking Flips ($w^* = 0.10$):** Under default smoothing $m=5.0$, feedback re-ranks candidates in Scenarios 1, 2, 3, and 6 at moderate weights ($w \ge 0.10$), correctly favoring strong verified historical evidence over unverified single reviews or lower-quality mature tutors.
- **Compatibility Dominance:** In Scenario 4, the $0.10$ hybrid compatibility advantage resists ranking changes for $w \le 0.20$, confirming that domain relevance is not easily subverted by reputation unless feedback weight is set high ($w \ge 0.30$).
- **Cold-Start Protection:** Zero-review candidates ($n=0$) receive neutral prior treatment ($\mu=3.5$, $S=0.625, C=0.0$), preventing artificial promotion while still allowing high-compatibility new tutors to compete.
- **Single-Review Shrinkage:** A single 5.0 rating ($n=1, m=5$) is shrunk from $5.0$ to $3.75$ ($1.25$ star reduction), preventing single 5-star reviews from outranking proven veteran tutors.

### D. How to Run Step 6B Evaluation

```bash
# Execute Step 6B stress test and sensitivity sweep
python evaluation/matching/evaluate_feedback_scenarios.py
```

Generated outputs in `evaluation/matching/results/`:
- `feedback_scenario_results.json` / `.csv`: Complete evaluation records for all 336 parameter permutations.
- `ranking_flip_analysis.csv`: Detailed baseline vs feedback-aware top candidate comparisons.
- `cold_start_analysis.csv`: Rating shrinkage and confidence curves across review counts $n \in [0, 100]$.
- `feedback_sensitivity_summary.csv`: Summary table across weights and smoothing settings.
- `feedback_analysis.md`: Comprehensive academic research report.

### E. Synthetic / Controlled Benchmark Limitations
- Scenarios are constructed deterministically to isolate specific mathematical properties of Bayesian shrinkage and linear interpolation.
- Real user behavioral dynamics (e.g. position bias, selective review submission, subject difficulty bias) are not simulated.

---

## 9. Production Safety & Architectural Isolation

| Environment | Formulation | Weights / Signals | Status |
| :--- | :--- | :--- | :--- |
| **PRODUCTION** | Multi-Criteria Hybrid Matcher | $0.45 \times \text{Learning Need} + 0.20 \times \text{Location} + 0.20 \times \text{Fee} + 0.15 \times \text{Time}$ | **Active Live Engine** |
| **EXPERIMENTAL** | Hybrid + Bayesian Feedback | $(1 - w) \times \text{Score}_{\text{hybrid}} + w \times S_{\text{feedback}}$ | **Offline Research Only** |

> [!CAUTION]
> **Production Recommendation Scoring Has NOT Been Modified:**
> All live API endpoints (`GET /api/matching/recommendations`) strictly execute the production hybrid matcher without feedback signals. Feedback-aware ranking remains an offline research benchmark until end-to-end user studies and online A/B testing can be conducted.
