# TutorLinkAI — Matching Benchmark Dataset Summary

- **Dataset Version:** `1.0.0`
- **Schema Version:** `1.0.0`
- **Validation Status:** `VALID` (Errors: `0`)

---

## 1. Record Counts & Dimensions

| Entity | Count | Details |
| :--- | :--- | :--- |
| **Learning Queries** | 8 | High School & Undergraduate student requirements |
| **Candidate Tutors** | 12 | Multi-subject domain experts |
| **Relevance Judgments** | 96 | Complete $8 \times 12$ dense evaluation matrix |
| **Academic Subjects** | 5 | Biology, Chemistry, Computer Science, Mathematics, Physics |
| **Unique Syllabus Topics** | 52 | High school and collegiate syllabus concepts |
| **Verified Tutors** | 12 | 100% credential verified |

---

## 2. Relevance Label Distribution (qrels)

| Grade | Meaning | Count | Proportion |
| :--- | :--- | :--- | :--- |
| **Grade 0** | Irrelevant (Cross-Subject) | 78 | 81.25% |
| **Grade 1** | Subject-Matched Only | 9 | 9.38% |
| **Grade 2** | Partial Topic Match | 1 | 1.04% |
| **Grade 3** | Strong / Exact Match | 8 | 8.33% |

---

## 3. Tutor & Student Financial Metrics

| Metric | Min | Mean | Max |
| :--- | :--- | :--- | :--- |
| **Tutor Rating (Stars)** | 4.5 | 4.79 | 4.9 |
| **Tutor Reviews Count** | 0 | 16.83 | 45 |
| **Tutor Hourly Rate (₹)** | ₹350.00 | ₹545.83 | ₹800.00 |
| **Student Budget Min (₹)** | ₹300.00 | ₹406.25 | ₹500.00 |
| **Student Budget Max (₹)** | ₹650.00 | ₹862.50 | ₹1200.00 |

---

## 4. Deterministic Reproducibility Checksums (SHA-256)

```json
{
  "queries_sha256": "6e75682ccceb79db650a91dd8b18cfc8d54558579e2695659120858737f724cb",
  "tutors_sha256": "cced0bd63d15f5863f6ac9108d0fe2e47478559ad6d4b8dd04d4c3afcea61bee",
  "qrels_sha256": "878dafedcbf1651b886a16020efe63e55c0e4d6a57f0a6c669e5c394e5825b01",
  "feedback_scenarios_sha256": "fe9c79bc8040ad074f2175b5ed249665f650ca11b6ae4e57283f8a06525c67fb"
}
```
