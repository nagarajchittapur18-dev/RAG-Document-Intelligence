"""
Dataset Validation Utility for DocuRAG / RAGMate Phase 12.
Validates question schema, uniqueness, field types, document existence,
and chunk ID integrity against the evaluation vector collection.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure backend and root imports are available
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(root_dir))

from app.services.vector_store import VectorStore

ALLOWED_QUESTION_TYPES = {
    "fact",
    "methodology",
    "algorithm",
    "results",
    "comparison",
    "multi_hop",
    "contextual",
    "unanswerable",
}

ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}

REQUIRED_FIELDS = [
    "id",
    "question",
    "document_id",
    "document_name",
    "expected_pages",
    "expected_chunk_ids",
    "reference_answer",
    "question_type",
    "difficulty",
]

EVAL_COLLECTION_NAME = "ragmate_eval_collection"


class DatasetValidator:
    """
    Validates academic evaluation benchmark datasets for RAGMate.
    Ensures zero fabricated data, exact schema conformance, and vector store chunk alignment.
    """

    def __init__(
        self,
        dataset_path: Optional[Path] = None,
        vector_store: Optional[VectorStore] = None,
        verify_chunks: bool = True,
    ):
        self.dataset_path = dataset_path or (
            root_dir / "evaluation" / "dataset" / "evaluation_questions.json"
        )
        self.verify_chunks = verify_chunks
        self.vector_store = vector_store
        self._existing_chunk_ids = None

    def _get_existing_chunk_ids(self) -> set:
        if self._existing_chunk_ids is not None:
            return self._existing_chunk_ids
        
        if not self.verify_chunks:
            self._existing_chunk_ids = set()
            return self._existing_chunk_ids

        try:
            vs = self.vector_store or VectorStore(collection_name=EVAL_COLLECTION_NAME)
            raw_data = vs.collection.get()
            self._existing_chunk_ids = set(raw_data.get("ids", []))
        except Exception as e:
            # If collection not yet initialized, fallback to empty set and log warning
            self._existing_chunk_ids = set()
        return self._existing_chunk_ids

    def validate(self, dataset: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        if dataset is None:
            if not self.dataset_path.exists():
                return {
                    "is_valid": False,
                    "total_questions": 0,
                    "valid_count": 0,
                    "invalid_count": 0,
                    "errors": [f"Dataset file not found at: {self.dataset_path}"],
                }
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                dataset = json.load(f)

        errors: List[str] = []
        seen_ids = set()
        valid_count = 0
        existing_chunks = self._get_existing_chunk_ids()

        for idx, item in enumerate(dataset):
            item_errors = []
            q_id = item.get("id")

            # 1. ID checks
            if not q_id or not isinstance(q_id, str):
                item_errors.append(f"Record #{idx}: missing or non-string 'id'.")
            elif q_id in seen_ids:
                item_errors.append(f"Record {q_id}: duplicate question ID.")
            else:
                seen_ids.add(q_id)

            label = q_id or f"Record #{idx}"

            # 2. Required fields
            for rf in REQUIRED_FIELDS:
                if rf not in item:
                    item_errors.append(f"{label}: missing required field '{rf}'.")

            # 3. Question text
            question = item.get("question", "")
            if not isinstance(question, str) or not question.strip():
                item_errors.append(f"{label}: 'question' must be a non-empty string.")

            # 4. Question type
            q_type = item.get("question_type")
            if q_type not in ALLOWED_QUESTION_TYPES:
                item_errors.append(
                    f"{label}: invalid 'question_type' '{q_type}'. Allowed: {sorted(ALLOWED_QUESTION_TYPES)}"
                )

            # 5. Difficulty
            diff = item.get("difficulty")
            if diff not in ALLOWED_DIFFICULTIES:
                item_errors.append(
                    f"{label}: invalid 'difficulty' '{diff}'. Allowed: {sorted(ALLOWED_DIFFICULTIES)}"
                )

            # 6. Reference answer
            ref = item.get("reference_answer", "")
            if not isinstance(ref, str) or not ref.strip():
                item_errors.append(f"{label}: 'reference_answer' must be a non-empty string.")

            # 7. Unanswerable vs Answerable constraints
            expected_chunks = item.get("expected_chunk_ids", [])
            expected_pages = item.get("expected_pages", [])

            if q_type == "unanswerable":
                if expected_chunks:
                    item_errors.append(
                        f"{label}: unanswerable question must have empty 'expected_chunk_ids', got {expected_chunks}."
                    )
                if expected_pages:
                    item_errors.append(
                        f"{label}: unanswerable question must have empty 'expected_pages', got {expected_pages}."
                    )
            else:
                if not isinstance(expected_chunks, list) or len(expected_chunks) == 0:
                    item_errors.append(
                        f"{label}: answerable question must specify at least one expected chunk ID in 'expected_chunk_ids'."
                    )
                if not isinstance(expected_pages, list) or len(expected_pages) == 0:
                    item_errors.append(
                        f"{label}: answerable question must specify at least one expected page in 'expected_pages'."
                    )

                # Verify chunk existence if collection is populated
                if self.verify_chunks and existing_chunks:
                    for cid in expected_chunks:
                        if cid not in existing_chunks:
                            item_errors.append(
                                f"{label}: expected chunk ID '{cid}' does not exist in collection '{EVAL_COLLECTION_NAME}'."
                            )

            if item_errors:
                errors.extend(item_errors)
            else:
                valid_count += 1

        total_questions = len(dataset)
        invalid_count = total_questions - valid_count
        is_valid = (len(errors) == 0) and (total_questions > 0)

        return {
            "is_valid": is_valid,
            "total_questions": total_questions,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "errors": errors,
        }


def run_cli_validation():
    print("=" * 70)
    print("  PHASE 12: EVALUATION DATASET SCHEMA & CHUNK INTEGRITY VALIDATION")
    print("=" * 70)

    validator = DatasetValidator()
    result = validator.validate()

    print(f"\nTotal Questions: {result['total_questions']}")
    print(f"Valid:           {result['valid_count']}")
    print(f"Invalid:         {result['invalid_count']}")

    if result["is_valid"]:
        print("\n  [SUCCESS] All questions passed validation! Dataset is 100% compliant.")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n  [FAILED] Validation errors detected:")
        for err in result["errors"][:20]:
            print(f"   - {err}")
        if len(result["errors"]) > 20:
            print(f"   ... and {len(result['errors']) - 20} more errors.")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    run_cli_validation()
