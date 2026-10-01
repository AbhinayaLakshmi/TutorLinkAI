# TutorLinkAI — Matching Benchmark Data Dictionary

This document defines the schema, types, allowed values, semantics, and system usage for all fields across the TutorLinkAI offline research benchmark dataset.

---

## 1. Overview of Datasets

The matching evaluation benchmark consists of three core relational datasets stored in JSON format:
1. **Queries Dataset (`queries.json`):** Formally represents student learning needs, academic requirements, pedagogical preferences, and matching constraints.
2. **Tutors Dataset (`tutors.json`):** Formally represents candidate tutor profiles, domain subject expertise, topic lists, fees, geographic coordinates, availability, and historical review metadata.
3. **Relevance Judgments (`qrels.json`):** Contains ground-truth graded relevance scores $\in \{0, 1, 2, 3\}$ assigned between query and tutor pairs for information retrieval evaluation (Precision@K, NDCG@K, MRR).

---

## 2. Student / Learning Need Dataset (`queries.json`)

| Field | Dataset | Type | Required | Allowed Values / Range | Matching Model Usage | Meaning & Example |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `query_id` | `queries.json` | `string` | **Yes** | Alphanumeric snake_case, unique | Evaluation / Indexing | Unique identifier for the learning query. Example: `"q1_physics_rotational"` |
| `subject` | `queries.json` | `string` | **Yes** | Academic subject name (e.g. "Physics", "Computer Science") | Stage 1 Subject Gate & Text Embedding | Primary subject domain needed. Example: `"Physics"` |
| `subjects_needed` | `queries.json` | `string` | **Yes** | Academic subject name | Stage 1 Subject Gate alias | Normalized subject string for backward compatibility. Example: `"Physics"` |
| `topics` | `queries.json` | `list[string]` | **Yes** | List of specific topic strings (can be empty `[]`) | Stage 2 Topic Overlap & Semantic Text | Specific syllabus topics / subtopics requested. Example: `["Rotational Motion", "Mechanics"]` |
| `learning_goals` | `queries.json` | `string` | No | Freeform text string | Stage 2 Semantic Embedding | Detailed statement of what the student wants to master. Example: `"Master rotational dynamics and problem solving"` |
| `preferred_tutor_characteristics` | `queries.json` | `string` | No | Freeform text string | Stage 2 Semantic Embedding | Desired pedagogical style or mentor traits. Example: `"Patient, step-by-step mathematical derivations"` |
| `student_level` | `queries.json` | `string` | No | Categorical/text (e.g., "High School (Class 12)", "Undergraduate") | Stage 2 Semantic Embedding | Student's current academic standard/level. Example: `"High School (Class 12)"` |
| `preferred_learning_mode` | `queries.json` | `string` | **Yes** | `"Online"`, `"Offline"`, `"Both"` | Stage 2 Location Constraint Scoring | Preferred mode of instruction. Example: `"Online"` |
| `preferred_tutor_languages` | `queries.json` | `list[string]` | No | List of language strings (e.g. `["English", "Tamil"]`) | Text Representation / Metadata | Languages preferred by student for tutoring. Example: `["English"]` |
| `latitude` | `queries.json` | `float` | **Yes** | $[-90.0, +90.0]$ | Stage 2 Location Distance Scoring | Latitude coordinates in decimal degrees. Example: `13.0827` |
| `longitude` | `queries.json` | `float` | **Yes** | $[-180.0, +180.0]$ | Stage 2 Location Distance Scoring | Longitude coordinates in decimal degrees. Example: `80.2707` |
| `budget_min` | `queries.json` | `float` | **Yes** | $\ge 0.0, \le \text{budget\_max}$ | Stage 2 Fee Compatibility Scoring | Minimum hourly budget in local currency. Example: `400.0` |
| `budget_max` | `queries.json` | `float` | **Yes** | $\ge \text{budget\_min}$ | Stage 2 Fee Compatibility Scoring | Maximum hourly budget in local currency. Example: `800.0` |
| `preferred_slots` | `queries.json` | `list[object]` | **Yes** | List of slot objects (can be empty `[]`) | Stage 2 Time Compatibility Scoring | Weekly preferred time windows with `day`, `start_time` (`HH:MM`), `end_time` (`HH:MM`). Example: `[{"day": "Monday", "start_time": "16:00", "end_time": "18:00"}]` |

---

## 3. Tutor Dataset (`tutors.json`)

| Field | Dataset | Type | Required | Allowed Values / Range | Matching Model Usage | Meaning & Example |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `tutor_id` | `tutors.json` | `string` | **Yes** | Alphanumeric snake_case, unique | Candidate Key / Indexing | Unique identifier for the candidate tutor. Example: `"t_phys_rotational_expert"` |
| `name` | `tutors.json` | `string` | **Yes** | Non-empty string | UI Display / Metadata | Full name or display title with specialization. Example: `"Dr. Subhash (Physics)"` |
| `subjects` | `tutors.json` | `list[string]` | **Yes** | Non-empty list of subject strings | Stage 1 Subject Gate | Subjects the tutor is qualified to teach. Example: `["Physics"]` |
| `subjects_taught` | `tutors.json` | `list[string]` | **Yes** | Non-empty list of subject strings | Stage 1 Subject Gate alias | Backward compatibility alias for subjects. Example: `["Physics"]` |
| `topics_expertise` | `tutors.json` | `list[string]` | **Yes** | List of topic strings | Stage 2 Topic Overlap & Semantic Text | Specific syllabus topics where tutor has proven expertise. Example: `["Rotational Motion", "Mechanics", "Angular Momentum"]` |
| `skills` | `tutors.json` | `list[string]` | No | List of pedagogical skill strings | Stage 2 Semantic Embedding | Teaching strengths and methodologies. Example: `["Mathematical derivations", "Step-by-step problem solving"]` |
| `student_levels` | `tutors.json` | `list[string]` | No | List of academic level strings | Stage 2 Semantic Embedding | Academic cohorts tutor accepts. Example: `["High School (Class 12)", "Undergraduate"]` |
| `languages_can_teach_in` | `tutors.json` | `list[string]` | No | List of language strings | Metadata / Filtering | Languages spoken by tutor. Example: `["English"]` |
| `preferred_teaching_mode` | `tutors.json` | `string` | **Yes** | `"Online"`, `"Offline"`, `"Both"` | Stage 2 Location Distance Scoring | Delivery modes offered by tutor. Example: `"Online"` |
| `hourly_rate` | `tutors.json` | `float` | **Yes** | $> 0.0$ | Stage 2 Fee Compatibility Scoring | Hourly fee in local currency. Example: `550.0` |
| `latitude` | `tutors.json` | `float` | **Yes** | $[-90.0, +90.0]$ | Stage 2 Location Distance Scoring | Base latitude coordinates in decimal degrees. Example: `13.0827` |
| `longitude` | `tutors.json` | `float` | **Yes** | $[-180.0, +180.0]$ | Stage 2 Location Distance Scoring | Base longitude coordinates in decimal degrees. Example: `80.2707` |
| `location` | `tutors.json` | `string` | No | String locality description | UI Display / Metadata | Locality or neighborhood name. Example: `"Chennai Central"` |
| `availability` | `tutors.json` | `list[object]` | **Yes** | List of slot objects | Stage 2 Time Compatibility Scoring | Available weekly teaching slots with `day`, `start_time` (`HH:MM`), `end_time` (`HH:MM`). Example: `[{"day": "Monday", "start_time": "15:00", "end_time": "19:00"}]` |
| `rating` | `tutors.json` | `float` | **Yes** | $[1.0, 5.0]$ | Experimental Bayesian Feedback Signal | Historical arithmetic mean review rating. Example: `4.9` |
| `review_count` | `tutors.json` | `int` | **Yes** | $\ge 0$ | Experimental Bayesian Feedback Signal | Total number of completed-session student reviews. Example: `28` |
| `years_of_experience` | `tutors.json` | `int` | No | $\ge 0$ | UI Display / Profile Metadata | Professional tutoring experience in years. Example: `8` |
| `is_verified` | `tutors.json` | `bool` | **Yes** | `true`, `false` | Stage 1 Verification Filter | Official credential verification status. Example: `true` |

---

## 4. Relevance Judgments Dataset (`qrels.json`)

The relevance judgments file maps each `query_id` to a dictionary of candidate `tutor_id` ratings representing graded relevance ground truth.

| Field | Dataset | Type | Required | Allowed Values / Range | Usage | Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `query_id` | `qrels.json` | `string` (Key) | **Yes** | Must exist in `queries.json` | Evaluation Index | Target query key. Example: `"q1_physics_rotational"` |
| `tutor_id` | `qrels.json` | `string` (Subkey) | **Yes** | Must exist in `tutors.json` | Evaluation Index | Candidate tutor key. Example: `"t_phys_rotational_expert"` |
| `relevance` | `qrels.json` | `integer` (Value) | **Yes** | `0, 1, 2, 3` | Ground Truth Metric Computation | Graded academic relevance level defined below. Example: `3` |

### Graded Relevance Scale Definition:
- **`0` = Irrelevant:** Candidate belongs to a different subject domain or cannot satisfy basic domain prerequisites (e.g. History tutor for Physics query).
- **`1` = Subject-Matched Only:** Candidate teaches the correct overarching subject domain, but has non-overlapping topic expertise or unaligned pedagogical level (e.g. Quantum Physics theorist for Rotational Motion mechanics).
- **`2` = Partial Match:** Candidate covers related or foundational subfields with moderate topic overlap, but lacks exact specialization (e.g. General Relativity / Astrophysics for Quantum mechanics).
- **`3` = Strong / Exact Match:** Candidate specializes directly in the requested topics, matches pedagogical style, meets level criteria, and has overlapping availability/modality.

---

## 5. Controlled Research Status Notice

All records in this dataset are **curated deterministic research artifacts** intended for academic recommendation and information retrieval evaluation. They do not represent uncurated production logs or identifiable real-world student data.
