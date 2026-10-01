# Model Comparison & Component Ablation Table

| Configuration | Model ID | Semantic | Topic | Constraints | Feedback | P@1 | P@3 | P@5 | R@5 | MRR | NDCG@3 | NDCG@5 | Pairwise Acc |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Configuration A: Legacy Baseline** | `legacy_baseline` | ✗ | ✗ | ✓ | ✗ | `0.8750` | `0.3750` | `0.2250` | `1.0000` | `0.9375` | `0.9670` | `0.9670` | `0.9856` |
| **Configuration B: Dense Semantic Only** | `dense_semantic` | ✓ | ✗ | ✓ | ✗ | `1.0000` | `0.3750` | `0.2250` | `1.0000` | `1.0000` | `1.0000` | `1.0000` | `1.0000` |
| **Configuration C: Topic Overlap Only** | `topic_overlap` | ✗ | ✓ | ✓ | ✗ | `1.0000` | `0.3750` | `0.2250` | `1.0000` | `1.0000` | `0.9965` | `0.9965` | `0.9958` |
| **Configuration D: Full Hybrid Matcher (Production)** | `full_hybrid` | ✓ | ✓ | ✓ | ✗ | `1.0000` | `0.3750` | `0.2250` | `1.0000` | `1.0000` | `0.9965` | `0.9965` | `0.9958` |
| **Configuration E: Full Hybrid + Feedback (Experimental)** | `full_hybrid_feedback` | ✓ | ✓ | ✓ | ✓ (w=0.10) | `1.0000` | `0.3750` | `0.2250` | `1.0000` | `1.0000` | `0.9965` | `0.9965` | `0.9958` |
