"""
Core dataset-preparation logic (no I/O side effects beyond reading images).

Responsibilities:
- Canonical class mapping (0=FMD, 1=LSD, 2=healthy) with alias normalization.
- Image discovery for folder-classification AND Roboflow train/valid/test layouts.
- Exact-duplicate detection via SHA-256 file hashing.
- Near-duplicate detection via perceptual hashing (imagehash.phash if available,
  otherwise a deterministic Pillow+numpy aHash fallback).
- Fixed-seed stratified 70/15/15 split with duplicate groups kept together
  (to prevent train/val/test leakage).
- Train-split class-weight computation.

All randomness is seeded so results are reproducible.
"""

from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass, field
from typing import Optional

# ── Canonical class order (REQUIRED): 0=FMD, 1=LSD, 2=healthy ────────────────
CANONICAL_CLASSES: list[str] = ["FMD", "LSD", "healthy"]
CLASS_TO_INDEX: dict[str, int] = {name: i for i, name in enumerate(CANONICAL_CLASSES)}

# Common source-folder naming variants mapped to canonical names.
CLASS_ALIASES: dict[str, str] = {
    # FMD / PMK
    "fmd": "FMD",
    "pmk": "FMD",
    "foot_and_mouth": "FMD",
    "foot-and-mouth": "FMD",
    "penyakit_mulut_dan_kuku": "FMD",
    # LSD / Lato-Lato
    "lsd": "LSD",
    "lato_lato": "LSD",
    "lato-lato": "LSD",
    "latolato": "LSD",
    "lumpy_skin_disease": "LSD",
    "lumpy-skin-disease": "LSD",
    "lumpy": "LSD",
    # Healthy / Sehat
    "healthy": "healthy",
    "sehat": "healthy",
    "normal": "healthy",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# Roboflow multi-label classification export annotation file.
ROBOFLOW_CLASSES_CSV = "_classes.csv"

# Roboflow / standard split folder names that should be flattened, not treated
# as classes. We re-split from scratch regardless of the source split.
SPLIT_FOLDER_NAMES = {"train", "valid", "validation", "val", "test"}

# Default split ratios.
DEFAULT_SPLIT = (0.70, 0.15, 0.15)
DEFAULT_SEED = 42

# Perceptual-hash backend, resolved at import time.
try:  # pragma: no cover - depends on optional dependency
    import imagehash as _imagehash  # type: ignore

    PERCEPTUAL_HASH_BACKEND = "imagehash.phash"
except Exception:  # pragma: no cover
    _imagehash = None
    PERCEPTUAL_HASH_BACKEND = "fallback_ahash"


@dataclass
class ImageRecord:
    """A discovered image and its derived metadata."""

    path: str
    canonical_class: str
    class_index: int
    raw_label: str  # original folder name as found on disk
    file_hash: str = ""
    perceptual_hash: str = ""
    group_id: int = -1  # duplicate-group id (exact + near merged)
    split: str = ""  # train / valid / test

    @property
    def filename(self) -> str:
        return os.path.basename(self.path)


# ── Class normalization ──────────────────────────────────────────────────────

def normalize_class_name(raw: str) -> Optional[str]:
    """Map a raw folder label to a canonical class name, or None if unknown."""
    key = raw.strip().lower().replace(" ", "_")
    if key in CLASS_ALIASES:
        return CLASS_ALIASES[key]
    # Also accept exact canonical names case-insensitively.
    for canonical in CANONICAL_CLASSES:
        if key == canonical.lower():
            return canonical
    return None


# ── Image discovery ──────────────────────────────────────────────────────────

def _is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in IMAGE_EXTENSIONS


def _discover_from_classes_csv(data_dir: str) -> tuple[list[ImageRecord], list[str]]:
    """
    Discover images labeled via Roboflow `_classes.csv` files.

    Each split folder (or the root) may contain a `_classes.csv` with a header
    like `filename,FMD,LSD,healthy` and one-hot rows. Multi-label or no-label
    rows are reported as unknown/skipped.

    Returns (records, unknown_labels). Returns ([], []) if no CSV is found.
    """
    import csv as _csv

    csv_paths: list[str] = []
    for root, _dirs, files in os.walk(data_dir):
        if ROBOFLOW_CLASSES_CSV in files:
            csv_paths.append(os.path.join(root, ROBOFLOW_CLASSES_CSV))

    if not csv_paths:
        return [], []

    records: list[ImageRecord] = []
    unknown: set[str] = set()

    for csv_path in sorted(csv_paths):
        csv_dir = os.path.dirname(csv_path)
        with open(csv_path, encoding="utf-8", newline="") as f:
            reader = _csv.reader(f)
            rows = [r for r in reader if r]
        if not rows:
            continue

        header = [h.strip() for h in rows[0]]
        # First column is the filename; remaining columns are label names.
        label_cols = header[1:]
        # Map each label column to a canonical class (or None if unmappable).
        col_to_canonical = [normalize_class_name(lbl) for lbl in label_cols]

        for row in rows[1:]:
            if not row:
                continue
            fname = row[0].strip()
            values = [v.strip() for v in row[1:]]
            # Find which label columns are "on" (== 1).
            on = [i for i, v in enumerate(values) if v in ("1", "1.0", "true", "True")]
            if len(on) != 1:
                # Multi-label or no-label: cannot assign a single canonical class.
                unknown.add(f"{os.path.basename(csv_dir)}:{fname} (labels={[label_cols[i] for i in on]})")
                continue
            raw_label = label_cols[on[0]]
            canonical = col_to_canonical[on[0]]
            if canonical is None:
                unknown.add(raw_label)
                continue

            img_path = os.path.join(csv_dir, fname)
            if not os.path.isfile(img_path):
                # Annotation references a missing image; record as unknown.
                unknown.add(f"missing_file:{fname}")
                continue

            records.append(
                ImageRecord(
                    path=img_path,
                    canonical_class=canonical,
                    class_index=CLASS_TO_INDEX[canonical],
                    raw_label=raw_label,
                )
            )

    records.sort(key=lambda r: (r.class_index, r.path))
    return records, sorted(unknown)


def discover_images(data_dir: str) -> tuple[list[ImageRecord], list[str]]:
    """
    Walk the dataset directory and return (records, unknown_labels).

    Supports three layouts (and mixtures):
      1. Roboflow classification export: `_classes.csv` (one-hot label columns)
         located in the root or each split folder. Detected first.
      2. Class folders directly:        <data>/FMD/*.jpg
      3. Roboflow split folders:        <data>/train/FMD/*.jpg, <data>/test/...

    For folder layouts, split folder names (train/valid/test) are flattened —
    the source split is intentionally discarded and a fresh fixed-seed split is
    generated later.

    Returns:
      records: list of ImageRecord with canonical class assigned
      unknown_labels: sorted list of labels/files that could not be mapped
    """
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Dataset directory not found: {data_dir}")

    # 1. Prefer Roboflow `_classes.csv` annotation files when present.
    csv_records, csv_unknown = _discover_from_classes_csv(data_dir)
    if csv_records:
        return csv_records, csv_unknown

    # 2/3. Fall back to folder-classification discovery.
    records: list[ImageRecord] = []
    unknown: set[str] = set()

    for root, _dirs, files in os.walk(data_dir):
        image_files = [f for f in files if _is_image(os.path.join(root, f))]
        if not image_files:
            continue

        # The label is the immediate parent folder of the images, unless that
        # folder is a split folder (then there are no class subfolders — skip).
        label_folder = os.path.basename(root.rstrip(os.sep))
        if label_folder.lower() in SPLIT_FOLDER_NAMES:
            # Images sit directly in a split folder with no class subdir — we
            # cannot label these; record as unknown for the validation report.
            unknown.add(label_folder)
            continue

        canonical = normalize_class_name(label_folder)
        if canonical is None:
            unknown.add(label_folder)
            continue

        for fname in sorted(image_files):
            full = os.path.join(root, fname)
            records.append(
                ImageRecord(
                    path=full,
                    canonical_class=canonical,
                    class_index=CLASS_TO_INDEX[canonical],
                    raw_label=label_folder,
                )
            )

    # Stable, deterministic ordering independent of filesystem walk order.
    records.sort(key=lambda r: (r.class_index, r.path))
    return records, sorted(unknown)


# ── Hashing ──────────────────────────────────────────────────────────────────

def compute_file_hash(path: str, chunk_size: int = 65536) -> str:
    """SHA-256 of the raw file bytes (exact-duplicate detection)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _fallback_ahash(path: str, hash_size: int = 8) -> str:
    """
    Deterministic average-hash (aHash) using Pillow + numpy.

    Limitation: aHash is simpler and less robust than DCT-based pHash. It
    reliably catches resized/recompressed copies and minor edits but is more
    sensitive to large crops or strong color shifts than pHash. Used only when
    the optional `imagehash` dependency is unavailable.
    """
    import numpy as np
    from PIL import Image

    with Image.open(path) as im:
        im = im.convert("L").resize((hash_size, hash_size), Image.LANCZOS)
        arr = np.asarray(im, dtype=np.float64)
    avg = arr.mean()
    bits = (arr >= avg).flatten()
    # Pack bits into a hex string for compact, comparable storage.
    value = 0
    for bit in bits:
        value = (value << 1) | int(bool(bit))
    hex_len = (hash_size * hash_size + 3) // 4
    return format(value, f"0{hex_len}x")


def compute_perceptual_hash(path: str, hash_size: int = 8) -> str:
    """
    Perceptual hash hex string. Uses imagehash.phash if available, else the
    deterministic aHash fallback. Both produce comparable hex strings of equal
    length for a given hash_size, enabling Hamming-distance comparison.
    """
    if _imagehash is not None:  # pragma: no cover - optional dependency
        from PIL import Image

        with Image.open(path) as im:
            return str(_imagehash.phash(im, hash_size=hash_size))
    return _fallback_ahash(path, hash_size=hash_size)


def hamming_distance(hex_a: str, hex_b: str) -> int:
    """Bit-level Hamming distance between two equal-length hex hashes."""
    if len(hex_a) != len(hex_b):
        # Pad the shorter one with leading zeros for a defined comparison.
        width = max(len(hex_a), len(hex_b))
        hex_a = hex_a.rjust(width, "0")
        hex_b = hex_b.rjust(width, "0")
    return bin(int(hex_a, 16) ^ int(hex_b, 16)).count("1")


# ── Duplicate grouping ───────────────────────────────────────────────────────

def group_exact_duplicates(records: list[ImageRecord]) -> dict[str, list[ImageRecord]]:
    """
    Compute file hashes and group records by identical hash.
    Mutates each record's file_hash. Returns hash -> [records].
    """
    groups: dict[str, list[ImageRecord]] = {}
    for rec in records:
        if not rec.file_hash:
            rec.file_hash = compute_file_hash(rec.path)
        groups.setdefault(rec.file_hash, []).append(rec)
    return groups


def group_near_duplicates(
    records: list[ImageRecord], threshold: int = 5
) -> None:
    """
    Assign a `group_id` to every record so that exact duplicates AND
    near-duplicates (perceptual Hamming distance <= threshold) share a group.

    Grouping keeps duplicate clusters together in the same split to prevent
    train/val/test leakage. Uses a union-find over records.

    Determinism: records are processed in their existing sorted order, and the
    perceptual hashes are content-derived, so group assignment is reproducible.
    """
    n = len(records)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    # Ensure hashes are populated.
    for rec in records:
        if not rec.file_hash:
            rec.file_hash = compute_file_hash(rec.path)
        if not rec.perceptual_hash:
            rec.perceptual_hash = compute_perceptual_hash(rec.path)

    # 1. Union exact duplicates (identical file hash).
    by_file: dict[str, list[int]] = {}
    for i, rec in enumerate(records):
        by_file.setdefault(rec.file_hash, []).append(i)
    for idxs in by_file.values():
        for j in idxs[1:]:
            union(idxs[0], j)

    # 2. Union near-duplicates by perceptual-hash Hamming distance.
    #    O(n^2) pairwise — acceptable for thesis-scale datasets (<= a few k).
    for i in range(n):
        for j in range(i + 1, n):
            if hamming_distance(records[i].perceptual_hash, records[j].perceptual_hash) <= threshold:
                union(i, j)

    # Assign compact, deterministic group ids.
    root_to_group: dict[int, int] = {}
    next_group = 0
    for i in range(n):
        root = find(i)
        if root not in root_to_group:
            root_to_group[root] = next_group
            next_group += 1
        records[i].group_id = root_to_group[root]


# ── Stratified split ─────────────────────────────────────────────────────────

def _group_representatives(records: list[ImageRecord]) -> dict[int, list[ImageRecord]]:
    groups: dict[int, list[ImageRecord]] = {}
    for rec in records:
        groups.setdefault(rec.group_id, []).append(rec)
    return groups


def stratified_split(
    records: list[ImageRecord],
    ratios: tuple[float, float, float] = DEFAULT_SPLIT,
    seed: int = DEFAULT_SEED,
) -> None:
    """
    Assign each record a split ('train'/'valid'/'test') in-place using a
    fixed-seed stratified split over DUPLICATE GROUPS (not individual images),
    so an entire duplicate cluster lands in exactly one split (no leakage).

    Stratification is per canonical class: groups are bucketed by the class of
    their representative, then split per class by the given ratios.

    Requires group_near_duplicates() to have run first (group_id set).
    """
    assert abs(sum(ratios) - 1.0) < 1e-9, "Split ratios must sum to 1.0"
    train_r, valid_r, _test_r = ratios

    groups = _group_representatives(records)

    # Bucket groups by the class of their representative (first record).
    class_to_groups: dict[str, list[int]] = {c: [] for c in CANONICAL_CLASSES}
    for gid, recs in groups.items():
        cls = recs[0].canonical_class
        class_to_groups[cls].append(gid)

    rng = random.Random(seed)

    for cls in CANONICAL_CLASSES:
        gids = sorted(class_to_groups[cls])  # deterministic base order
        rng.shuffle(gids)
        n = len(gids)
        n_train = int(round(n * train_r))
        n_valid = int(round(n * valid_r))
        # Guard rounding so totals never exceed n; test gets the remainder.
        n_train = min(n_train, n)
        n_valid = min(n_valid, n - n_train)

        for k, gid in enumerate(gids):
            if k < n_train:
                split = "train"
            elif k < n_train + n_valid:
                split = "valid"
            else:
                split = "test"
            for rec in groups[gid]:
                rec.split = split


# ── Class weights ────────────────────────────────────────────────────────────

def compute_class_weights(records: list[ImageRecord]) -> dict[str, float]:
    """
    Compute balanced class weights from the TRAIN split only.

    weight(c) = total_train / (num_classes * count(c))

    Validation/test splits are never oversampled or reweighted.
    """
    train = [r for r in records if r.split == "train"]
    counts = {c: 0 for c in CANONICAL_CLASSES}
    for r in train:
        counts[r.canonical_class] += 1

    total = sum(counts.values())
    num_classes = len(CANONICAL_CLASSES)
    weights: dict[str, float] = {}
    for c in CANONICAL_CLASSES:
        if counts[c] == 0:
            weights[c] = 0.0
        else:
            weights[c] = round(total / (num_classes * counts[c]), 6)
    return weights


def split_counts(records: list[ImageRecord]) -> dict[str, dict[str, int]]:
    """Per-split, per-class support counts. Returns {split: {class: count}}."""
    result: dict[str, dict[str, int]] = {
        s: {c: 0 for c in CANONICAL_CLASSES} for s in ("train", "valid", "test")
    }
    for r in records:
        if r.split in result:
            result[r.split][r.canonical_class] += 1
    return result
