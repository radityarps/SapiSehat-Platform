"""Root-level pytest entrypoint for backend tests.

This keeps `python -m pytest tests -q` useful from the repository root while
the real backend test suite stays under `apps/backend/tests`.
"""

import os
import subprocess
import sys
from pathlib import Path


def test_backend_suite_from_repo_root():
    repo_root = Path(__file__).resolve().parents[1]
    backend_root = repo_root / "apps" / "backend"
    env = os.environ.copy()
    env.setdefault("FASTAPI_ENV", "test")
    env.setdefault("RATE_LIMIT_MAX_REQUESTS", "1000")
    existing_opts = env.get("PYTEST_ADDOPTS", "")
    if "no:cacheprovider" not in existing_opts:
        env["PYTEST_ADDOPTS"] = f"{existing_opts} -p no:cacheprovider".strip()

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q"],
        cwd=backend_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
