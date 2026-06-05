"""
Tests for model selection logic (issue #21).

Verifies selection behavior using metric fixtures covering:
  - All candidates pass -> highest macro F1 wins (with Android viability)
  - Candidate rejected for per-class F1 below floor
  - Tied macro F1 -> tie-breaker by accuracy then TFLite size
  - Under-target scenario -> experimental/demo with follow-up
  - No candidates provided
  - Real results from the Kaggle run
"""

import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Load the selection module from docs/team-1-image/model/model_selection.py
THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[3]
SELECTION_PATH = REPO_ROOT / "docs" / "team-1-image" / "model" / "model_selection.py"


def _load_selection():
    spec = importlib.util.spec_from_file_location("model_selection", SELECTION_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestSelectionLogic(unittest.TestCase):
    """Deterministic tests for select_model() with metric fixtures."""

    @classmethod
    def setUpClass(cls):
        cls.sel = _load_selection()

    def _make_candidate(self, name, accuracy, macro_f1, per_class_f1,
                        tflite_size_mb=5.0, params=1000000):
        return self.sel.CandidateResult(
            name=name,
            accuracy=accuracy,
            macro_f1=macro_f1,
            per_class_f1=per_class_f1,
            params=params,
            keras_size_mb=10.0,
            tflite_size_mb=tflite_size_mb,
        )

    # ── All pass: highest macro F1 wins ──────────────────────────────────

    def test_highest_macro_f1_wins(self):
        candidates = [
            self._make_candidate("model_a", 0.90, 0.89,
                                 {"FMD": 0.88, "LSD": 0.90, "healthy": 0.89}),
            self._make_candidate("model_b", 0.95, 0.94,
                                 {"FMD": 0.93, "LSD": 0.95, "healthy": 0.94}),
        ]
        decision = self.sel.select_model(candidates)
        self.assertEqual(decision.status, "selected")
        self.assertEqual(decision.selected.name, "model_b")

    # ── Per-class F1 rejection ───────────────────────────────────────────

    def test_reject_below_per_class_f1_floor(self):
        candidates = [
            self._make_candidate("bad_model", 0.92, 0.91,
                                 {"FMD": 0.80, "LSD": 0.95, "healthy": 0.92}),
            self._make_candidate("good_model", 0.90, 0.89,
                                 {"FMD": 0.88, "LSD": 0.90, "healthy": 0.89}),
        ]
        decision = self.sel.select_model(candidates)
        self.assertEqual(decision.status, "selected")
        self.assertEqual(decision.selected.name, "good_model")
        self.assertEqual(len(decision.rejected), 1)
        self.assertEqual(decision.rejected[0][0].name, "bad_model")
        self.assertIn("F1 floor", decision.rejected[0][1])

    # ── Tie-breaker: accuracy then TFLite size ───────────────────────────

    def test_tie_breaker_accuracy(self):
        # Same macro F1 (within threshold), different accuracy.
        candidates = [
            self._make_candidate("model_a", 0.93, 0.920,
                                 {"FMD": 0.91, "LSD": 0.93, "healthy": 0.92},
                                 tflite_size_mb=5.0),
            self._make_candidate("model_b", 0.95, 0.922,
                                 {"FMD": 0.91, "LSD": 0.93, "healthy": 0.92},
                                 tflite_size_mb=5.0),
        ]
        decision = self.sel.select_model(candidates)
        self.assertEqual(decision.selected.name, "model_b")

    def test_tie_breaker_tflite_size(self):
        # Same macro F1 and accuracy, different TFLite size.
        candidates = [
            self._make_candidate("big_model", 0.95, 0.940,
                                 {"FMD": 0.93, "LSD": 0.95, "healthy": 0.94},
                                 tflite_size_mb=8.0),
            self._make_candidate("small_model", 0.95, 0.940,
                                 {"FMD": 0.93, "LSD": 0.95, "healthy": 0.94},
                                 tflite_size_mb=3.0),
        ]
        decision = self.sel.select_model(candidates)
        self.assertEqual(decision.selected.name, "small_model")

    # ── Android viability fallback ───────────────────────────────────────

    def test_android_viability_fallback(self):
        # Best macro F1 model exceeds TFLite budget -> fall back.
        candidates = [
            self._make_candidate("big_accurate", 0.99, 0.99,
                                 {"FMD": 0.99, "LSD": 0.99, "healthy": 0.99},
                                 tflite_size_mb=30.0),
            self._make_candidate("small_good", 0.97, 0.96,
                                 {"FMD": 0.95, "LSD": 0.97, "healthy": 0.96},
                                 tflite_size_mb=8.0),
        ]
        decision = self.sel.select_model(candidates)
        self.assertEqual(decision.status, "selected")
        self.assertEqual(decision.selected.name, "small_good")
        self.assertTrue(any("exceeds" in w for w in decision.warnings))

    # ── Under-target: experimental/demo ──────────────────────────────────

    def test_all_below_floor_marks_experimental(self):
        candidates = [
            self._make_candidate("weak_a", 0.80, 0.78,
                                 {"FMD": 0.70, "LSD": 0.82, "healthy": 0.80}),
            self._make_candidate("weak_b", 0.82, 0.80,
                                 {"FMD": 0.75, "LSD": 0.83, "healthy": 0.82}),
        ]
        decision = self.sel.select_model(candidates)
        self.assertEqual(decision.status, "experimental_demo")
        self.assertEqual(decision.selected.name, "weak_b")  # best macro F1
        self.assertTrue(len(decision.follow_up) > 0)
        self.assertIn("experimental/demo", decision.reason)

    # ── No candidates ────────────────────────────────────────────────────

    def test_no_candidates(self):
        decision = self.sel.select_model([])
        self.assertEqual(decision.status, "no_candidates")
        self.assertIsNone(decision.selected)

    # ── Real results from Kaggle run ─────────────────────────────────────

    def test_real_results_select_mobilenetv2(self):
        """The real Kaggle results should select MobileNetV2 (Android viable)."""
        results_dir = REPO_ROOT / "docs" / "team-1-image" / "model" / "results"
        if not results_dir.exists():
            self.skipTest("Real results not available")
        candidates = self.sel.load_results_dir(str(results_dir))
        self.assertEqual(len(candidates), 3)
        decision = self.sel.select_model(candidates)
        self.assertEqual(decision.status, "selected")
        self.assertEqual(decision.selected.name, "mobilenetv2")
        # All candidates should pass (none rejected).
        self.assertEqual(len(decision.rejected), 0)
        self.assertEqual(len(decision.passed), 3)

    # ── Report formatting ────────────────────────────────────────────────

    def test_report_contains_key_sections(self):
        candidates = [
            self._make_candidate("test_model", 0.92, 0.91,
                                 {"FMD": 0.90, "LSD": 0.92, "healthy": 0.91}),
        ]
        decision = self.sel.select_model(candidates)
        report = self.sel.format_report(candidates, decision)
        self.assertIn("# Model Selection Report", report)
        self.assertIn("Selection Rules", report)
        self.assertIn("Candidate Results", report)
        self.assertIn("Decision", report)
        self.assertIn("Failure Policy", report)
        self.assertIn("Wording Compliance", report)
        self.assertIn("early detection", report)

    def test_experimental_report_has_follow_up(self):
        candidates = [
            self._make_candidate("weak", 0.80, 0.78,
                                 {"FMD": 0.70, "LSD": 0.82, "healthy": 0.80}),
        ]
        decision = self.sel.select_model(candidates)
        report = self.sel.format_report(candidates, decision)
        self.assertIn("experimental/demo", report)
        self.assertIn("Follow-up Recommendations", report)
        self.assertIn("MUST NOT be deployed", report)


if __name__ == "__main__":
    unittest.main()
