"""
Data Loader for Step 7A Research Benchmark Dataset.
Loads queries, tutors, qrels, and feedback scenarios, validating integrity and computing content hashes.
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

from evaluation.research.config import (
    QUERIES_PATH,
    TUTORS_PATH,
    QRELS_PATH,
    FEEDBACK_SCENARIOS_PATH,
)
from evaluation.matching.validate_dataset import validate_dataset


def compute_sha256(filepath: Path) -> str:
    """Computes deterministic SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


class BenchmarkDataLoader:
    """Loads and encapsulates the validated Step 7A benchmark dataset."""

    def __init__(
        self,
        queries_path: Optional[Path] = None,
        tutors_path: Optional[Path] = None,
        qrels_path: Optional[Path] = None,
        feedback_scenarios_path: Optional[Path] = None,
        validate: bool = True,
    ):
        self.queries_path = queries_path or QUERIES_PATH
        self.tutors_path = tutors_path or TUTORS_PATH
        self.qrels_path = qrels_path or QRELS_PATH
        self.feedback_scenarios_path = feedback_scenarios_path or FEEDBACK_SCENARIOS_PATH

        if validate:
            self._validate_dataset_integrity()

        self.queries: List[Dict[str, Any]] = self._load_json(self.queries_path)
        self.tutors: List[Dict[str, Any]] = self._load_json(self.tutors_path)
        self.qrels: Dict[str, Dict[str, int]] = self._load_json(self.qrels_path)
        self.feedback_scenarios: List[Dict[str, Any]] = (
            self._load_json(self.feedback_scenarios_path)
            if self.feedback_scenarios_path.exists()
            else []
        )

    def _validate_dataset_integrity(self) -> None:
        """Executes Step 7A validation suite and raises error if invalid."""
        is_valid, errors, _ = validate_dataset()
        if not is_valid:
            error_msg = "; ".join(errors)
            raise ValueError(f"Benchmark dataset validation failed: {error_msg}")

    def _load_json(self, path: Path) -> Any:
        """Loads and parses JSON from path with descriptive error handling."""
        if not path.exists():
            raise FileNotFoundError(f"Required benchmark dataset file not found: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON in benchmark dataset file '{path}': {exc}") from exc

    def get_checksums(self) -> Dict[str, str]:
        """Returns deterministic SHA-256 hashes of all loaded dataset files."""
        checksums = {
            "queries_sha256": compute_sha256(self.queries_path),
            "tutors_sha256": compute_sha256(self.tutors_path),
            "qrels_sha256": compute_sha256(self.qrels_path),
        }
        if self.feedback_scenarios_path.exists():
            checksums["feedback_scenarios_sha256"] = compute_sha256(self.feedback_scenarios_path)
        return checksums

    def get_dataset_summary(self) -> Dict[str, Any]:
        """Returns core counts and dimensions of the loaded dataset."""
        return {
            "queries_count": len(self.queries),
            "tutors_count": len(self.tutors),
            "qrels_queries_count": len(self.qrels),
            "feedback_scenarios_count": len(self.feedback_scenarios),
            "checksums": self.get_checksums(),
        }
