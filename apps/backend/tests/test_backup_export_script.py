"""Backup/export script contract."""

from pathlib import Path


def test_backup_export_script_exists_and_mentions_database_dump():
    script = Path(__file__).resolve().parents[1] / "scripts" / "backup_export.sh"
    text = script.read_text(encoding="utf-8")

    assert "pg_dump" in text or "sqlite3" in text
    assert "DATABASE_URL" in text
    assert "backup" in text.lower()
