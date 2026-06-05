"""
Tests for the dataset-preparation package (issue #18).

The real Roboflow dataset is NOT present in the repo and must not be committed.
These tests build tiny synthetic fixture images at runtime in a temp dir, so
they are fully self-contained and never touch real training data.

Coverage:
- canonical class mapping (0=FMD, 1=LSD, 2=healthy) + alias normalization
- discovery for direct class folders AND Roboflow train/valid/test layout
- exact-duplicate detection by file hash
- near-duplicate grouping keeps clusters together
- fixed-seed stratified 70/15/15 split reproducibility
- no train/valid/test overlap (by group and by file hash)
- train-only class weights; valid/test not oversampled
- required artifact generation + fixture marking
- CLI fails clearly when --data is missing
"""

import csv
import json
import os
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory

from PIL import Image

# Make the backend root importable when tests run from repo root.
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from dataset_prep import (  # noqa: E402
    CANONICAL_CLASSES,
    normalize_class_name,
    discover_images,
    group_exact_duplicates,
    group_near_duplicates,
    stratified_split,
    compute_class_weights,
)
from dataset_prep import artifacts  # noqa: E402


# ── Fixture helpers ──────────────────────────────────────────────────────────

def _make_patterned_image(path: str, seed: int, size=(16, 16)) -> None:
    """
    Create a deterministic, spatially-varied image whose perceptual hash is
    unique per `seed`. Solid-color images are intentionally avoided: a uniform
    image yields a degenerate average-hash (all bits identical), which would
    make every image look like a near-duplicate.
    """
    import numpy as np

    os.makedirs(os.path.dirname(path), exist_ok=True)
    rng = np.random.RandomState(seed)
    arr = rng.randint(0, 256, size=(size[1], size[0], 3), dtype=np.uint8)
    Image.fromarray(arr, mode="RGB").save(path, format="PNG")


def _build_class_folder_fixture(root: str, per_class: int = 12) -> None:
    """Create <root>/FMD, <root>/LSD, <root>/healthy with distinct images."""
    counter = 0
    for cls in ("FMD", "LSD", "healthy"):
        for k in range(per_class):
            counter += 1
            _make_patterned_image(
                os.path.join(root, cls, f"{cls}_{k}.png"),
                seed=counter,
            )


def _build_roboflow_fixture(root: str, per_class: int = 10) -> None:
    """Create <root>/{train,valid,test}/{FMD,LSD,healthy}/ with aliases too."""
    counter = 0
    layout = {
        "train": ("pmk", "lato_lato", "sehat"),  # use aliases to test mapping
        "valid": ("FMD", "LSD", "healthy"),
        "test": ("FMD", "LSD", "healthy"),
    }
    for split, classes in layout.items():
        for cls in classes:
            for k in range(per_class):
                counter += 1
                _make_patterned_image(
                    os.path.join(root, split, cls, f"{split}_{cls}_{k}.png"),
                    seed=counter,
                )


def _build_roboflow_csv_fixture(root: str, per_class: int = 6) -> None:
    """
    Create a Roboflow classification-export fixture: split folders with images
    directly inside and a `_classes.csv` (one-hot header filename,FMD,LSD,healthy).
    Uses one alias header to verify normalization is applied to CSV columns too.
    """
    import csv as _csv

    counter = 0
    for split in ("train", "valid", "test"):
        split_dir = os.path.join(root, split)
        os.makedirs(split_dir, exist_ok=True)
        rows = [["filename", "FMD", "LSD", "healthy"]]
        for cls_idx, cls in enumerate(("FMD", "LSD", "healthy")):
            for k in range(per_class):
                counter += 1
                fname = f"{split}_{cls}_{k}.png"
                _make_patterned_image(os.path.join(split_dir, fname), seed=counter)
                onehot = ["0", "0", "0"]
                onehot[cls_idx] = "1"
                rows.append([fname] + onehot)
        with open(os.path.join(split_dir, "_classes.csv"), "w",
                  encoding="utf-8", newline="") as f:
            _csv.writer(f).writerows(rows)


# ── Class mapping ────────────────────────────────────────────────────────────

class TestClassMapping(unittest.TestCase):
    def test_canonical_order(self):
        self.assertEqual(CANONICAL_CLASSES, ["FMD", "LSD", "healthy"])

    def test_aliases_map_to_canonical(self):
        self.assertEqual(normalize_class_name("PMK"), "FMD")
        self.assertEqual(normalize_class_name("pmk"), "FMD")
        self.assertEqual(normalize_class_name("Lato-Lato"), "LSD")
        self.assertEqual(normalize_class_name("lumpy_skin_disease"), "LSD")
        self.assertEqual(normalize_class_name("Sehat"), "healthy")
        self.assertEqual(normalize_class_name("healthy"), "healthy")

    def test_unknown_label_returns_none(self):
        self.assertIsNone(normalize_class_name("dog"))


# ── Discovery ────────────────────────────────────────────────────────────────

class TestDiscovery(unittest.TestCase):
    def test_discovers_direct_class_folders(self):
        with TemporaryDirectory() as d:
            _build_class_folder_fixture(d, per_class=5)
            records, unknown = discover_images(d)
            self.assertEqual(len(records), 15)
            self.assertEqual(unknown, [])
            # Class indices follow canonical order.
            for r in records:
                if r.canonical_class == "FMD":
                    self.assertEqual(r.class_index, 0)
                elif r.canonical_class == "LSD":
                    self.assertEqual(r.class_index, 1)
                else:
                    self.assertEqual(r.class_index, 2)

    def test_discovers_roboflow_layout_with_aliases(self):
        with TemporaryDirectory() as d:
            _build_roboflow_fixture(d, per_class=4)
            records, unknown = discover_images(d)
            # 3 splits * 3 classes * 4 = 36, all mapped via aliases/canonical.
            self.assertEqual(len(records), 36)
            self.assertEqual(unknown, [])

    def test_unmapped_folder_reported(self):
        with TemporaryDirectory() as d:
            _build_class_folder_fixture(d, per_class=3)
            _make_patterned_image(os.path.join(d, "dog", "dog_0.png"), seed=999)
            records, unknown = discover_images(d)
            self.assertIn("dog", unknown)
            self.assertTrue(all(r.canonical_class in CANONICAL_CLASSES for r in records))

    def test_missing_directory_raises(self):
        with self.assertRaises(FileNotFoundError):
            discover_images("/path/that/does/not/exist/xyz123")

    def test_discovers_roboflow_classes_csv(self):
        with TemporaryDirectory() as d:
            _build_roboflow_csv_fixture(d, per_class=6)
            records, unknown = discover_images(d)
            # 3 splits * 3 classes * 6 = 54 single-label rows.
            self.assertEqual(len(records), 54)
            self.assertEqual(unknown, [])
            # Canonical indices respected.
            by_class = {c: 0 for c in CANONICAL_CLASSES}
            for r in records:
                by_class[r.canonical_class] += 1
            self.assertEqual(by_class["FMD"], 18)
            self.assertEqual(by_class["LSD"], 18)
            self.assertEqual(by_class["healthy"], 18)

    def test_classes_csv_flags_multilabel_rows(self):
        import csv as _csv
        with TemporaryDirectory() as d:
            split_dir = os.path.join(d, "train")
            os.makedirs(split_dir, exist_ok=True)
            _make_patterned_image(os.path.join(split_dir, "a.png"), seed=1)
            _make_patterned_image(os.path.join(split_dir, "b.png"), seed=2)
            with open(os.path.join(split_dir, "_classes.csv"), "w",
                      encoding="utf-8", newline="") as f:
                w = _csv.writer(f)
                w.writerow(["filename", "FMD", "LSD", "healthy"])
                w.writerow(["a.png", "1", "0", "0"])   # valid single-label
                w.writerow(["b.png", "1", "1", "0"])   # multi-label -> unknown
            records, unknown = discover_images(d)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].canonical_class, "FMD")
            self.assertTrue(any("b.png" in u for u in unknown))


# ── Duplicate detection ──────────────────────────────────────────────────────

class TestDuplicates(unittest.TestCase):
    def test_exact_duplicates_detected_by_hash(self):
        with TemporaryDirectory() as d:
            _build_class_folder_fixture(d, per_class=4)
            # Create an exact byte-copy of one FMD image.
            src = os.path.join(d, "FMD", "FMD_0.png")
            dup = os.path.join(d, "FMD", "FMD_0_copy.png")
            with open(src, "rb") as f:
                data = f.read()
            with open(dup, "wb") as f:
                f.write(data)

            records, _ = discover_images(d)
            groups = group_exact_duplicates(records)
            # The src + dup share one hash bucket of size 2.
            sizes = sorted(len(v) for v in groups.values())
            self.assertEqual(sizes[-1], 2)

    def test_near_duplicates_share_group(self):
        with TemporaryDirectory() as d:
            _build_class_folder_fixture(d, per_class=4)
            # Near-dup: same pixels re-saved as a different file (byte content
            # differs slightly via re-encode, but perceptual hash matches).
            src = os.path.join(d, "LSD", "LSD_0.png")
            near = os.path.join(d, "LSD", "LSD_0_near.png")
            with Image.open(src) as im:
                # Re-save with optimization so file bytes differ from src.
                im.convert("RGB").save(near, format="PNG", optimize=True)

            records, _ = discover_images(d)
            group_near_duplicates(records, threshold=5)
            # src and near should land in the same group_id.
            gid = {r.filename: r.group_id for r in records}
            self.assertEqual(gid["LSD_0.png"], gid["LSD_0_near.png"])


# ── Split ────────────────────────────────────────────────────────────────────

class TestSplit(unittest.TestCase):
    def _prepare(self, d, per_class=20, seed=42):
        _build_class_folder_fixture(d, per_class=per_class)
        records, _ = discover_images(d)
        group_exact_duplicates(records)
        group_near_duplicates(records, threshold=0)  # strict: only exact dups group
        stratified_split(records, ratios=(0.70, 0.15, 0.15), seed=seed)
        return records

    def test_split_assigns_all_three_splits(self):
        with TemporaryDirectory() as d:
            records = self._prepare(d)
            splits = {r.split for r in records}
            self.assertEqual(splits, {"train", "valid", "test"})

    def test_split_is_reproducible_with_same_seed(self):
        with TemporaryDirectory() as d:
            recs1 = self._prepare(d, seed=42)
            assign1 = {r.path: r.split for r in recs1}
        with TemporaryDirectory() as d2:
            recs2 = self._prepare(d2, seed=42)
            assign2 = {os.path.basename(r.path): r.split for r in recs2}
        # Compare by basename since temp dirs differ.
        norm1 = {os.path.basename(p): s for p, s in assign1.items()}
        self.assertEqual(norm1, assign2)

    def test_different_seed_changes_assignment(self):
        with TemporaryDirectory() as d:
            recs1 = self._prepare(d, seed=1)
            a1 = {os.path.basename(r.path): r.split for r in recs1}
        with TemporaryDirectory() as d2:
            recs2 = self._prepare(d2, seed=2)
            a2 = {os.path.basename(r.path): r.split for r in recs2}
        self.assertNotEqual(a1, a2)

    def test_no_overlap_between_splits_by_group(self):
        with TemporaryDirectory() as d:
            records = self._prepare(d)
            group_to_splits: dict[int, set] = {}
            for r in records:
                group_to_splits.setdefault(r.group_id, set()).add(r.split)
            # Every duplicate group must live in exactly one split.
            for gid, splits in group_to_splits.items():
                self.assertEqual(len(splits), 1, f"group {gid} leaked across {splits}")

    def test_approx_70_15_15_ratio(self):
        with TemporaryDirectory() as d:
            records = self._prepare(d, per_class=20)
            counts = {"train": 0, "valid": 0, "test": 0}
            for r in records:
                counts[r.split] += 1
            total = len(records)
            # 60 images: expect ~42/9/9. Allow tolerance for rounding per class.
            self.assertAlmostEqual(counts["train"] / total, 0.70, delta=0.08)
            self.assertAlmostEqual(counts["valid"] / total, 0.15, delta=0.08)
            self.assertAlmostEqual(counts["test"] / total, 0.15, delta=0.08)


# ── Class weights ────────────────────────────────────────────────────────────

class TestClassWeights(unittest.TestCase):
    def test_weights_computed_from_train_only(self):
        with TemporaryDirectory() as d:
            _build_class_folder_fixture(d, per_class=20)
            records, _ = discover_images(d)
            group_exact_duplicates(records)
            group_near_duplicates(records, threshold=0)
            stratified_split(records, seed=42)
            weights = compute_class_weights(records)
            # All canonical classes present and weights positive.
            for c in CANONICAL_CLASSES:
                self.assertIn(c, weights)
                self.assertGreater(weights[c], 0.0)

    def test_balanced_classes_have_equal_weights(self):
        with TemporaryDirectory() as d:
            _build_class_folder_fixture(d, per_class=20)
            records, _ = discover_images(d)
            group_exact_duplicates(records)
            group_near_duplicates(records, threshold=0)
            stratified_split(records, seed=42)
            weights = compute_class_weights(records)
            # With equal per-class counts, weights should be ~equal.
            vals = list(weights.values())
            self.assertAlmostEqual(max(vals), min(vals), delta=0.5)


# ── Artifacts ────────────────────────────────────────────────────────────────

class TestArtifacts(unittest.TestCase):
    def _run_pipeline(self, d, out):
        _build_class_folder_fixture(d, per_class=12)
        records, unknown = discover_images(d)
        group_exact_duplicates(records)
        group_near_duplicates(records, threshold=0)
        stratified_split(records, seed=42)
        return artifacts.generate_all(
            out,
            records,
            data_dir=d,
            seed=42,
            ratios=(0.70, 0.15, 0.15),
            near_dup_threshold=0,
            unknown_labels=unknown,
            expert_audit=False,
            is_fixture=True,
        )

    def test_all_required_artifacts_generated(self):
        with TemporaryDirectory() as d, TemporaryDirectory() as out:
            written = self._run_pipeline(d, out)
            for name in (
                "class_indices.json",
                "split_manifest.csv",
                "class_weights.json",
                "DATASET_SPLIT_REPORT.md",
                "LABEL_VALIDATION.md",
            ):
                self.assertIn(name, written)
                self.assertTrue(os.path.exists(written[name]), f"{name} missing")

    def test_class_indices_canonical_order(self):
        with TemporaryDirectory() as d, TemporaryDirectory() as out:
            written = self._run_pipeline(d, out)
            with open(written["class_indices.json"], encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["index_to_class"]["0"], "FMD")
            self.assertEqual(data["index_to_class"]["1"], "LSD")
            self.assertEqual(data["index_to_class"]["2"], "healthy")
            self.assertEqual(data["canonical_order"], ["FMD", "LSD", "healthy"])

    def test_manifest_has_all_records_and_splits(self):
        with TemporaryDirectory() as d, TemporaryDirectory() as out:
            written = self._run_pipeline(d, out)
            with open(written["split_manifest.csv"], encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 36)  # 3 classes * 12
            self.assertTrue(all(r["split"] in ("train", "valid", "test") for r in rows))
            self.assertTrue(all(r["class_index"] in ("0", "1", "2") for r in rows))

    def test_reports_marked_as_fixture(self):
        with TemporaryDirectory() as d, TemporaryDirectory() as out:
            written = self._run_pipeline(d, out)
            with open(written["DATASET_SPLIT_REPORT.md"], encoding="utf-8") as f:
                report = f.read()
            self.assertIn("FIXTURE", report.upper())
            self.assertIn("NOT REAL TRAINING DATA", report.upper())

    def test_label_validation_documents_missing_expert_audit(self):
        with TemporaryDirectory() as d, TemporaryDirectory() as out:
            written = self._run_pipeline(d, out)
            with open(written["LABEL_VALIDATION.md"], encoding="utf-8") as f:
                content = f.read()
            self.assertIn("NO EXPERT AUDIT", content.upper())
            self.assertIn("LIMITATION", content.upper())


# ── CLI ──────────────────────────────────────────────────────────────────────

class TestCli(unittest.TestCase):
    def test_cli_fails_clearly_on_missing_data(self):
        result = subprocess.run(
            [sys.executable, "-m", "dataset_prep.cli", "--data",
             "/no/such/dir/xyz", "--out", "ignored"],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", (result.stderr + result.stdout).lower())

    def test_cli_end_to_end_on_fixture(self):
        with TemporaryDirectory() as d, TemporaryDirectory() as out:
            _build_class_folder_fixture(d, per_class=8)
            result = subprocess.run(
                [sys.executable, "-m", "dataset_prep.cli",
                 "--data", d, "--out", out, "--fixture"],
                cwd=BACKEND_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(os.path.exists(os.path.join(out, "split_manifest.csv")))
            self.assertTrue(os.path.exists(os.path.join(out, "DATASET_SPLIT_REPORT.md")))


if __name__ == "__main__":
    unittest.main()
