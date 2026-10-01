import sys
import json
import csv
from pathlib import Path
import pytest

# Ensure project root and ai-service are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AI_SERVICE_DIR = BASE_DIR / "ai-service"
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from evaluation.research.config import (
    RESULTS_DIR,
    ALL_MODELS,
    QUERIES_PATH,
    TUTORS_PATH,
    QRELS_PATH,
    FEEDBACK_SCENARIOS_PATH,
    PROD_WEIGHT_LEARNING_NEED,
    PROD_WEIGHT_LOCATION,
    PROD_WEIGHT_FEE,
    PROD_WEIGHT_TIME,
)
from evaluation.research.visualization.generate_tables import (
    generate_model_comparison_table,
    generate_ranking_flip_table,
    generate_cold_start_table,
    generate_all_tables,
    TABLES_DIR,
)
from evaluation.research.visualization.generate_figures import (
    generate_ablation_figure,
    generate_cold_start_figure,
    generate_feedback_sensitivity_figure,
    generate_all_figures,
    FIGURES_DIR,
)
from evaluation.research.visualization.generate_report import generate_research_report
from evaluation.matching.validate_dataset import compute_file_sha256
from app.matching.config import (
    DEFAULT_WEIGHT_LEARNING_NEED,
    DEFAULT_WEIGHT_LOCATION,
    DEFAULT_WEIGHT_FEE,
    DEFAULT_WEIGHT_TIME,
)


def test_table_generation_creates_expected_artifacts():
    outputs = generate_all_tables()

    assert "model_comparison_csv" in outputs
    assert "model_comparison_md" in outputs
    assert "ranking_flip_csv" in outputs
    assert "ranking_flip_md" in outputs
    assert "cold_start_csv" in outputs
    assert "cold_start_md" in outputs

    for path in outputs.values():
        assert path.exists(), f"Missing table file: {path}"
        assert path.stat().st_size > 0


def test_model_comparison_table_contains_all_models():
    csv_path, md_path = generate_model_comparison_table()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    model_ids = [row["model_id"] for row in reader]
    assert len(model_ids) == len(ALL_MODELS)
    for m in ALL_MODELS:
        assert m in model_ids

    # Check metric columns
    required_cols = ["precision@1", "precision@3", "precision@5", "recall@5", "mrr", "ndcg@3", "ndcg@5", "pairwise_accuracy"]
    for col in required_cols:
        assert col in reader[0]
        for row in reader:
            val = float(row[col])
            assert 0.0 <= val <= 1.0


def test_ranking_flip_table_structure_and_validity():
    csv_path, md_path = generate_ranking_flip_table()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) > 0
    # Check that rank_flipped values are boolean-like
    flipped_flags = [row["rank_flipped"] for row in reader]
    assert "True" in flipped_flags or "true" in flipped_flags or True in flipped_flags


def test_figure_generation_creates_png_and_svg():
    fig_outputs = generate_all_figures()

    assert "ablation_metrics" in fig_outputs
    assert "cold_start_shrinkage" in fig_outputs
    assert "feedback_sensitivity" in fig_outputs

    for name, paths in fig_outputs.items():
        png_file = paths["png"]
        svg_file = paths["svg"]

        assert png_file.exists(), f"Missing PNG figure: {png_file}"
        assert svg_file.exists(), f"Missing SVG figure: {svg_file}"
        assert png_file.stat().st_size > 1000, f"PNG figure too small: {png_file}"
        assert svg_file.stat().st_size > 1000, f"SVG figure too small: {svg_file}"


def test_research_report_generation():
    report_path = generate_research_report()

    assert report_path.exists()
    assert report_path.name == "research_summary.md"

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Legacy Baseline" in content
    assert "Full Hybrid" in content
    assert "Bayesian Cold-Start Observations" in content
    assert "Ranking-Flip Observations" in content
    assert "Limitations" in content


def test_deterministic_generation_does_not_mutate_dataset():
    # Capture dataset hashes before
    q_hash_before = compute_file_sha256(QUERIES_PATH)
    t_hash_before = compute_file_sha256(TUTORS_PATH)
    r_hash_before = compute_file_sha256(QRELS_PATH)
    s_hash_before = compute_file_sha256(FEEDBACK_SCENARIOS_PATH)

    # Re-run all generators
    generate_all_tables()
    generate_all_figures()
    generate_research_report()

    # Capture dataset hashes after
    q_hash_after = compute_file_sha256(QUERIES_PATH)
    t_hash_after = compute_file_sha256(TUTORS_PATH)
    r_hash_after = compute_file_sha256(QRELS_PATH)
    s_hash_after = compute_file_sha256(FEEDBACK_SCENARIOS_PATH)

    assert q_hash_before == q_hash_after
    assert t_hash_before == t_hash_after
    assert r_hash_before == r_hash_after
    assert s_hash_before == s_hash_after


def test_production_matching_weights_remain_unmodified():
    # Strict safety invariant
    assert DEFAULT_WEIGHT_LEARNING_NEED == PROD_WEIGHT_LEARNING_NEED == 0.45
    assert DEFAULT_WEIGHT_LOCATION == PROD_WEIGHT_LOCATION == 0.20
    assert DEFAULT_WEIGHT_FEE == PROD_WEIGHT_FEE == 0.20
    assert DEFAULT_WEIGHT_TIME == PROD_WEIGHT_TIME == 0.15
