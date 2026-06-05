"""
Tests for the training wrapper (issue #19).

These are DRY-RUN tests: they verify wrapper argument handling, version-string
pattern, runtime-metadata generation, bundle manifest, and the versioned zip —
WITHOUT requiring a GPU, TensorFlow, or the real dataset.

The wrapper module lives at docs/model/training_wrapper.py; we import it by path.
"""

import importlib.util
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

# Locate docs/model/training_wrapper.py relative to the repo root.
THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[3]  # apps/backend/tests -> repo root
WRAPPER_PATH = REPO_ROOT / "docs" / "model" / "training_wrapper.py"
EVAL_PATH = REPO_ROOT / "docs" / "model" / "evaluate_candidates.py"


def _load_wrapper():
    spec = importlib.util.spec_from_file_location("training_wrapper", WRAPPER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _load_eval():
    spec = importlib.util.spec_from_file_location("evaluate_candidates", EVAL_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


# Manifest column order produced by issue #18 dataset_prep.
MANIFEST_HEADER = [
    "filename", "relpath", "canonical_class", "class_index",
    "raw_label", "split", "group_id", "file_hash", "perceptual_hash",
]


def _write_fixture_manifest(manifest_path: Path, *, rows=None,
                            with_prep_artifacts=True):
    """
    Write a tiny synthetic split_manifest.csv (no real images) plus, optionally,
    the sibling issue #18 dataset-prep artifacts so the wrapper can bundle them.
    """
    if rows is None:
        # Minimal but valid: every split + every class present.
        rows = [
            ("a.jpg", "FMD", 0, "train"),
            ("b.jpg", "LSD", 1, "train"),
            ("c.jpg", "healthy", 2, "train"),
            ("d.jpg", "FMD", 0, "valid"),
            ("e.jpg", "LSD", 1, "valid"),
            ("f.jpg", "healthy", 2, "valid"),
            ("g.jpg", "FMD", 0, "test"),
            ("h.jpg", "LSD", 1, "test"),
            ("i.jpg", "healthy", 2, "test"),
        ]
    with open(manifest_path, "w", encoding="utf-8", newline="") as f:
        import csv as _csv
        w = _csv.writer(f)
        w.writerow(MANIFEST_HEADER)
        for fname, cls, idx, split in rows:
            w.writerow([fname, fname, cls, idx, cls, split,
                        "grp", "deadbeef", "0" * 16])
    if with_prep_artifacts:
        d = manifest_path.parent
        (d / "DATASET_SPLIT_REPORT.md").write_text(
            "# FIXTURE/DEMO split report\n", encoding="utf-8")
        (d / "LABEL_VALIDATION.md").write_text(
            "# FIXTURE/DEMO label validation\n", encoding="utf-8")
        (d / "class_indices.json").write_text(
            '{"FMD":0,"LSD":1,"healthy":2}', encoding="utf-8")
        (d / "class_weights.json").write_text('{"0":1.0,"1":1.0,"2":1.0}',
                                              encoding="utf-8")


class TestTrainingWrapper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrap = _load_wrapper()

    # ── version string ────────────────────────────────────────────────

    def test_version_pattern(self):
        v = self.wrap.make_version("mobilenetv2", 42,
                                    date=datetime(2026, 6, 1, tzinfo=timezone.utc))
        self.assertEqual(v, "cattle-disease-mobilenetv2-v20260601-s42")

    def test_version_pattern_regex(self):
        v = self.wrap.make_version("densenet121", 7)
        self.assertRegex(
            v, r"^cattle-disease-densenet121-v\d{8}-s7$"
        )

    # ── argument validation ───────────────────────────────────────────

    def test_requires_data_when_not_dry_run(self):
        rc = self.wrap.run(["--architecture", "mobilenetv2", "--out", "x"])
        self.assertEqual(rc, 2)

    def test_missing_data_dir_errors(self):
        rc = self.wrap.run([
            "--data", "/no/such/dataset/path",
            "--architecture", "mobilenetv2", "--out", "x",
        ])
        self.assertEqual(rc, 2)

    def test_invalid_architecture_rejected(self):
        with self.assertRaises(SystemExit):
            self.wrap.run(["--dry-run", "--architecture", "resnet999", "--out", "x"])

    # ── dry run end-to-end ─────────────────────────────────────────────

    def test_dry_run_produces_metadata_manifest_and_bundle(self):
        with TemporaryDirectory() as out:
            rc = self.wrap.run([
                "--dry-run",
                "--architecture", "mobilenetv2",
                "--seed", "42",
                "--epochs", "50",
                "--out", out,
            ])
            self.assertEqual(rc, 0)

            meta = Path(out) / "runtime_metadata.json"
            manifest = Path(out) / "bundle_manifest.json"
            self.assertTrue(meta.exists())
            self.assertTrue(manifest.exists())

            # Exactly one versioned bundle zip.
            zips = list(Path(out).glob("model_training_artifacts_*.zip"))
            self.assertEqual(len(zips), 1)
            self.assertRegex(
                zips[0].name,
                r"^model_training_artifacts_cattle-disease-mobilenetv2-v\d{8}-s42\.zip$",
            )

    def test_runtime_metadata_fields(self):
        with TemporaryDirectory() as out:
            self.wrap.run(["--dry-run", "--architecture", "densenet121",
                           "--seed", "7", "--out", out])
            meta = json.loads((Path(out) / "runtime_metadata.json").read_text())
            for key in (
                "model_version", "architecture", "seed", "epochs",
                "training_date", "platform", "python_version",
                "tensorflow_version", "dataset", "dry_run",
            ):
                self.assertIn(key, meta)
            self.assertEqual(meta["architecture"], "densenet121")
            self.assertEqual(meta["seed"], 7)
            self.assertTrue(meta["dry_run"])
            # Date parses as ISO 8601.
            datetime.fromisoformat(meta["training_date"])

    def test_bundle_manifest_lists_artifacts(self):
        with TemporaryDirectory() as out:
            self.wrap.run(["--dry-run", "--architecture", "mobilenetv2",
                           "--seed", "42", "--out", out])
            manifest = json.loads((Path(out) / "bundle_manifest.json").read_text())
            self.assertIn("model_version", manifest)
            self.assertIn("artifacts", manifest)
            self.assertIn("artifact_count", manifest)
            self.assertEqual(manifest["artifact_count"], len(manifest["artifacts"]))
            # Runtime metadata is always bundled.
            self.assertIn("runtime_metadata.json", manifest["artifacts"])

    def test_bundle_zip_contains_manifest_and_metadata(self):
        with TemporaryDirectory() as out:
            self.wrap.run(["--dry-run", "--architecture", "mobilenetv2",
                           "--seed", "42", "--out", out])
            zip_path = next(Path(out).glob("model_training_artifacts_*.zip"))
            with zipfile.ZipFile(zip_path) as zf:
                names = zf.namelist()
            self.assertIn("runtime_metadata.json", names)
            self.assertIn("bundle_manifest.json", names)
            # The zip must not contain itself.
            self.assertFalse(any(n.endswith(".zip") for n in names))

    def test_dry_run_bundles_preexisting_artifacts(self):
        """If repo-script artifacts already exist in out_dir, they are bundled."""
        with TemporaryDirectory() as out:
            outp = Path(out)
            outp.mkdir(exist_ok=True)
            # Simulate artifacts the repo script would have produced.
            (outp / "mobilenetv2_metrics.json").write_text('{"model":"mobilenetv2"}')
            (outp / "preprocessing.json").write_text('{"rescale":"1/255"}')
            (outp / "comparison_summary.json").write_text("{}")

            self.wrap.run(["--dry-run", "--architecture", "mobilenetv2",
                           "--seed", "42", "--out", out])

            zip_path = next(outp.glob("model_training_artifacts_*.zip"))
            with zipfile.ZipFile(zip_path) as zf:
                names = set(zf.namelist())
            self.assertIn("mobilenetv2_metrics.json", names)
            self.assertIn("preprocessing.json", names)
            self.assertIn("comparison_summary.json", names)

    # ── platform/tf detection are non-crashing ─────────────────────────

    def test_detect_platform_returns_known_value(self):
        self.assertIn(self.wrap.detect_platform(), ("kaggle", "colab", "local"))

    def test_eval_script_path_exists(self):
        self.assertTrue(self.wrap.EVAL_SCRIPT.exists(),
                        "source-of-truth evaluate_candidates.py must exist")


class TestWrapperManifestMode(unittest.TestCase):
    """Issue #19 integration: prove the wrapper uses the prepared 70/15/15 split."""

    @classmethod
    def setUpClass(cls):
        cls.wrap = _load_wrapper()

    def test_manifest_and_data_mutually_exclusive(self):
        with TemporaryDirectory() as out:
            mpath = Path(out) / "split_manifest.csv"
            _write_fixture_manifest(mpath)
            rc = self.wrap.run([
                "--dry-run", "--manifest", str(mpath),
                "--data", out, "--out", out,
            ])
            self.assertEqual(rc, 2)

    def test_missing_manifest_file_errors(self):
        with TemporaryDirectory() as out:
            rc = self.wrap.run([
                "--dry-run", "--manifest",
                str(Path(out) / "does_not_exist.csv"), "--out", out,
            ])
            self.assertEqual(rc, 2)

    def test_dry_run_manifest_bundles_dataset_prep_artifacts(self):
        """The prepared-split path bundles the #18 artifacts (not Roboflow folders)."""
        with TemporaryDirectory() as out:
            prep_dir = Path(out) / "dataset_artifacts"
            prep_dir.mkdir()
            mpath = prep_dir / "split_manifest.csv"
            _write_fixture_manifest(mpath)

            run_out = Path(out) / "run_out"
            rc = self.wrap.run([
                "--dry-run", "--architecture", "mobilenetv2",
                "--seed", "42", "--manifest", str(mpath),
                "--out", str(run_out),
            ])
            self.assertEqual(rc, 0)

            zip_path = next(run_out.glob("model_training_artifacts_*.zip"))
            with zipfile.ZipFile(zip_path) as zf:
                names = set(zf.namelist())
            # Required prepared-split artifacts present in the bundle.
            self.assertIn("split_manifest.csv", names)
            self.assertIn("DATASET_SPLIT_REPORT.md", names)
            self.assertIn("LABEL_VALIDATION.md", names)
            self.assertIn("runtime_metadata.json", names)
            self.assertIn("bundle_manifest.json", names)

    def test_manifest_mode_metadata_marks_prepared_split(self):
        with TemporaryDirectory() as out:
            prep_dir = Path(out) / "dataset_artifacts"
            prep_dir.mkdir()
            mpath = prep_dir / "split_manifest.csv"
            _write_fixture_manifest(mpath)

            run_out = Path(out) / "run_out"
            self.wrap.run([
                "--dry-run", "--manifest", str(mpath), "--out", str(run_out),
            ])
            meta = json.loads((run_out / "runtime_metadata.json").read_text())
            self.assertEqual(meta["data_source_mode"], "prepared_split_manifest")
            self.assertEqual(meta["split_manifest"], str(mpath))

    def test_run_training_command_passes_manifest(self):
        """run_training must invoke the eval script with --manifest, not --data."""
        captured = {}

        class _FakeArgs:
            manifest = "/some/split_manifest.csv"
            data = None
            epochs = 1
            seed = 42
            architecture = "mobilenetv2"

        import subprocess as _sp
        orig = _sp.run

        def _fake_run(cmd, *a, **k):
            captured["cmd"] = cmd

            class _R:
                returncode = 0
            return _R()

        _sp.run = _fake_run
        try:
            with TemporaryDirectory() as out:
                rc = self.wrap.run_training(_FakeArgs(), Path(out))
        finally:
            _sp.run = orig
        self.assertEqual(rc, 0)
        self.assertIn("--manifest", captured["cmd"])
        self.assertIn("/some/split_manifest.csv", captured["cmd"])
        self.assertNotIn("--data", captured["cmd"])


class TestEvalManifestReader(unittest.TestCase):
    """TF-free unit tests for evaluate_candidates.read_split_manifest (issue #19)."""

    @classmethod
    def setUpClass(cls):
        cls.ev = _load_eval()

    def test_reads_valid_manifest(self):
        with TemporaryDirectory() as out:
            mpath = Path(out) / "split_manifest.csv"
            _write_fixture_manifest(mpath, with_prep_artifacts=False)
            splits = self.ev.read_split_manifest(str(mpath))
            self.assertEqual(len(splits["train"]), 3)
            self.assertEqual(len(splits["valid"]), 3)
            self.assertEqual(len(splits["test"]), 3)
            # canonical mapping 0=FMD,1=LSD,2=healthy preserved.
            classes = {idx for _p, idx in splits["train"]}
            self.assertEqual(classes, {0, 1, 2})

    def test_split_counts_helper(self):
        with TemporaryDirectory() as out:
            mpath = Path(out) / "split_manifest.csv"
            _write_fixture_manifest(mpath, with_prep_artifacts=False)
            splits = self.ev.read_split_manifest(str(mpath))
            counts = self.ev.manifest_split_counts(splits)
            self.assertEqual(counts["train"], {"FMD": 1, "LSD": 1, "healthy": 1})

    def test_missing_columns_raise(self):
        with TemporaryDirectory() as out:
            mpath = Path(out) / "bad.csv"
            with open(mpath, "w", encoding="utf-8", newline="") as f:
                f.write("filename,split\n")
                f.write("a.jpg,train\n")
            with self.assertRaises(ValueError):
                self.ev.read_split_manifest(str(mpath))

    def test_class_index_mismatch_raises(self):
        with TemporaryDirectory() as out:
            mpath = Path(out) / "split_manifest.csv"
            # FMD wrongly mapped to index 2 (canonical is 0).
            rows = [
                ("a.jpg", "FMD", 2, "train"),
                ("b.jpg", "LSD", 1, "train"),
                ("c.jpg", "healthy", 2, "train"),
                ("d.jpg", "FMD", 0, "valid"),
                ("e.jpg", "LSD", 1, "test"),
            ]
            _write_fixture_manifest(mpath, rows=rows, with_prep_artifacts=False)
            with self.assertRaises(ValueError):
                self.ev.read_split_manifest(str(mpath))

    def test_missing_split_raises(self):
        with TemporaryDirectory() as out:
            mpath = Path(out) / "split_manifest.csv"
            # No 'test' rows.
            rows = [
                ("a.jpg", "FMD", 0, "train"),
                ("b.jpg", "LSD", 1, "valid"),
            ]
            _write_fixture_manifest(mpath, rows=rows, with_prep_artifacts=False)
            with self.assertRaises(ValueError):
                self.ev.read_split_manifest(str(mpath))

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.ev.read_split_manifest("/no/such/manifest.csv")


class TestEvalProtocolHelpers(unittest.TestCase):
    """TF-free tests for the issue #17/#20 training-protocol helpers."""

    @classmethod
    def setUpClass(cls):
        cls.ev = _load_eval()

    def test_canonical_class_order(self):
        self.assertEqual(self.ev.CLASSES, ["FMD", "LSD", "healthy"])
        self.assertEqual(self.ev.CLASS_TO_INDEX,
                         {"FMD": 0, "LSD": 1, "healthy": 2})

    def test_batch_size_defaults(self):
        self.assertEqual(self.ev.resolve_batch_size("mobilenetv2"), 32)
        self.assertEqual(self.ev.resolve_batch_size("custom_cnn"), 32)
        # DenseNet121 falls back to 16 by default (memory).
        self.assertEqual(self.ev.resolve_batch_size("densenet121"), 16)

    def test_batch_size_override_wins(self):
        self.assertEqual(self.ev.resolve_batch_size("densenet121", 8), 8)
        self.assertEqual(self.ev.resolve_batch_size("mobilenetv2", 64), 64)

    def test_supports_fine_tuning(self):
        # Transfer-learning models support two-phase fine-tuning.
        self.assertTrue(self.ev.supports_fine_tuning("mobilenetv2"))
        self.assertTrue(self.ev.supports_fine_tuning("densenet121"))
        # Custom CNN is from-scratch: no pretrained base to fine-tune.
        self.assertFalse(self.ev.supports_fine_tuning("custom_cnn"))

    def test_augmentation_is_lesion_preserving(self):
        pol = self.ev.augmentation_policy()
        # Mild geometric / photometric only.
        self.assertEqual(pol["rotation_max_deg"], 15)
        self.assertEqual(pol["zoom_max"], 0.10)
        self.assertTrue(pol["horizontal_flip"])
        # Disease-cue-destroying transforms are excluded.
        self.assertFalse(pol["vertical_flip"])
        for bad in ("vertical_flip", "heavy_blur", "aggressive_crop",
                    "extreme_color_shift"):
            self.assertIn(bad, pol["excluded"])
        # Returned dict is a copy (mutation does not leak).
        pol["rotation_max_deg"] = 999
        self.assertEqual(self.ev.augmentation_policy()["rotation_max_deg"], 15)

    def test_protocol_constants(self):
        self.assertEqual(self.ev.EARLY_STOPPING_PATIENCE, 8)
        self.assertEqual(self.ev.REDUCE_LR_PATIENCE, 4)
        self.assertEqual(self.ev.REDUCE_LR_FACTOR, 0.2)
        self.assertEqual(self.ev.PHASE1_LR, 0.001)
        self.assertLess(self.ev.FINE_TUNE_LR, self.ev.PHASE1_LR)

    def test_verify_manifest_paths_ok_for_real_files(self):
        with TemporaryDirectory() as out:
            p1 = Path(out) / "a.txt"
            p2 = Path(out) / "b.txt"
            p1.write_text("x")
            p2.write_text("y")
            # Should not raise: paths exist in this runtime.
            self.ev.verify_manifest_paths([(str(p1), 0), (str(p2), 1)])

    def test_verify_manifest_paths_raises_for_foreign_paths(self):
        # Simulate a Windows-generated manifest used on a runtime that can't
        # see those paths.
        items = [
            (r"D:\Files\Documents\Kuliah\Dataset\img1.jpg", 0),
            (r"D:\Files\Documents\Kuliah\Dataset\img2.jpg", 1),
        ]
        with self.assertRaises(FileNotFoundError):
            self.ev.verify_manifest_paths(items)


if __name__ == "__main__":
    unittest.main()
