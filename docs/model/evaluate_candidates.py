"""
Model Candidate Evaluation Script (issues #13 / #19).

Trains and evaluates candidate architectures on the cattle disease dataset
(FMD / LSD / healthy) and produces a consistent set of metrics for the formal
comparison report:

  - Custom CNN baseline (trained from scratch)
  - MobileNetV2 (transfer learning, ImageNet)
  - DenseNet121 (transfer learning, ImageNet)

Data source (two modes)
-----------------------
1. PREPARED SPLIT (recommended, issue #18 integration):
       python evaluate_candidates.py --manifest /path/split_manifest.csv ...
   Uses the approved fixed-seed stratified 70/15/15 split:
     - train split  -> model training (shuffled with the fixed seed)
     - valid split  -> validation / early stopping
     - test  split  -> FINAL reported metrics
   This avoids the raw Roboflow train/valid folders entirely.

2. FOLDER FALLBACK (legacy):
       python evaluate_candidates.py --data /path/to/dataset ...
   Uses <data>/train and <data>/valid folders. Final metrics are computed on
   the valid folder. Prefer the manifest mode so the documented split is used.

For each model it records: accuracy, per-class precision/recall/F1, macro F1,
confusion matrix (JSON + PNG), parameter count, and on-disk model size.

Note
----
Full training requires a GPU and the real dataset (run on Kaggle/Colab). This
script never fabricates metrics.
"""

import argparse
import csv
import json
import os
from pathlib import Path


CLASSES = ["FMD", "LSD", "healthy"]
CLASS_TO_INDEX = {c: i for i, c in enumerate(CLASSES)}
NUM_CLASSES = len(CLASSES)
INPUT_SIZE = (224, 224)

# Early-stopping / LR-schedule protocol (issue #17/#19).
EARLY_STOPPING_PATIENCE = 8
REDUCE_LR_PATIENCE = 4
REDUCE_LR_FACTOR = 0.2

# Batch-size protocol (issue #17): 32 default; DenseNet121 falls back to 16 if
# memory requires it.
DEFAULT_BATCH_SIZE = 32
DENSENET_BATCH_SIZE = 16

# Two-phase transfer-learning protocol (issue #17): phase 1 trains the
# classification head with a frozen ImageNet base; phase 2 (optional) unfreezes
# the top layers of the base and fine-tunes with a low learning rate.
PHASE1_LR = 0.001
FINE_TUNE_LR = 1e-5
DEFAULT_FINE_TUNE_EPOCHS = 10
# How many of the base model's top layers to unfreeze during phase 2.
FINE_TUNE_UNFREEZE_LAYERS = 30

# Mild, lesion-preserving augmentation (issue #17). TRAINING ONLY — validation
# and test stay deterministic. No vertical flip / heavy blur / aggressive crop /
# extreme color shift (these can destroy disease cues).
AUGMENTATION_POLICY = {
    "rotation_max_deg": 15,
    "zoom_max": 0.10,
    "brightness_max_delta": 0.10,
    "contrast_range": [0.9, 1.1],
    "horizontal_flip": True,
    "vertical_flip": False,
    "excluded": ["vertical_flip", "heavy_blur", "aggressive_crop",
                 "extreme_color_shift"],
    "applies_to": "train split only",
}


def augmentation_policy() -> dict:
    """Return the documented training-only augmentation policy (TF-free)."""
    return dict(AUGMENTATION_POLICY)


def resolve_batch_size(architecture: str, requested: int | None = None) -> int:
    """
    Resolve the training batch size for an architecture (TF-free).

    Explicit --batch-size always wins. Otherwise DenseNet121 defaults to 16
    (heavier model / memory), everything else to 32.
    """
    if requested:
        return requested
    if architecture == "densenet121":
        return DENSENET_BATCH_SIZE
    return DEFAULT_BATCH_SIZE


def supports_fine_tuning(architecture: str) -> bool:
    """Custom CNN is trained from scratch, so two-phase fine-tuning is N/A."""
    return architecture in ("mobilenetv2", "densenet121")


def build_custom_cnn(num_classes: int):
    """A small CNN baseline trained from scratch. Returns (model, base=None)."""
    from tensorflow.keras import layers, models

    model = models.Sequential([
        layers.Input(shape=(*INPUT_SIZE, 3)),
        layers.Conv2D(32, 3, activation="relu", padding="same"),
        layers.MaxPooling2D(),
        layers.Conv2D(64, 3, activation="relu", padding="same"),
        layers.MaxPooling2D(),
        layers.Conv2D(128, 3, activation="relu", padding="same"),
        layers.MaxPooling2D(),
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation="softmax"),
    ], name="custom_cnn")
    return model, None


def build_mobilenetv2(num_classes: int):
    """MobileNetV2 transfer learning. Returns (model, base) for fine-tuning."""
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras import layers, models

    base = MobileNetV2(weights="imagenet", include_top=False,
                       input_shape=(*INPUT_SIZE, 3))
    base.trainable = False
    x = base.output
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    out = layers.Dense(num_classes, activation="softmax")(x)
    return models.Model(inputs=base.input, outputs=out, name="mobilenetv2"), base


def build_densenet121(num_classes: int):
    """DenseNet121 transfer learning. Returns (model, base) for fine-tuning."""
    from tensorflow.keras.applications import DenseNet121
    from tensorflow.keras import layers, models

    base = DenseNet121(weights="imagenet", include_top=False,
                       input_shape=(*INPUT_SIZE, 3))
    base.trainable = False
    x = base.output
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    out = layers.Dense(num_classes, activation="softmax")(x)
    return models.Model(inputs=base.input, outputs=out, name="densenet121"), base


BUILDERS = {
    "custom_cnn": build_custom_cnn,
    "mobilenetv2": build_mobilenetv2,
    "densenet121": build_densenet121,
}


# ── Prepared-split (issue #18) manifest loading ──────────────────────────────

def read_split_manifest(manifest_path: str) -> dict[str, list[tuple[str, int]]]:
    """
    Read the issue #18 split_manifest.csv and return:
        {"train": [(relpath, class_index), ...], "valid": [...], "test": [...]}

    The manifest is the source of truth for the fixed-seed 70/15/15 split.
    Pure function (no TensorFlow) so it is unit-testable without a GPU.

    Raises ValueError if required columns/splits are missing or a class index
    does not match the canonical order.
    """
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(f"Split manifest not found: {manifest_path}")

    required_cols = {"relpath", "class_index", "split", "canonical_class"}
    splits: dict[str, list[tuple[str, int]]] = {"train": [], "valid": [], "test": []}

    with open(manifest_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = required_cols - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Manifest missing required columns: {sorted(missing)}"
            )
        for row in reader:
            split = row["split"].strip()
            if split not in splits:
                continue
            relpath = row["relpath"]
            cls = row["canonical_class"].strip()
            idx = int(row["class_index"])
            # Enforce canonical mapping consistency.
            if cls in CLASS_TO_INDEX and CLASS_TO_INDEX[cls] != idx:
                raise ValueError(
                    f"Class index mismatch for {cls}: manifest={idx}, "
                    f"canonical={CLASS_TO_INDEX[cls]}"
                )
            splits[split].append((relpath, idx))

    for s in ("train", "valid", "test"):
        if not splits[s]:
            raise ValueError(f"Manifest has no rows for the '{s}' split")
    return splits


def manifest_split_counts(splits: dict[str, list[tuple[str, int]]]) -> dict:
    """Per-split, per-class counts for logging/run_config (TF-free)."""
    out: dict[str, dict[str, int]] = {}
    for split, items in splits.items():
        counts = {c: 0 for c in CLASSES}
        for _relpath, idx in items:
            counts[CLASSES[idx]] += 1
        out[split] = counts
    return out


def verify_manifest_paths(items: list[tuple[str, int]], *, sample: int = 25) -> None:
    """
    Preflight check (TF-free): confirm the manifest's image paths are readable
    from THIS runtime before training starts.

    The issue #18 manifest stores absolute paths captured when the split was
    generated. If a manifest produced on one machine (e.g. Windows
    ``D:\\...``) is used on another (e.g. Kaggle ``/kaggle/input/...``) the
    paths will not resolve. Rather than fail deep inside tf.data with an opaque
    error, fail fast with actionable guidance.

    Checks up to ``sample`` evenly-spaced paths. Raises FileNotFoundError if any
    are missing.
    """
    if not items:
        return
    n = len(items)
    step = max(1, n // sample)
    missing: list[str] = []
    for i in range(0, n, step):
        p = items[i][0]
        if not os.path.isfile(p):
            missing.append(p)
    if missing:
        example = missing[0]
        raise FileNotFoundError(
            f"{len(missing)} sampled image path(s) from the split manifest are "
            f"not readable in this environment.\n"
            f"  example missing path: {example}\n"
            "The manifest stores absolute paths from where the split was "
            "generated. If you generated it on another machine (e.g. Windows) "
            "and are now on Kaggle/Colab, REGENERATE the split inside this "
            "runtime so the paths point at the local dataset:\n"
            "    python -m dataset_prep.cli --data <dataset_dir_here> "
            "--out <out_dir_here>\n"
            "then pass the freshly generated split_manifest.csv via --manifest."
        )


def _augment_image(img, seed_pair):
    """
    Mild, lesion-preserving augmentation (issue #17), TRAINING ONLY.
    Uses stateless ops seeded per-sample for reproducibility.
    """
    import tensorflow as tf

    s = seed_pair
    # Horizontal flip only (no vertical flip — would distort lesion layout).
    img = tf.image.stateless_random_flip_left_right(img, seed=s)
    # Mild brightness / contrast.
    img = tf.image.stateless_random_brightness(
        img, max_delta=AUGMENTATION_POLICY["brightness_max_delta"], seed=s)
    img = tf.image.stateless_random_contrast(
        img, AUGMENTATION_POLICY["contrast_range"][0],
        AUGMENTATION_POLICY["contrast_range"][1], seed=s)
    img = tf.clip_by_value(img, 0.0, 1.0)
    return img


def make_manifest_dataset(items: list[tuple[str, int]], seed: int, *,
                          training: bool, batch_size: int = DEFAULT_BATCH_SIZE,
                          augment: bool = False):
    """
    Build a tf.data.Dataset from manifest (relpath, class_index) pairs.

    - Images decoded, resized to INPUT_SIZE, rescaled to 1/255 (matches the
      documented inference preprocessing).
    - Labels one-hot encoded in canonical order.
    - Training set is shuffled with the FIXED seed; valid/test are NOT shuffled.
    - When ``augment`` is True (training only), mild lesion-preserving
      augmentation is applied. Validation/test stay deterministic.
    """
    import tensorflow as tf  # local import: tests don't need TF

    paths = [p for p, _ in items]
    labels = [i for _, i in items]

    def _load(path, label):
        data = tf.io.read_file(path)
        img = tf.image.decode_image(data, channels=3, expand_animations=False)
        img = tf.image.resize(img, INPUT_SIZE)
        img = tf.cast(img, tf.float32) / 255.0
        onehot = tf.one_hot(label, NUM_CLASSES)
        return img, onehot

    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if training:
        ds = ds.shuffle(buffer_size=len(paths), seed=seed,
                        reshuffle_each_iteration=True)
    ds = ds.map(_load, num_parallel_calls=tf.data.AUTOTUNE)
    if training and augment:
        # Deterministic per-element seeds derived from the fixed seed.
        counter = tf.data.experimental.Counter()
        ds = tf.data.Dataset.zip((ds, counter))
        ds = ds.map(
            lambda xy, c: (_augment_image(xy[0], tf.stack([seed, c])), xy[1]),
            num_parallel_calls=tf.data.AUTOTUNE,
        )
    ds = ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return ds


def make_generators(data_dir: str, batch_size: int = DEFAULT_BATCH_SIZE,
                    augment: bool = True):
    """
    Folder-fallback generators. Training uses mild lesion-preserving
    augmentation (issue #17); validation stays deterministic (rescale only).
    """
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    train_dir = os.path.join(data_dir, "train")
    valid_dir = os.path.join(data_dir, "valid")

    if augment:
        train_datagen = ImageDataGenerator(
            rescale=1.0 / 255,
            rotation_range=AUGMENTATION_POLICY["rotation_max_deg"],
            zoom_range=AUGMENTATION_POLICY["zoom_max"],
            brightness_range=[0.9, 1.1],
            horizontal_flip=AUGMENTATION_POLICY["horizontal_flip"],
            vertical_flip=AUGMENTATION_POLICY["vertical_flip"],
            fill_mode="nearest",
        )
    else:
        train_datagen = ImageDataGenerator(rescale=1.0 / 255)

    valid_datagen = ImageDataGenerator(rescale=1.0 / 255)
    train_gen = train_datagen.flow_from_directory(
        train_dir, target_size=INPUT_SIZE, batch_size=batch_size,
        class_mode="categorical",
    )
    valid_gen = valid_datagen.flow_from_directory(
        valid_dir, target_size=INPUT_SIZE, batch_size=batch_size,
        class_mode="categorical", shuffle=False,
    )
    return train_gen, valid_gen


def _write_metrics(name: str, y_true, y_pred, model, out_dir: Path,
                   *, split_name: str):
    """Compute + persist metrics from true/pred label arrays."""
    import numpy as np  # noqa: F401
    from sklearn.metrics import classification_report, confusion_matrix

    report = classification_report(
        y_true, y_pred, target_names=CLASSES,
        labels=list(range(NUM_CLASSES)), output_dict=True, zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=list(range(NUM_CLASSES))).tolist()

    params = model.count_params()
    tmp_path = out_dir / f"{name}.keras"
    model.save(tmp_path)
    size_mb = round(os.path.getsize(tmp_path) / (1024 * 1024), 2)

    metrics = {
        "model": name,
        "evaluated_on_split": split_name,
        "accuracy": report.get("accuracy"),
        "macro_avg": report.get("macro avg"),
        "weighted_avg": report.get("weighted avg"),
        "per_class": {c: report[c] for c in CLASSES if c in report},
        "confusion_matrix": cm,
        "class_order": CLASSES,
        "params": int(params),
        "keras_size_mb": size_mb,
    }

    out_json = out_dir / f"{name}_metrics.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"[{name}] split={split_name} "
          f"accuracy={metrics['accuracy']:.4f} "
          f"macroF1={report['macro avg']['f1-score']:.4f} "
          f"params={params} size={size_mb}MB -> {out_json}")

    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        from sklearn.metrics import confusion_matrix as _cm
        plt.figure(figsize=(8, 6))
        sns.heatmap(_cm(y_true, y_pred, labels=list(range(NUM_CLASSES))),
                    annot=True, fmt="d", cmap="Blues",
                    xticklabels=CLASSES, yticklabels=CLASSES)
        plt.title(f"Confusion Matrix - {name} ({split_name})")
        plt.ylabel("True")
        plt.xlabel("Predicted")
        plt.tight_layout()
        plt.savefig(out_dir / f"{name}_confusion_matrix.png", dpi=120)
        plt.close()
    except Exception as e:  # pragma: no cover - optional plotting
        print(f"[{name}] confusion matrix PNG skipped: {e}")

    return metrics


def evaluate_model(name: str, model, valid_gen, out_dir: Path):
    """Folder-fallback evaluation (legacy): metrics on the valid generator."""
    import numpy as np

    y_true = valid_gen.classes
    y_pred = np.argmax(model.predict(valid_gen, verbose=1), axis=1)
    return _write_metrics(name, y_true, y_pred, model, out_dir, split_name="valid")


def evaluate_model_on_dataset(name: str, model, test_ds, out_dir: Path):
    """Manifest mode: FINAL metrics on the held-out TEST split."""
    import numpy as np

    y_true, y_pred = [], []
    for batch_imgs, batch_labels in test_ds:
        probs = model.predict(batch_imgs, verbose=0)
        y_pred.extend(np.argmax(probs, axis=1).tolist())
        y_true.extend(np.argmax(batch_labels.numpy(), axis=1).tolist())
    return _write_metrics(name, y_true, y_pred, model, out_dir, split_name="test")


def train_candidate(name, model, base, train_data, valid_data, *,
                    epochs, fine_tune_epochs, class_weight=None,
                    do_fine_tune=True):
    """
    Train one candidate under the approved protocol (issue #17):

      Phase 1 — frozen pretrained base (if any), train the classifier head.
      Phase 2 — (transfer-learning models only, optional) unfreeze the top
                FINE_TUNE_UNFREEZE_LAYERS of the base and fine-tune at a low
                learning rate, continuing early stopping / LR reduction.

    Custom CNN has no pretrained base, so only phase 1 runs (full network).
    Returns the training history list.
    """
    import tensorflow as tf

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=EARLY_STOPPING_PATIENCE,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", patience=REDUCE_LR_PATIENCE,
            factor=REDUCE_LR_FACTOR,
        ),
    ]

    # ── Phase 1: train classification head (base frozen if present) ──────
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=PHASE1_LR),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    print(f"[{name}] phase 1: training head (base frozen={base is not None})")
    h1 = model.fit(train_data, epochs=epochs, validation_data=valid_data,
                   callbacks=callbacks, class_weight=class_weight)
    histories = [("phase1", h1.history)]

    # ── Phase 2: optional fine-tuning of the top base layers ─────────────
    if base is not None and do_fine_tune and fine_tune_epochs > 0:
        base.trainable = True
        # Only unfreeze the TOP layers; keep the rest frozen.
        for layer in base.layers[:-FINE_TUNE_UNFREEZE_LAYERS]:
            layer.trainable = False
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=FINE_TUNE_LR),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )
        print(f"[{name}] phase 2: fine-tuning top "
              f"{FINE_TUNE_UNFREEZE_LAYERS} base layers (lr={FINE_TUNE_LR})")
        h2 = model.fit(train_data, epochs=fine_tune_epochs,
                       validation_data=valid_data, callbacks=callbacks,
                       class_weight=class_weight)
        histories.append(("phase2_fine_tune", h2.history))

    return histories


def main():
    parser = argparse.ArgumentParser(description="Evaluate model candidates")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--manifest",
                     help="Path to issue #18 split_manifest.csv (PREFERRED: uses "
                     "the approved fixed-seed 70/15/15 split).")
    src.add_argument("--data",
                     help="Dataset dir with train/ and valid/ subfolders "
                     "(legacy fallback; uses raw source split).")
    parser.add_argument("--epochs", type=int, default=50,
                        help="Max epochs for phase 1 (default: 50)")
    parser.add_argument("--fine-tune-epochs", type=int,
                        default=DEFAULT_FINE_TUNE_EPOCHS,
                        help="Max epochs for phase-2 fine-tuning of transfer "
                        f"models (default: {DEFAULT_FINE_TUNE_EPOCHS}; 0 disables).")
    parser.add_argument("--no-fine-tune", action="store_true",
                        help="Skip phase-2 fine-tuning (phase 1 only).")
    parser.add_argument("--batch-size", type=int, default=None,
                        help="Override batch size (default: 32; DenseNet121: 16).")
    parser.add_argument("--no-augment", action="store_true",
                        help="Disable training augmentation (deterministic).")
    parser.add_argument("--no-class-weight", action="store_true",
                        help="Disable train-split class weighting.")
    parser.add_argument("--seed", type=int, default=42,
                        help="Fixed random seed for reproducibility (default: 42)")
    parser.add_argument("--out", default="results",
                        help="Output directory for metrics/artifacts")
    parser.add_argument("--models", nargs="+",
                        default=list(BUILDERS.keys()),
                        choices=list(BUILDERS.keys()),
                        help="Which candidates to train/evaluate")
    args = parser.parse_args()

    import random
    import numpy as np
    import tensorflow as tf

    # Fixed-seed training for reproducibility (issue #17/#19 protocol).
    random.seed(args.seed)
    np.random.seed(args.seed)
    tf.keras.utils.set_random_seed(args.seed)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Deterministic inference preprocessing config — must match backend & mobile.
    preprocessing = {
        "input_size": list(INPUT_SIZE),
        "channels": 3,
        "color_mode": "RGB",
        "rescale": "1/255",
        "exif_orientation_correction": "before resize where available",
        "note": "Inference preprocessing only; training augmentation is separate.",
    }
    with open(out_dir / "preprocessing.json", "w", encoding="utf-8") as f:
        json.dump(preprocessing, f, indent=2)

    use_manifest = args.manifest is not None

    run_config = {
        "data_source_mode": "prepared_split_manifest" if use_manifest else "source_folders",
        "manifest": args.manifest,
        "data": args.data,
        "epochs": args.epochs,
        "fine_tune_epochs": 0 if args.no_fine_tune else args.fine_tune_epochs,
        "seed": args.seed,
        "models": args.models,
        "classes": CLASSES,
        "class_indices": CLASS_TO_INDEX,
        "optimizer": "Adam",
        "phase1_learning_rate": PHASE1_LR,
        "fine_tune_learning_rate": FINE_TUNE_LR,
        "fine_tune_unfreeze_layers": FINE_TUNE_UNFREEZE_LAYERS,
        "loss": "categorical_crossentropy",
        "early_stopping_patience": EARLY_STOPPING_PATIENCE,
        "reduce_lr_patience": REDUCE_LR_PATIENCE,
        "reduce_lr_factor": REDUCE_LR_FACTOR,
        "augmentation": None if args.no_augment else augmentation_policy(),
        "class_weighting": not args.no_class_weight,
        "two_phase_transfer_learning": not args.no_fine_tune,
        "batch_sizes": {m: resolve_batch_size(m, args.batch_size) for m in args.models},
    }

    if use_manifest:
        splits = read_split_manifest(args.manifest)
        manifest_dir = os.path.dirname(os.path.abspath(args.manifest))

        def _abs(relpath: str) -> str:
            return relpath if os.path.isabs(relpath) else os.path.join(manifest_dir, relpath)

        train_items = [(_abs(p), i) for p, i in splits["train"]]
        valid_items = [(_abs(p), i) for p, i in splits["valid"]]
        test_items = [(_abs(p), i) for p, i in splits["test"]]

        counts = manifest_split_counts(splits)
        run_config["split_counts"] = counts

        # Train-split class weights (issue #17): balance imbalanced classes.
        class_weight = None
        if not args.no_class_weight:
            train_counts = counts["train"]
            total = sum(train_counts.values())
            class_weight = {}
            for idx, c in enumerate(CLASSES):
                n = train_counts.get(c, 0)
                class_weight[idx] = (total / (NUM_CLASSES * n)) if n else 0.0
            run_config["class_weights_by_index"] = class_weight

        with open(out_dir / "run_config.json", "w", encoding="utf-8") as f:
            json.dump(run_config, f, indent=2)

        print(f"[eval] Using PREPARED split manifest: {args.manifest}")
        print(f"[eval] train={len(train_items)} valid={len(valid_items)} "
              f"test={len(test_items)} (seed={args.seed})")

        # Fail fast if the manifest's absolute image paths are not readable here
        # (e.g. a Windows-generated manifest used on Kaggle). See #20 review.
        verify_manifest_paths(train_items + valid_items + test_items)

        all_metrics = {}
        for name in args.models:
            bs = resolve_batch_size(name, args.batch_size)
            print(f"\n=== Training {name} (seed={args.seed}, batch={bs}) ===")
            train_ds = make_manifest_dataset(
                train_items, args.seed, training=True, batch_size=bs,
                augment=not args.no_augment)
            valid_ds = make_manifest_dataset(
                valid_items, args.seed, training=False, batch_size=bs)
            test_ds = make_manifest_dataset(
                test_items, args.seed, training=False, batch_size=bs)

            model, base = BUILDERS[name](NUM_CLASSES)
            train_candidate(
                name, model, base, train_ds, valid_ds,
                epochs=args.epochs,
                fine_tune_epochs=0 if args.no_fine_tune else args.fine_tune_epochs,
                class_weight=class_weight,
                do_fine_tune=not args.no_fine_tune,
            )
            # FINAL metrics on the held-out TEST split.
            all_metrics[name] = evaluate_model_on_dataset(name, model, test_ds, out_dir)
    else:
        print(f"[eval] FALLBACK: using source folders under {args.data} "
              "(prefer --manifest for the documented 70/15/15 split).")

        all_metrics = {}
        for name in args.models:
            bs = resolve_batch_size(name, args.batch_size)
            print(f"\n=== Training {name} (seed={args.seed}, batch={bs}) ===")
            train_gen, valid_gen = make_generators(
                args.data, batch_size=bs, augment=not args.no_augment)

            # Train-split class weights from the generator's class counts.
            class_weight = None
            if not args.no_class_weight:
                import numpy as np
                classes_arr = train_gen.classes
                total = len(classes_arr)
                class_weight = {}
                for idx in range(NUM_CLASSES):
                    n = int(np.sum(classes_arr == idx))
                    class_weight[idx] = (total / (NUM_CLASSES * n)) if n else 0.0

            with open(out_dir / "run_config.json", "w", encoding="utf-8") as f:
                run_config["class_weights_by_index"] = class_weight
                json.dump(run_config, f, indent=2)

            model, base = BUILDERS[name](NUM_CLASSES)
            train_candidate(
                name, model, base, train_gen, valid_gen,
                epochs=args.epochs,
                fine_tune_epochs=0 if args.no_fine_tune else args.fine_tune_epochs,
                class_weight=class_weight,
                do_fine_tune=not args.no_fine_tune,
            )
            all_metrics[name] = evaluate_model(name, model, valid_gen, out_dir)

    summary_path = out_dir / "comparison_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\nComparison summary written to {summary_path}")
    print("Paste these numbers into docs/model/MODEL_EVALUATION_REPORT.md")


if __name__ == "__main__":
    main()
