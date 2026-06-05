import json
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import importlib.util  # noqa: E402

MODEL_DOCS = os.path.join(REPO_ROOT, 'docs', 'team-1-image', 'model')
spec = importlib.util.spec_from_file_location('two_stage_fusion_evaluator', os.path.join(MODEL_DOCS, 'two_stage_fusion_evaluator.py'))
two_stage_fusion_evaluator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = two_stage_fusion_evaluator
spec.loader.exec_module(two_stage_fusion_evaluator)
aggregate_top_crops = two_stage_fusion_evaluator.aggregate_top_crops
evaluate_fusion = two_stage_fusion_evaluator.evaluate_fusion
success_gate = two_stage_fusion_evaluator.success_gate


class TwoStageFusionEvaluatorTest(unittest.TestCase):
    def test_aggregates_top_three_crop_scores_by_per_class_max(self):
        rows = [
            {"image_id": "a", "detector_confidence": 0.9, "symptom_region_type": "fmd_mouth_lesion", "scores": {"FMD": 0.7, "LSD": 0.1, "healthy": 0.2}},
            {"image_id": "a", "detector_confidence": 0.8, "symptom_region_type": "fmd_hoof_lesion", "scores": {"FMD": 0.8, "LSD": 0.2, "healthy": 0.0}},
            {"image_id": "a", "detector_confidence": 0.7, "symptom_region_type": "fmd_hoof_lesion", "scores": {"FMD": 0.6, "LSD": 0.4, "healthy": 0.0}},
            {"image_id": "a", "detector_confidence": 0.1, "symptom_region_type": "lsd_skin_nodule", "scores": {"FMD": 0.0, "LSD": 0.9, "healthy": 0.0}},
        ]
        scores, _ = aggregate_top_crops(rows)

        self.assertEqual(scores["a"]["FMD"], 0.8)
        self.assertEqual(scores["a"]["LSD"], 0.4)

    def test_fusion_reports_success_gate_inputs_and_review_conflict(self):
        truth = {"a": "FMD", "b": "LSD", "c": "healthy"}
        full = {
            "a": {"FMD": 0.90, "LSD": 0.05, "healthy": 0.05},
            "b": {"FMD": 0.20, "LSD": 0.66, "healthy": 0.14},
            "c": {"FMD": 0.82, "LSD": 0.10, "healthy": 0.08},
        }
        crops = [
            {"image_id": "a", "detector_confidence": 0.9, "symptom_region_type": "fmd_mouth_lesion", "scores": {"FMD": 0.96, "LSD": 0.02, "healthy": 0.02}},
            {"image_id": "b", "detector_confidence": 0.9, "symptom_region_type": "lsd_skin_nodule", "scores": {"FMD": 0.04, "LSD": 0.93, "healthy": 0.03}},
            {"image_id": "c", "detector_confidence": 0.8, "symptom_region_type": "lsd_skin_nodule", "scores": {"FMD": 0.10, "LSD": 0.09, "healthy": 0.81}},
        ]
        metrics = evaluate_fusion(truth, full, crops)

        self.assertEqual(metrics["fusion"]["full_image_weight"], 0.4)
        self.assertEqual(metrics["fusion"]["top_k_boxes"], 3)
        self.assertEqual(metrics["needs_review_rate"], 0.0)
        self.assertEqual(metrics["fmd_recall"], 1.0)
        self.assertEqual(metrics["lsd_recall"], 1.0)

    def test_success_gate_compares_against_baseline(self):
        two_stage = {"false_confident_result_rate": 0.0, "macro_f1": 0.8, "fmd_recall": 1.0, "lsd_recall": 0.9, "insufficient_visual_evidence_rate": 0.2}
        baseline = {"false_confident_result_rate": 0.2, "macro_f1": 0.7, "fmd_recall": 1.0, "lsd_recall": 0.92, "insufficient_visual_evidence_rate": 0.3}

        gate = success_gate(two_stage, baseline)

        self.assertTrue(gate["passed"])


if __name__ == "__main__":
    unittest.main()
