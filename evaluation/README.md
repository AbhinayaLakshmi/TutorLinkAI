# TutorLinkAI Identity Similarity Evaluation Harness

This directory contains the isolated research evaluation harness for benchmarking SFace face verification cosine similarities between educational certificate portraits and live camera captures.

---

## 1. Directory Structure

```
evaluation/
├── data/                               # Local benchmark data (GITIGNORED)
│   ├── genuine/                        # Genuine Identity Pairs (Same Subject)
│   │   ├── pair_001_cert.pdf           # Certificate PDF (or .png / .jpg)
│   │   ├── pair_001_live.jpg           # Corresponding Live Camera Capture
│   │   ├── pair_002_cert.png
│   │   └── pair_002_live.jpg
│   └── impostor/                       # Impostor Identity Pairs (Different Subjects)
│       ├── pair_001_cert.pdf           # Certificate of Person A
│       ├── pair_001_live.jpg           # Live capture of Person B
│       ├── pair_002_cert.png
│       └── pair_002_live.jpg
├── results/                            # Benchmark outputs (GITIGNORED)
│   ├── evaluation_results.json         # Summary statistics & pair-level metadata
│   └── evaluation_results.csv          # Machine-readable tabular results
├── run_identity_evaluation.py          # Command-line evaluation runner
└── README.md                           # Documentation & privacy protocols
```

---

## 2. Naming Conventions

For automatic pair matching by the evaluation harness:
- Certificate file: `pair_<ID>_cert.<ext>` or `pair_<ID>_certificate.<ext>` (supported extensions: `.pdf`, `.png`, `.jpg`, `.jpeg`)
- Live frame file: `pair_<ID>_live.<ext>` or `pair_<ID>_camera.<ext>` (supported extensions: `.png`, `.jpg`, `.jpeg`)

---

## 3. Privacy & Research Compliance Policy

- **No Personal Biometrics in Git:** Real student/tutor certificates, live photos, and biometric vector embeddings MUST NEVER be committed to Git.
- **Gitignore Protection:** `evaluation/data/` and `evaluation/results/` are explicitly added to `.gitignore`.
- **Output Sanitization:** Exported CSV and JSON files contain only evaluation metadata (pair ID, pair type, extraction status, quality metric) and the calculated float cosine similarity $[-1.0, 1.0]$. They never contain raw pixel arrays or 128-D embedding vectors.
- **Consent Prerequisite:** All real biometric samples collected for empirical evaluation must have explicit subject consent for identity benchmarking.

---

## 4. Running the Evaluation Harness

From the project root:

```powershell
$env:PYTHONPATH="c:\Users\abhin\Desktop\final year project\TutorLinkAI"; & "backend\venv\Scripts\python.exe" evaluation/run_identity_evaluation.py --data-dir evaluation/data --output-dir evaluation/results
```
