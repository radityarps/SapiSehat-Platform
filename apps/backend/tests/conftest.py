"""Backend test helpers."""

import os
from pathlib import Path

import pytest

os.environ.setdefault(
    "DATABASE_URL", f"sqlite:////tmp/sapisehat_backend_tests_{os.getpid()}.db"
)

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = TESTS_DIR.parent


def _resolve_repo_root() -> Path:
    candidates = [
        TESTS_DIR.parents[2] if len(TESTS_DIR.parents) > 2 else BACKEND_ROOT,
        BACKEND_ROOT,
        TESTS_DIR.parents[1] if len(TESTS_DIR.parents) > 1 else BACKEND_ROOT,
    ]
    for candidate in candidates:
        if (candidate / "apps" / "backend").exists():
            return candidate
    return BACKEND_ROOT


REPO_ROOT = _resolve_repo_root()

# Model-dependent test files require ML artifacts not present in CI or
# backend-only deployments. Skip collection entirely when the sentinel
# model directory is absent so pytest exits cleanly.
_MODEL_DIR = BACKEND_ROOT / "model"
_MODEL_ARTIFACTS_PRESENT = _MODEL_DIR.exists() and any(_MODEL_DIR.iterdir())

# These tests import repository documentation modules by relative path. The
# backend Docker image intentionally contains only apps/backend, so skip them
# there instead of failing during collection.
_REPOSITORY_DOC_TESTS = [
    "test_yolo_symptom_detector.py",
    "test_field_baseline_evaluation.py",
    "test_model_selection.py",
    "test_tflite_parity.py",
    "test_training_wrapper.py",
    "test_two_stage_fusion_evaluator.py",
]

collect_ignore: list[str] = [
    str(TESTS_DIR / name)
    for name in _REPOSITORY_DOC_TESTS
    if not (REPO_ROOT / "docs" / "team-1-image" / "model").is_dir()
]
if not _MODEL_ARTIFACTS_PRESENT:
    collect_ignore.extend(
        str(TESTS_DIR / name)
        for name in (
            "test_model_metadata.py",
            "test_model_selection.py",
            "test_tflite_parity.py",
            "test_training_wrapper.py",
            "test_two_stage_fusion_evaluator.py",
        )
        if str(TESTS_DIR / name) not in collect_ignore
    )


def repo_file(relative_path: str) -> Path:
    """Return repo-root file path or skip in backend-only package/image."""
    path = REPO_ROOT / relative_path
    if not path.exists() and relative_path.startswith("apps/backend/"):
        path = BACKEND_ROOT / relative_path.removeprefix("apps/backend/")
    if not path.exists():
        pytest.skip(
            f"repo fixture not present in backend-only workspace: {relative_path}"
        )
    return path


def repo_text(relative_path: str) -> str:
    return repo_file(relative_path).read_text(encoding="utf-8")
