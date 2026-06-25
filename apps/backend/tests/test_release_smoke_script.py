"""Release smoke script must cover backend release-critical checks."""

from pathlib import Path

def test_release_smoke_script_covers_core_backend_checks():
    script = Path(__file__).resolve().parents[1] / "scripts" / "release_smoke.sh"

    text = script.read_text(encoding="utf-8")

    assert "alembic -c alembic.ini upgrade head" in text
    assert "tests/test_contract_examples.py" in text
    assert "tests/test_surface_specific_auth.py" in text
    assert "tests/test_media_object_storage.py" in text
    assert "tests/test_audit_logs.py" in text
    assert "tests/test_minio_media_smoke.py" in text
    assert "tests/test_inference.py" in text
