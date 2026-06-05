import csv
import os
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from dataset_prep.symptom_annotations import REQUIRED_COLUMNS, validate_rows  # noqa: E402


def _row(**overrides):
    row = {
        "image_id": "field-1",
        "disease_class": "FMD",
        "is_hard_negative": "false",
        "annotation_id": "ann-1",
        "symptom_category": "fmd_mouth_lesion",
        "x_min": "0.10",
        "y_min": "0.20",
        "x_max": "0.50",
        "y_max": "0.60",
        "annotator_id": "annotator-1",
        "review_status": "accepted",
        "review_notes": "usable",
    }
    row.update(overrides)
    return row


class SymptomAnnotationValidationTest(unittest.TestCase):
    def test_disease_image_accepts_symptom_box(self):
        result = validate_rows([_row()])

        self.assertEqual(result.errors, [])

    def test_disease_image_requires_box(self):
        result = validate_rows([_row(annotation_id="", symptom_category="", x_min="", y_min="", x_max="", y_max="")])

        self.assertTrue(any("requires at least one symptom-region box" in e for e in result.errors))

    def test_healthy_image_rejects_fake_box(self):
        result = validate_rows([_row(disease_class="healthy", symptom_category="lsd_skin_nodule")])

        self.assertTrue(any("healthy images must not have fake" in e for e in result.errors))

    def test_hard_negative_allows_only_confusing_region(self):
        result = validate_rows([_row(disease_class="", is_hard_negative="true", symptom_category="lsd_skin_nodule")])

        self.assertTrue(any("hard-negative boxes may only mark confusing_region" in e for e in result.errors))

    def test_invalid_coordinates_are_rejected(self):
        result = validate_rows([_row(x_min="0.70", x_max="0.20")])

        self.assertTrue(any("coordinates must be normalized" in e for e in result.errors))

    def test_cli_validates_example_shape(self):
        with TemporaryDirectory() as d:
            path = os.path.join(d, "symptom_region_annotations.csv")
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
                writer.writeheader()
                writer.writerow(_row())

            result = subprocess.run(
                [sys.executable, "-m", "dataset_prep.symptom_annotations", path],
                cwd=BACKEND_ROOT,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Annotation manifest valid", result.stdout)


if __name__ == "__main__":
    unittest.main()
