import json
import os
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import importlib.util  # noqa: E402

MODEL_DOCS = os.path.join(REPO_ROOT, 'docs', 'team-1-image', 'model')
spec = importlib.util.spec_from_file_location('yolo_symptom_detector', os.path.join(MODEL_DOCS, 'yolo_symptom_detector.py'))
yolo_symptom_detector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = yolo_symptom_detector
spec.loader.exec_module(yolo_symptom_detector)
convert_annotations_to_yolo = yolo_symptom_detector.convert_annotations_to_yolo
evaluate_predictions = yolo_symptom_detector.evaluate_predictions


class YoloSymptomDetectorTest(unittest.TestCase):
    def test_convert_annotations_writes_yolo_labels_and_yaml(self):
        with TemporaryDirectory() as out:
            grouped = convert_annotations_to_yolo(
                os.path.join(REPO_ROOT, "docs/team-1-image/model/templates/symptom_region_annotations_example.csv"),
                out,
            )
            label_path = os.path.join(out, "labels", "field-0001.txt")
            data_path = os.path.join(out, "data.yaml")

            self.assertIn("field-0001", grouped)
            self.assertTrue(os.path.exists(label_path))
            self.assertTrue(os.path.exists(data_path))
            content = open(label_path, encoding="utf-8").read()

        self.assertIn("0 0.340000 0.445000 0.240000 0.270000", content)

    def test_evaluate_predictions_reports_precision_recall(self):
        metrics = evaluate_predictions(
            os.path.join(REPO_ROOT, "docs/team-1-image/model/templates/symptom_region_annotations_example.csv"),
            os.path.join(REPO_ROOT, "docs/team-1-image/model/templates/yolo_predictions_example.csv"),
        )

        self.assertEqual(metrics["overall"]["tp"], 4)
        self.assertEqual(metrics["overall"]["fp"], 0)
        self.assertAlmostEqual(metrics["overall"]["precision"], 1.0)
        self.assertAlmostEqual(metrics["overall"]["recall"], 1.0)

    def test_cli_evaluate_writes_metrics_json(self):
        with TemporaryDirectory() as d:
            out = os.path.join(d, "metrics.json")
            result = subprocess.run(
                [
                    sys.executable,
                    "docs/team-1-image/model/yolo_symptom_detector.py",
                    "evaluate",
                    "--ground-truth", "docs/team-1-image/model/templates/symptom_region_annotations_example.csv",
                    "--predictions", "docs/team-1-image/model/templates/yolo_predictions_example.csv",
                    "--out", out,
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            metrics = json.load(open(out, encoding="utf-8"))

        self.assertIn("per_class", metrics)
        self.assertIn("overall", metrics)


if __name__ == "__main__":
    unittest.main()
