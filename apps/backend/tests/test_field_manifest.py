import csv
import os
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from dataset_prep.field_manifest import REQUIRED_COLUMNS, validate_rows  # noqa: E402


def _row(**overrides):
    row = {
        "image_id": "field-1",
        "image_path": "field_images/a.jpg",
        "source_session_id": "session-1",
        "field_source": "farm-a",
        "disease_class": "FMD",
        "is_hard_negative": "false",
        "label_tier": "expert_reviewed",
        "reviewer_role": "veterinarian",
        "reviewer_id": "vet-1",
        "review_date": "2026-06-03",
        "review_notes": "usable",
        "train_eligible": "include",
        "validation_eligible": "include",
        "test_eligible": "exclude",
        "scan_history_record_id": "",
    }
    row.update(overrides)
    return row


class FieldManifestValidationTest(unittest.TestCase):
    def test_expert_reviewed_row_can_be_validation_eligible(self):
        result = validate_rows([_row()])

        self.assertEqual(result.errors, [])
        self.assertEqual(result.target_counts["FMD"], 1)

    def test_weak_label_cannot_be_validation_or_test_eligible(self):
        result = validate_rows([
            _row(
                label_tier="farmer_weak",
                reviewer_role="farmer",
                validation_eligible="include",
            )
        ])

        self.assertTrue(any("validation/test eligibility requires expert_reviewed" in e for e in result.errors))

    def test_hard_negative_requires_empty_disease_class(self):
        result = validate_rows([_row(is_hard_negative="true", disease_class="FMD")])

        self.assertTrue(any("hard-negative rows must leave disease_class empty" in e for e in result.errors))

    def test_scan_history_reference_warns_not_training_by_default(self):
        result = validate_rows([_row(scan_history_record_id="local-history-1")])

        self.assertTrue(any("Scan History reference is metadata only" in w for w in result.warnings))

    def test_cli_validates_csv_file(self):
        with TemporaryDirectory() as d:
            path = os.path.join(d, "field_manifest.csv")
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
                writer.writeheader()
                writer.writerow(_row())

            result = subprocess.run(
                [sys.executable, "-m", "dataset_prep.field_manifest", path],
                cwd=BACKEND_ROOT,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("FMD: 1/50", result.stdout)


if __name__ == "__main__":
    unittest.main()
