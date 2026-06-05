"""
Tests for TFLite export and parity logic (issue #22).

Verifies parity threshold checking and report generation using synthetic
metric fixtures. Does NOT require TensorFlow or a real model file.
"""

import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[3]
TFLITE_PATH = REPO_ROOT / "docs" / "model" / "tflite_export.py"


def _load_tflite():
    spec = importlib.util.spec_from_file_location("tflite_export", TFLITE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestParityThresholds(unittest.TestCase):
    """Deterministic tests for check_parity() with metric fixtures."""

    @classmethod
    def setUpClass(cls):
        cls.tfl = _load_tflite()

    def _make_metrics(self, accuracy, macro_f1, per_class_f1, predictions=None):
        return self.tfl.ModelMetrics(
            accuracy=accuracy,
            macro_f1=macro_f1,
            per_class_f1=per_class_f1,
            predictions=predictions or [],
        )

    # ── Perfect parity (no drop) ─────────────────────────────────────────

    def test_perfect_parity_passes(self):
        keras = self._make_metrics(0.97, 0.97,
                                   {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96})
        tflite = self._make_metrics(0.97, 0.97,
                                    {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96})
        result = self.tfl.check_parity(keras, tflite, 8.0,
                                       self.tfl.CLASSES, self.tfl.CLASSES)
        self.assertTrue(result.overall_pass)
        self.assertEqual(result.accuracy_drop, 0.0)
        self.assertEqual(result.macro_f1_drop, 0.0)

    # ── Accuracy drop exceeds threshold ──────────────────────────────────

    def test_accuracy_drop_fails(self):
        keras = self._make_metrics(0.97, 0.97,
                                   {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96})
        tflite = self._make_metrics(0.94, 0.94,
                                    {"FMD": 0.95, "LSD": 0.94, "healthy": 0.93})
        result = self.tfl.check_parity(keras, tflite, 8.0,
                                       self.tfl.CLASSES, self.tfl.CLASSES)
        self.assertFalse(result.passes_accuracy)
        self.assertFalse(result.overall_pass)
        self.assertAlmostEqual(result.accuracy_drop, 0.03, places=2)

    # ── Macro F1 drop exceeds threshold ──────────────────────────────────

    def test_macro_f1_drop_fails(self):
        keras = self._make_metrics(0.97, 0.97,
                                   {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96})
        tflite = self._make_metrics(0.96, 0.94,
                                    {"FMD": 0.96, "LSD": 0.94, "healthy": 0.93})
        result = self.tfl.check_parity(keras, tflite, 8.0,
                                       self.tfl.CLASSES, self.tfl.CLASSES)
        self.assertFalse(result.passes_macro_f1)
        self.assertFalse(result.overall_pass)

    # ── Per-class F1 drop exceeds threshold ──────────────────────────────

    def test_per_class_f1_drop_fails(self):
        keras = self._make_metrics(0.97, 0.97,
                                   {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96})
        # FMD drops by 4 pp (> 3 pp threshold).
        tflite = self._make_metrics(0.96, 0.96,
                                    {"FMD": 0.94, "LSD": 0.97, "healthy": 0.96})
        result = self.tfl.check_parity(keras, tflite, 8.0,
                                       self.tfl.CLASSES, self.tfl.CLASSES)
        self.assertFalse(result.passes_per_class_f1)
        self.assertEqual(result.max_per_class_f1_drop_class, "FMD")
        self.assertAlmostEqual(result.max_per_class_f1_drop, 0.04, places=2)

    # ── Class-index mismatch ─────────────────────────────────────────────

    def test_class_index_mismatch_fails(self):
        keras = self._make_metrics(0.97, 0.97,
                                   {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96})
        tflite = self._make_metrics(0.97, 0.97,
                                    {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96})
        # Different class order.
        result = self.tfl.check_parity(keras, tflite, 8.0,
                                       ["FMD", "LSD", "healthy"],
                                       ["healthy", "FMD", "LSD"])
        self.assertFalse(result.passes_class_index)
        self.assertFalse(result.overall_pass)

    # ── TFLite size exceeds budget ───────────────────────────────────────

    def test_size_exceeds_budget_fails(self):
        keras = self._make_metrics(0.97, 0.97,
                                   {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96})
        tflite = self._make_metrics(0.97, 0.97,
                                    {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96})
        result = self.tfl.check_parity(keras, tflite, 15.0,
                                       self.tfl.CLASSES, self.tfl.CLASSES)
        self.assertFalse(result.passes_size)
        self.assertFalse(result.overall_pass)

    # ── Within threshold passes ──────────────────────────────────────────

    def test_within_threshold_passes(self):
        keras = self._make_metrics(0.97, 0.97,
                                   {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96})
        # Small drops within all thresholds.
        tflite = self._make_metrics(0.955, 0.955,
                                    {"FMD": 0.96, "LSD": 0.95, "healthy": 0.94})
        result = self.tfl.check_parity(keras, tflite, 8.5,
                                       self.tfl.CLASSES, self.tfl.CLASSES)
        self.assertTrue(result.passes_accuracy)  # 1.5 pp < 2 pp
        self.assertTrue(result.passes_macro_f1)  # 1.5 pp < 2 pp
        self.assertTrue(result.passes_per_class_f1)  # max 2 pp < 3 pp
        self.assertTrue(result.overall_pass)

    # ── Probability drift ────────────────────────────────────────────────

    def test_probability_drift_computed(self):
        keras = self._make_metrics(0.97, 0.97,
                                   {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96},
                                   predictions=[[0.9, 0.05, 0.05], [0.1, 0.8, 0.1]])
        tflite = self._make_metrics(0.97, 0.97,
                                    {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96},
                                    predictions=[[0.88, 0.06, 0.06], [0.12, 0.78, 0.1]])
        result = self.tfl.check_parity(keras, tflite, 8.0,
                                       self.tfl.CLASSES, self.tfl.CLASSES)
        self.assertIn("mean_abs_diff", result.probability_drift_summary)
        self.assertGreater(result.probability_drift_summary["mean_abs_diff"], 0)

    # ── Report generation ────────────────────────────────────────────────

    def test_report_contains_key_sections(self):
        keras = self._make_metrics(0.97, 0.97,
                                   {"FMD": 0.98, "LSD": 0.97, "healthy": 0.96})
        parity = self.tfl.check_parity(keras, keras, 8.0,
                                       self.tfl.CLASSES, self.tfl.CLASSES)
        report = self.tfl.format_parity_report(keras, parity, parity, 9.0, 5.0)
        self.assertIn("# TFLite Parity Report", report)
        self.assertIn("Preprocessing", report)
        self.assertIn("Parity Thresholds", report)
        self.assertIn("Float32 TFLite", report)
        self.assertIn("Dynamic-Range Quantized", report)
        self.assertIn("Verdict", report)
        self.assertIn("Full Int8", report)
        self.assertIn("Offline Latency", report)

    # ── Dry run ──────────────────────────────────────────────────────────

    def test_dry_run_produces_report(self):
        with TemporaryDirectory() as out:
            rc = self.tfl.run(["--dry-run", "--out", out])
            self.assertEqual(rc, 0)
            report_path = Path(out) / "TFLITE_PARITY_REPORT.md"
            self.assertTrue(report_path.exists())
            preproc_path = Path(out) / "preprocessing.json"
            self.assertTrue(preproc_path.exists())
            preproc = json.loads(preproc_path.read_text())
            self.assertEqual(preproc["input_size"], [224, 224])
            self.assertEqual(preproc["rescale"], "1/255")
            self.assertIn("exif_orientation_correction", preproc)

    # ── Constants ────────────────────────────────────────────────────────

    def test_preprocessing_spec_complete(self):
        spec = self.tfl.PREPROCESSING_SPEC
        self.assertEqual(spec["input_size"], [224, 224])
        self.assertEqual(spec["channels"], 3)
        self.assertEqual(spec["color_mode"], "RGB")
        self.assertEqual(spec["rescale"], "1/255")
        self.assertIn("exif_orientation_correction", spec)


if __name__ == "__main__":
    unittest.main()
