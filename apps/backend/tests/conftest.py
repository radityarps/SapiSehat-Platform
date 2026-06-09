"""Backend test helpers."""

import os
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", f"sqlite:////tmp/sapisehat_backend_tests_{os.getpid()}.db")

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


def repo_file(relative_path: str) -> Path:
    """Return repo-root file path or skip in backend-only package/image."""
    path = REPO_ROOT / relative_path
    if not path.exists() and relative_path.startswith("apps/backend/"):
        path = BACKEND_ROOT / relative_path.removeprefix("apps/backend/")
    if not path.exists():
        pytest.skip(f"repo fixture not present in backend-only workspace: {relative_path}")
    return path


def repo_text(relative_path: str) -> str:
    return repo_file(relative_path).read_text(encoding="utf-8")
