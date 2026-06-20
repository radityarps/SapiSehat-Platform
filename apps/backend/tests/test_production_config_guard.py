"""Production config must fail fast on unsafe defaults."""

import os
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = TESTS_DIR.parent
REPO_ROOT = BACKEND_ROOT.parent.parent

def run_config_import(extra_env):
    env = os.environ.copy()
    env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-c", "import config"],
        cwd=BACKEND_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

def test_production_rejects_default_jwt_secret():
    result = run_config_import({"FASTAPI_ENV": "production", "CORS_ORIGINS": "https://agency.sapisehat.test"})

    assert result.returncode != 0
    assert "JWT_SECRET must be set" in result.stderr

def test_production_rejects_default_s3_credentials():
    result = run_config_import(
        {
            "FASTAPI_ENV": "production",
            "CORS_ORIGINS": "https://agency.sapisehat.test",
            "JWT_SECRET": "x" * 40,
        }
    )

    assert result.returncode != 0
    assert "S3_ACCESS_KEY_ID must be set" in result.stderr

def test_production_accepts_strong_required_config():
    result = run_config_import(
        {
            "FASTAPI_ENV": "production",
            "CORS_ORIGINS": "https://agency.sapisehat.test",
            "JWT_SECRET": "x" * 40,
            "S3_ACCESS_KEY_ID": "prod-access-key",
            "S3_SECRET_ACCESS_KEY": "prod-secret-key",
            "S3_BUCKET": "prod-sapisehat-scan-images",
        }
    )

    assert result.returncode == 0, result.stderr
