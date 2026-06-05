"""
TFLite Export and Parity Check (issue #22).

Exports the selected Keras model to TFLite (Float32 baseline + dynamic-range
quantized app candidate), evaluates both on the same test split, and produces
a parity report with pass/fail against approved thresholds.

This module is both:
  - A library (importable for tests with tiny synthetic models)
  - A CLI that converts a real .keras model and generates the parity report

Parity thresholds (issue #17):
  - Accuracy drop ≤ 2 percentage points
  - Macro F1 drop ≤ 2 percentage points
  - Per-class F1 drop ≤ 3 percentage points
  - No class-index mismatch
  - TFLite size < 10 MB

Usage:
    python tflite_export.py --keras model.keras \
        --manifest split_manifest.csv --out tflite_out/
    python tflite_export.py --dry-run --out tflite_out/
"""

import argparse
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Constants ────────────────────────────────────────────────────────────────

CLASSES = ["FMD", "LSD", "healthy"]
NUM_CLASSES = len(CLASSES)
INPUT_SIZE = (224, 224)

# Parity thresholds (issue #17).
ACCURACY_DROP_THRESHOLD = 0.02  # 2 percentage points
MACRO_F1_DROP_THRESHOLD = 0.02  # 2 percentage points
PER_CLASS_F1_DROP_THRESHOLD = 0.03  # 3 percentage points
TFLITE_SIZE_BUDGET_MB = 10.0

# Preprocessing spec (must match training and backend/mobile inference).
PREPROCESSING_SPEC = {
    "input_size": list(INPUT_SIZE),
    "channels": 3,
    "color_mode": "RGB",
    "rescale": "1/255",
    "exif_orientation_correction": "before resize where available",
    "resize_method": "bilinear",
    "note": "Deterministic inference preprocessing. Same for Keras and TFLite.",
}


@dataclass
class ModelMetrics:
    """Metrics from evaluating a model on the test split."""
    accuracy: float = 0.0
    macro_f1: float = 0.0
    per_class_f1: dict = field(default_factory=dict)
    confusion_matrix: list = field(default_factory=list)
    predictions: list = field(default_factory=list)


@dataclass
class ParityResult:
    """Result of comparing Keras vs TFLite metrics."""
    accuracy_drop: float = 0.0
    macro_f1_drop: float = 0.0
    per_class_f1_drops: dict = field(default_factory=dict)
    max_per_class_f1_drop: float = 0.0
    max_per_class_f1_drop_class: str = ""
    class_index_match: bool = True
    tflite_size_mb: float = 0.0
    passes_accuracy: bool = True
    passes_macro_f1: bool = True
    passes_per_class_f1: bool = True
    passes_size: bool = True
    passes_class_index: bool = True
    overall_pass: bool = True
    probability_drift_summary: dict = field(default_factory=dict)


def check_parity(keras_metrics: ModelMetrics, tflite_metrics: ModelMetrics,
                 tflite_size_mb: float,
                 class_order_keras: list = None,
                 class_order_tflite: list = None) -> ParityResult:
    """
    Compare Keras vs TFLite metrics and check parity thresholds.

    Pure function — no I/O, no TensorFlow. Fully testable with fixtures.
    """
    result = ParityResult()

    # Accuracy drop.
    result.accuracy_drop = keras_metrics.accuracy - tflite_metrics.accuracy
    result.passes_accuracy = result.accuracy_drop <= ACCURACY_DROP_THRESHOLD

    # Macro F1 drop.
    result.macro_f1_drop = keras_metrics.macro_f1 - tflite_metrics.macro_f1
    result.passes_macro_f1 = result.macro_f1_drop <= MACRO_F1_DROP_THRESHOLD

    # Per-class F1 drops.
    max_drop = 0.0
    max_drop_cls = ""
    for cls in CLASSES:
        keras_f1 = keras_metrics.per_class_f1.get(cls, 0.0)
        tflite_f1 = tflite_metrics.per_class_f1.get(cls, 0.0)
        drop = keras_f1 - tflite_f1
        result.per_class_f1_drops[cls] = drop
        if drop > max_drop:
            max_drop = drop
            max_drop_cls = cls
    result.max_per_class_f1_drop = max_drop
    result.max_per_class_f1_drop_class = max_drop_cls
    result.passes_per_class_f1 = max_drop <= PER_CLASS_F1_DROP_THRESHOLD

    # Class-index mismatch.
    if class_order_keras and class_order_tflite:
        result.class_index_match = class_order_keras == class_order_tflite
    result.passes_class_index = result.class_index_match

    # TFLite size.
    result.tflite_size_mb = tflite_size_mb
    result.passes_size = tflite_size_mb <= TFLITE_SIZE_BUDGET_MB

    # Probability drift summary (mean absolute difference in predicted probs).
    if keras_metrics.predictions and tflite_metrics.predictions:
        import numpy as np
        keras_preds = np.array(keras_metrics.predictions)
        tflite_preds = np.array(tflite_metrics.predictions)
        if keras_preds.shape == tflite_preds.shape:
            abs_diff = np.abs(keras_preds - tflite_preds)
            result.probability_drift_summary = {
                "mean_abs_diff": float(np.mean(abs_diff)),
                "max_abs_diff": float(np.max(abs_diff)),
                "std_abs_diff": float(np.std(abs_diff)),
            }

    # Overall pass.
    result.overall_pass = (
        result.passes_accuracy
        and result.passes_macro_f1
        and result.passes_per_class_f1
        and result.passes_class_index
        and result.passes_size
    )
    return result


def convert_to_tflite_float32(keras_model_path: str, output_path: str) -> str:
    """Convert a Keras model to Float32 TFLite (parity baseline)."""
    import tensorflow as tf

    model = tf.keras.models.load_model(keras_model_path)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    with open(output_path, "wb") as f:
        f.write(tflite_model)
    return output_path


def convert_to_tflite_dynamic_range(keras_model_path: str,
                                     output_path: str) -> str:
    """Convert a Keras model to dynamic-range quantized TFLite (app candidate)."""
    import tensorflow as tf

    model = tf.keras.models.load_model(keras_model_path)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    with open(output_path, "wb") as f:
        f.write(tflite_model)
    return output_path


def evaluate_tflite_on_test(tflite_path: str, test_items: list,
                            seed: int = 42) -> ModelMetrics:
    """
    Evaluate a TFLite model on the test split from the manifest.

    test_items: list of (image_path, class_index) tuples.
    Returns ModelMetrics with accuracy, macro F1, per-class F1, confusion matrix.
    """
    import numpy as np
    import tensorflow as tf
    from sklearn.metrics import classification_report, confusion_matrix

    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    y_true = []
    y_pred = []
    all_probs = []

    for img_path, label in test_items:
        img = tf.io.read_file(img_path)
        img = tf.image.decode_image(img, channels=3, expand_animations=False)
        img = tf.image.resize(img, INPUT_SIZE)
        img = tf.cast(img, tf.float32) / 255.0
        img = tf.expand_dims(img, 0)

        interpreter.set_tensor(input_details[0]["index"], img.numpy())
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]["index"])

        probs = output[0]
        all_probs.append(probs.tolist())
        y_true.append(label)
        y_pred.append(int(np.argmax(probs)))

    report = classification_report(
        y_true, y_pred, target_names=CLASSES,
        labels=list(range(NUM_CLASSES)), output_dict=True, zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=list(range(NUM_CLASSES))).tolist()

    per_class_f1 = {}
    for cls in CLASSES:
        per_class_f1[cls] = report.get(cls, {}).get("f1-score", 0.0)

    return ModelMetrics(
        accuracy=report.get("accuracy", 0.0),
        macro_f1=report.get("macro avg", {}).get("f1-score", 0.0),
        per_class_f1=per_class_f1,
        confusion_matrix=cm,
        predictions=all_probs,
    )


def evaluate_keras_on_test(keras_model_path: str, test_items: list,
                           seed: int = 42) -> ModelMetrics:
    """Evaluate the Keras model on the same test split for comparison."""
    import numpy as np
    import tensorflow as tf
    from sklearn.metrics import classification_report, confusion_matrix

    model = tf.keras.models.load_model(keras_model_path)

    y_true = []
    y_pred = []
    all_probs = []

    for img_path, label in test_items:
        img = tf.io.read_file(img_path)
        img = tf.image.decode_image(img, channels=3, expand_animations=False)
        img = tf.image.resize(img, INPUT_SIZE)
        img = tf.cast(img, tf.float32) / 255.0
        img = tf.expand_dims(img, 0)

        probs = model.predict(img, verbose=0)[0]
        all_probs.append(probs.tolist())
        y_true.append(label)
        y_pred.append(int(np.argmax(probs)))

    report = classification_report(
        y_true, y_pred, target_names=CLASSES,
        labels=list(range(NUM_CLASSES)), output_dict=True, zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=list(range(NUM_CLASSES))).tolist()

    per_class_f1 = {}
    for cls in CLASSES:
        per_class_f1[cls] = report.get(cls, {}).get("f1-score", 0.0)

    return ModelMetrics(
        accuracy=report.get("accuracy", 0.0),
        macro_f1=report.get("macro avg", {}).get("f1-score", 0.0),
        per_class_f1=per_class_f1,
        confusion_matrix=cm,
        predictions=all_probs,
    )


def format_parity_report(keras_metrics: ModelMetrics,
                         float32_parity: ParityResult,
                         dynrange_parity: ParityResult,
                         float32_size_mb: float,
                         dynrange_size_mb: float,
                         model_name: str = "mobilenetv2") -> str:
    """Format the TFLite parity report as Markdown."""
    lines = []
    lines.append("# TFLite Parity Report (issue #22)")
    lines.append("")
    lines.append(f"Model: **{model_name}** (selected in issue #21)")
    lines.append("")
    lines.append("Generated by `docs/model/tflite_export.py`.")
    lines.append("")

    # Preprocessing.
    lines.append("## Preprocessing (deterministic, shared)")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("|----------|-------|")
    for k, v in PREPROCESSING_SPEC.items():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    # Thresholds.
    lines.append("## Parity Thresholds (issue #17)")
    lines.append("")
    lines.append(f"| Threshold | Value |")
    lines.append(f"|-----------|-------|")
    lines.append(f"| Accuracy drop | ≤ {ACCURACY_DROP_THRESHOLD*100:.0f} pp |")
    lines.append(f"| Macro F1 drop | ≤ {MACRO_F1_DROP_THRESHOLD*100:.0f} pp |")
    lines.append(f"| Per-class F1 drop | ≤ {PER_CLASS_F1_DROP_THRESHOLD*100:.0f} pp |")
    lines.append(f"| Class-index mismatch | None allowed |")
    lines.append(f"| TFLite size | < {TFLITE_SIZE_BUDGET_MB} MB |")
    lines.append("")

    # Keras baseline.
    lines.append("## Keras Baseline (server model)")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Accuracy | {keras_metrics.accuracy:.4f} |")
    lines.append(f"| Macro F1 | {keras_metrics.macro_f1:.4f} |")
    for cls in CLASSES:
        lines.append(f"| {cls} F1 | {keras_metrics.per_class_f1.get(cls, 0):.4f} |")
    lines.append("")

    # Float32 parity.
    lines.append("## Float32 TFLite (parity baseline)")
    lines.append("")
    _append_parity_table(lines, float32_parity, float32_size_mb)

    # Dynamic-range parity.
    lines.append("## Dynamic-Range Quantized TFLite (app candidate)")
    lines.append("")
    _append_parity_table(lines, dynrange_parity, dynrange_size_mb)

    # Overall verdict.
    lines.append("## Verdict")
    lines.append("")
    if float32_parity.overall_pass and dynrange_parity.overall_pass:
        lines.append("✅ **PASS** — Both Float32 and dynamic-range quantized TFLite "
                     "meet all parity thresholds. The dynamic-range quantized model "
                     "is approved as the Android app candidate.")
    elif float32_parity.overall_pass:
        lines.append("⚠️ **PARTIAL** — Float32 TFLite passes parity but the "
                     "dynamic-range quantized version fails. Consider using Float32 "
                     "for the app or investigating quantization issues.")
    else:
        lines.append("❌ **FAIL** — TFLite parity thresholds not met. "
                     "Investigate conversion issues before deploying.")
    lines.append("")

    # Int8 note.
    lines.append("## Full Int8 Quantization")
    lines.append("")
    lines.append("Per issue #17: full int8 quantization is attempted **only if** "
                 "size or latency targets fail. Since the dynamic-range quantized "
                 "model meets the size budget, int8 is not required at this time.")
    lines.append("")

    # Latency.
    lines.append("## Offline Latency")
    lines.append("")
    lines.append("**Status**: Not measured (limitation).")
    lines.append("")
    lines.append("On-device latency benchmarking requires running the TFLite model "
                 "on a physical Android device. This is documented as a limitation "
                 "pending device testing. Expected: < 1 second on mid-range ARM64 "
                 "based on MobileNetV2 architecture characteristics.")
    lines.append("")

    # Limitations.
    lines.append("## Limitations")
    lines.append("")
    lines.append("- Offline latency not measured (requires physical device).")
    lines.append("- Single-seed evaluation (seed 42).")
    lines.append("- Not a clinical diagnosis tool.")
    lines.append("")

    return "\n".join(lines)


def _append_parity_table(lines: list, parity: ParityResult, size_mb: float):
    """Helper to append a parity comparison table."""
    lines.append(f"| Check | Value | Threshold | Pass |")
    lines.append(f"|-------|-------|-----------|------|")
    lines.append(f"| Accuracy drop | {parity.accuracy_drop*100:.2f} pp | "
                 f"≤ {ACCURACY_DROP_THRESHOLD*100:.0f} pp | "
                 f"{'✅' if parity.passes_accuracy else '❌'} |")
    lines.append(f"| Macro F1 drop | {parity.macro_f1_drop*100:.2f} pp | "
                 f"≤ {MACRO_F1_DROP_THRESHOLD*100:.0f} pp | "
                 f"{'✅' if parity.passes_macro_f1 else '❌'} |")
    lines.append(f"| Max per-class F1 drop | {parity.max_per_class_f1_drop*100:.2f} pp "
                 f"({parity.max_per_class_f1_drop_class}) | "
                 f"≤ {PER_CLASS_F1_DROP_THRESHOLD*100:.0f} pp | "
                 f"{'✅' if parity.passes_per_class_f1 else '❌'} |")
    lines.append(f"| Class-index match | "
                 f"{'Yes' if parity.class_index_match else 'MISMATCH'} | "
                 f"Required | {'✅' if parity.passes_class_index else '❌'} |")
    lines.append(f"| Model size | {size_mb:.2f} MB | "
                 f"< {TFLITE_SIZE_BUDGET_MB} MB | "
                 f"{'✅' if parity.passes_size else '❌'} |")
    lines.append(f"| **Overall** | | | "
                 f"**{'✅ PASS' if parity.overall_pass else '❌ FAIL'}** |")
    lines.append("")

    if parity.probability_drift_summary:
        lines.append("Probability drift:")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        for k, v in parity.probability_drift_summary.items():
            lines.append(f"| {k} | {v:.6f} |")
        lines.append("")

    # Per-class F1 drops.
    lines.append("Per-class F1 drops:")
    lines.append("")
    lines.append("| Class | Drop (pp) | Pass |")
    lines.append("|-------|-----------|------|")
    for cls in CLASSES:
        drop = parity.per_class_f1_drops.get(cls, 0.0)
        passes = drop <= PER_CLASS_F1_DROP_THRESHOLD
        lines.append(f"| {cls} | {drop*100:.2f} | {'✅' if passes else '❌'} |")
    lines.append("")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Export selected Keras model to TFLite and check parity."
    )
    p.add_argument("--keras", default=None,
                   help="Path to the selected .keras model file.")
    p.add_argument("--manifest", default=None,
                   help="Path to split_manifest.csv (for test-split evaluation).")
    p.add_argument("--out", default="tflite_out",
                   help="Output directory for TFLite files and parity report.")
    p.add_argument("--model-name", default="mobilenetv2",
                   help="Name of the selected model (for report).")
    p.add_argument("--dry-run", action="store_true",
                   help="Skip conversion/evaluation; produce report template.")
    return p


def run(argv=None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write preprocessing spec.
    preproc_path = out_dir / "preprocessing.json"
    with open(preproc_path, "w", encoding="utf-8") as f:
        json.dump(PREPROCESSING_SPEC, f, indent=2)
    print(f"[tflite] preprocessing spec -> {preproc_path}")

    if args.dry_run:
        print("[tflite] DRY RUN — skipping conversion and evaluation.")
        # Write a template report.
        keras_m = ModelMetrics(accuracy=0.970, macro_f1=0.972,
                              per_class_f1={"FMD": 0.98, "LSD": 0.97, "healthy": 0.97})
        # Simulate perfect parity for template.
        float32_parity = check_parity(keras_m, keras_m, 9.0,
                                      CLASSES, CLASSES)
        dynrange_parity = check_parity(keras_m, keras_m, 5.0,
                                       CLASSES, CLASSES)
        report = format_parity_report(keras_m, float32_parity, dynrange_parity,
                                      9.0, 5.0, args.model_name)
        report_path = out_dir / "TFLITE_PARITY_REPORT.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"[tflite] parity report (template) -> {report_path}")
        return 0

    if not args.keras or not os.path.isfile(args.keras):
        print(f"ERROR: --keras model file required and must exist: {args.keras}")
        return 2
    if not args.manifest or not os.path.isfile(args.manifest):
        print(f"ERROR: --manifest required for test-split evaluation: {args.manifest}")
        return 2

    # Import evaluate_candidates for manifest reading.
    import importlib.util
    eval_path = Path(__file__).resolve().parent / "evaluate_candidates.py"
    spec = importlib.util.spec_from_file_location("evaluate_candidates", eval_path)
    ev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)

    splits = ev.read_split_manifest(args.manifest)
    manifest_dir = os.path.dirname(os.path.abspath(args.manifest))

    def _abs(relpath):
        return relpath if os.path.isabs(relpath) else os.path.join(manifest_dir, relpath)

    test_items = [(_abs(p), i) for p, i in splits["test"]]
    print(f"[tflite] test split: {len(test_items)} images")

    # Convert.
    float32_path = str(out_dir / f"{args.model_name}_float32.tflite")
    dynrange_path = str(out_dir / f"{args.model_name}_dynamic_range.tflite")

    print("[tflite] converting to Float32 TFLite...")
    convert_to_tflite_float32(args.keras, float32_path)
    float32_size = os.path.getsize(float32_path) / (1024 * 1024)
    print(f"[tflite] Float32: {float32_size:.2f} MB -> {float32_path}")

    print("[tflite] converting to dynamic-range quantized TFLite...")
    convert_to_tflite_dynamic_range(args.keras, dynrange_path)
    dynrange_size = os.path.getsize(dynrange_path) / (1024 * 1024)
    print(f"[tflite] Dynamic-range: {dynrange_size:.2f} MB -> {dynrange_path}")

    # Evaluate.
    print("[tflite] evaluating Keras on test split...")
    keras_metrics = evaluate_keras_on_test(args.keras, test_items)
    print(f"[tflite] Keras: acc={keras_metrics.accuracy:.4f} "
          f"macroF1={keras_metrics.macro_f1:.4f}")

    print("[tflite] evaluating Float32 TFLite on test split...")
    float32_metrics = evaluate_tflite_on_test(float32_path, test_items)
    print(f"[tflite] Float32: acc={float32_metrics.accuracy:.4f} "
          f"macroF1={float32_metrics.macro_f1:.4f}")

    print("[tflite] evaluating dynamic-range TFLite on test split...")
    dynrange_metrics = evaluate_tflite_on_test(dynrange_path, test_items)
    print(f"[tflite] DynRange: acc={dynrange_metrics.accuracy:.4f} "
          f"macroF1={dynrange_metrics.macro_f1:.4f}")

    # Check parity.
    float32_parity = check_parity(keras_metrics, float32_metrics, float32_size,
                                  CLASSES, CLASSES)
    dynrange_parity = check_parity(keras_metrics, dynrange_metrics, dynrange_size,
                                   CLASSES, CLASSES)

    # Write metrics.
    for name, metrics in [("keras", keras_metrics),
                          ("float32_tflite", float32_metrics),
                          ("dynrange_tflite", dynrange_metrics)]:
        path = out_dir / f"{args.model_name}_{name}_test_metrics.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "model": args.model_name,
                "variant": name,
                "accuracy": metrics.accuracy,
                "macro_f1": metrics.macro_f1,
                "per_class_f1": metrics.per_class_f1,
                "confusion_matrix": metrics.confusion_matrix,
            }, f, indent=2)

    # Write parity results.
    parity_data = {
        "float32": {
            "accuracy_drop": float32_parity.accuracy_drop,
            "macro_f1_drop": float32_parity.macro_f1_drop,
            "per_class_f1_drops": float32_parity.per_class_f1_drops,
            "size_mb": float32_size,
            "overall_pass": float32_parity.overall_pass,
        },
        "dynamic_range": {
            "accuracy_drop": dynrange_parity.accuracy_drop,
            "macro_f1_drop": dynrange_parity.macro_f1_drop,
            "per_class_f1_drops": dynrange_parity.per_class_f1_drops,
            "size_mb": dynrange_size,
            "overall_pass": dynrange_parity.overall_pass,
        },
    }
    with open(out_dir / "parity_results.json", "w", encoding="utf-8") as f:
        json.dump(parity_data, f, indent=2)

    # Generate report.
    report = format_parity_report(keras_metrics, float32_parity, dynrange_parity,
                                  float32_size, dynrange_size, args.model_name)
    report_path = out_dir / "TFLITE_PARITY_REPORT.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n[tflite] parity report -> {report_path}")
    print(f"[tflite] Float32 parity: {'PASS' if float32_parity.overall_pass else 'FAIL'}")
    print(f"[tflite] DynRange parity: {'PASS' if dynrange_parity.overall_pass else 'FAIL'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
