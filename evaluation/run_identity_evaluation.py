"""
Command-line runner for TutorLinkAI Identity Similarity Evaluation.

Usage:
    python evaluation/run_identity_evaluation.py --data-dir evaluation/data --output-dir evaluation/results

Arguments:
    --data-dir: Directory containing 'genuine' and 'impostor' subdirectories.
    --output-dir: Directory where results.json and results.csv will be written.
"""

import os
import sys
import argparse
import logging

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.evaluation.identity_evaluator import IdentityEvaluator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_identity_evaluation")


def main():
    parser = argparse.ArgumentParser(description="Run TutorLinkAI Identity Verification Evaluation Harness.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "evaluation", "data"),
        help="Path to dataset directory with genuine/ and impostor/ subfolders."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.path.join(PROJECT_ROOT, "evaluation", "results"),
        help="Path to output directory for saving evaluation JSON and CSV."
    )
    args = parser.parse_args()

    data_dir = os.path.abspath(args.data_dir)
    output_dir = os.path.abspath(args.output_dir)

    logger.info(f"Starting Identity Evaluation...")
    logger.info(f"Dataset Directory: {data_dir}")
    logger.info(f"Output Directory:  {output_dir}")

    if not os.path.exists(data_dir):
        logger.warning(
            f"Dataset directory '{data_dir}' does not exist yet. "
            "Please create 'genuine/' and 'impostor/' subdirectories with paired images to run empirical evaluation."
        )
        return

    evaluator = IdentityEvaluator()
    results, summary = evaluator.evaluate_directory(data_dir)

    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "evaluation_results.json")
    csv_path = os.path.join(output_dir, "evaluation_results.csv")

    evaluator.export_results_json(results, summary, json_path)
    evaluator.export_results_csv(results, csv_path)

    logger.info(f"Evaluation complete! Processed {summary.total_pairs} pairs.")
    logger.info(f"Genuine Pairs:  {summary.genuine_valid} valid / {summary.genuine_total} total")
    if summary.genuine_stats:
        logger.info(f"  Genuine Mean: {summary.genuine_stats['mean']:.4f} | Std: {summary.genuine_stats['std']:.4f}")
        logger.info(f"  Genuine Min:  {summary.genuine_stats['min']:.4f} | Max: {summary.genuine_stats['max']:.4f}")

    logger.info(f"Impostor Pairs: {summary.impostor_valid} valid / {summary.impostor_total} total")
    if summary.impostor_stats:
        logger.info(f"  Impostor Mean: {summary.impostor_stats['mean']:.4f} | Std: {summary.impostor_stats['std']:.4f}")
        logger.info(f"  Impostor Min:  {summary.impostor_stats['min']:.4f} | Max: {summary.impostor_stats['max']:.4f}")

    logger.info(f"Exported JSON: {json_path}")
    logger.info(f"Exported CSV:  {csv_path}")


if __name__ == "__main__":
    main()
