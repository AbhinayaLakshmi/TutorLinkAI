# TutorLinkAI — Matching & Recommender Research Benchmark Dataset

## 1. Dataset Purpose
This benchmark dataset provides a standardized, reproducible, and deterministic testbed for evaluating multi-criteria academic tutoring recommendation engines. It supports empirical benchmarking of dense semantic retrieval, lexical topic overlap, multi-constraint satisfaction (location, budget, schedule), Bayesian reputation shrinkage, and cold-start candidate ranking.

---

## 2. Dataset Structure & Files

The benchmark consists of four primary JSON artifacts in `evaluation/matching/`:

```
evaluation/matching/
├── queries.json             # 8 student learning need requirements (queries)
├── tutors.json              # 12 candidate tutor profiles across 5 subjects
├── qrels.json               # 96 ground-truth graded relevance judgments (8 queries × 12 tutors)
├── feedback_scenarios.json  # 6 edge-case stress-test scenarios for Bayesian reputation analysis
├── DATA_DICTIONARY.md       # Exhaustive field-by-field schema & types specification
├── DATASET_README.md        # Comprehensive dataset documentation (this file)
└── results/                 # Machine-readable evaluation outputs, summaries, and plots
```

---

## 3. Student / Learning Need Records (`queries.json`)
Each record models a student's structured learning request, containing:
- **Core Domain:** High-level subject (`subject`) and fine-grained subtopics (`topics`).
- **Pedagogical Preferences:** Freeform learning objectives (`learning_goals`), desired tutor traits (`preferred_tutor_characteristics`), and student grade level (`student_level`).
- **Operational Constraints:** Delivery mode (`preferred_learning_mode`), geographic coordinates (`latitude`, `longitude`), hourly budget bounds (`budget_min`, `budget_max`), and weekly time slots (`preferred_slots`).

---

## 4. Tutor Records (`tutors.json`)
Each record models a candidate tutor profile, containing:
- **Qualifications:** Subjects taught (`subjects`), specialized topic list (`topics_expertise`), teaching skills (`skills`), student cohorts accepted (`student_levels`), and experience (`years_of_experience`).
- **Logistics & Constraints:** Preferred teaching mode (`preferred_teaching_mode`), hourly rate (`hourly_rate`), geographic location coordinates (`latitude`, `longitude`), and recurring availability slots (`availability`).
- **Verification & Feedback:** Official platform verification flag (`is_verified`), empirical mean rating (`rating`), and completed-session review volume (`review_count`).

---

## 5. Relevance Judgments (`qrels.json`)
Ground truth relevance is annotated using a 4-point graded scale:
- **Grade 0 (Irrelevant):** Candidate belongs to an unrelated discipline (cross-subject mismatch).
- **Grade 1 (Subject-Matched Only):** Candidate teaches the same broad subject, but lacks the specific topic specialization or pedagogical alignment requested.
- **Grade 2 (Partial Match):** Candidate covers foundational or closely related topics within the subject domain.
- **Grade 3 (Strong / Exact Match):** Candidate possesses exact topic expertise, aligned pedagogical level, and compatible modality/schedule constraints.

---

## 6. Dataset Size & Summary Statistics

- **Total Learning Queries ($|Q|$):** 8 queries
- **Total Candidate Tutors ($|T|$):** 12 tutors
- **Total Graded Relevance Judgments ($|R|$):** 96 pairs (complete dense evaluation matrix)
- **Academic Subject Disciplines:** 5 subjects (Physics, Computer Science, Mathematics, Chemistry, Biology + 1 History cross-subject control)
- **Total Unique Expertise Topics:** 46 unique topics
- **Tutor Verification Rate:** 100% (all 12 tutors verified)
- **Review Count Range:** 0 to 45 reviews ($\mu = 16.08, \text{median} = 16.5$)
- **Rating Range:** 4.5 to 4.9 stars ($\mu = 4.78, \text{median} = 4.85$)
- **Hourly Rate Range:** ₹350.0 to ₹800.0 ($\mu = ₹550.0, \text{median} = ₹525.0$)

---

## 7. How Relevance Labels Were Created
Relevance labels were systematically curated by domain expert assessment against explicit academic curricula (CBSE/State Board High School and University Undergraduate standards). Each candidate profile was judged independently on:
1. **Topic Alignment:** Direct presence and depth of the requested syllabus chapters.
2. **Pedagogical Alignment:** Suitability of teaching methods for the student's stated goal (e.g. proof-based rigor vs competitive exam problem-solving).
3. **Constraint Feasibility:** Geographic, financial, and temporal viability.

---

## 8. Controlled Research Benchmark Status Notice

> [!IMPORTANT]
> **Controlled Synthetic Benchmark Notice:**
> This dataset is a **controlled, curated research benchmark** constructed specifically to facilitate reproducible, offline scientific evaluation of recommendation algorithms.
> - It does **not** represent production user click logs or identifiable personal student/tutor records.
> - Review counts, ratings, and profile variations are curated to create deterministic test conditions (cold-start, sparse feedback, mature evidence).
> - Researchers and developers must not cite or treat this benchmark as an uncurated real-world population sample.

---

## 9. Limitations
1. **Curated Scale:** With 8 queries and 12 candidate tutors, the benchmark is designed for high-precision ablation studies and metric tractability rather than large-scale retrieval index stress testing.
2. **Deterministic Ratings:** Historical ratings and review counts represent static snapshots rather than sequential temporal event logs.
3. **Position Bias Absence:** As an offline testbed with static $Q \times T$ relevance judgments, online position bias and click-through attrition are not modeled.

---

## 10. Reproducibility Instructions

### Validating the Dataset
To check dataset schema integrity, cross-table foreign key validity, and score bounds:
```bash
python evaluation/matching/validate_dataset.py
```

### Running the Matching Ablation Study (Step 6A)
```bash
python evaluation/matching/evaluate_matcher.py --feedback-weight 0.10 --smoothing-m 5.0
```

### Running the Feedback Stress-Test Suite (Step 6B)
```bash
python evaluation/matching/evaluate_feedback_scenarios.py
```

### Running Unit Tests
```bash
pytest backend/tests/test_research_dataset.py -v
```
