import csv
import os
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from docs.model.field_baseline_evaluation import evaluate, load_field_examples, load_predictions  # noqa: E402


FIELD_COLUMNS = [
    "image_id", "image_path", "source_session_id", "field_source", "disease_class",
    "is_hard_negative", "label_tier", "reviewer_role", "reviewer_id", "review_date",
    "review_notes", "train_eligible", "validation_eligible", "test_eligible",
    "scan_history_record_id",
]


def field_row(image_id, label, tier="expert_reviewed", test="include"):
    return {
        "image_id": image_id,
        "image_path": f"field/{image_id}.jpg",
        "source_session_id": "s1",
        "field_source": "farm-a",
        "disease_class": label,
        "is_hard_negative": "false",
        "label_tier": tier,
        "reviewer_role": "veterinarian" if tier == "expert_reviewed" else "farmer",
        "reviewer_id": "r1",
        "review_date": "2026-06-03",
        "review_notes": "fixture",
        "train_eligible": "exclude",
        "validation_eligible": "exclude",
        "test_eligible": test,
        "scan_history_record_id": "",
    }


class FieldBaselineEvaluationTest(unittest.TestCase):
    def test_excludes_weak_labels_from_test_ground_truth(self):
        with TemporaryDirectory() as d:
            manifest = os.path.join(d, "manifest.csv")
            with open(manifest, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=FIELD_COLUMNS)
                writer.writeheader()
                writer.writerow(field_row("a", "FMD"))
                writer.writerow(field_row("b", "LSD", tier="farmer_weak"))

            examples = load_field_examples(manifest, "test")

        self.assertEqual([e.image_id for e in examples], ["a"])

    def test_metrics_include_insufficient_and_false_confident_rates(self):
        examples = [
            type("Example", (), {"image_id": "a", "true_label": "FMD"})(),
            type("Example", (), {"image_id": "b", "true_label": "LSD"})(),
            type("Example", (), {"image_id": "c", "true_label": "healthy"})(),
        ]
        predictions = {
            "a": type("Prediction", (), {"image_id": "a", "predicted_label": "FMD", "confidence": 0.90, "scores": {"FMD": 0.90, "LSD": 0.05, "healthy": 0.05}})(),
            "b": type("Prediction", (), {"image_id": "b", "predicted_label": "LSD", "confidence": 0.66, "scores": {"FMD": 0.20, "LSD": 0.66, "healthy": 0.14}})(),
            "c": type("Prediction", (), {"image_id": "c", "predicted_label": "FMD", "confidence": 0.82, "scores": {"FMD": 0.82, "LSD": 0.10, "healthy": 0.08}})(),
        }

        metrics = evaluate(examples, predictions)

        self.assertEqual(metrics["evaluated_count"], 3)
        self.assertEqual(metrics["confusion_matrix"]["LSD"]["INSUFFICIENT_VISUAL_EVIDENCE"], 1)
        self.assertAlmostEqual(metrics["insufficient_visual_evidence_rate"], 1 / 3)
        self.assertAlmostEqual(metrics["false_confident_result_rate"], 1 / 3)

    def test_cli_writes_report_from_example_templates(self):
        with TemporaryDirectory() as d:
            out = os.path.join(d, "report.md")
            result = subprocess.run(
                [
                    sys.executable,
                    "docs/model/field_baseline_evaluation.py",
                    "--field-manifest", "docs/model/templates/field_manifest_eval_example.csv",
                    "--predictions", "docs/model/templates/field_predictions_example.csv",
                    "--split", "test",
                    "--out", out,
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            content = open(out, encoding="utf-8").read()

        self.assertIn("Macro F1", content)
        self.assertIn("False Confident Result rate", content)


if __name__ == "__main__":
    unittest.main()
