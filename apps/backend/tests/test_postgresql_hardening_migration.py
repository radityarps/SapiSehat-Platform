from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = BACKEND_ROOT / "alembic/versions/0018_postgresql_hardening.py"
DOC = BACKEND_ROOT / "docs/postgresql-hardening.md"


def test_hardening_migration_declares_constraints_and_indexes():
    text = MIGRATION.read_text()
    required = [
        "ck_accounts_type",
        "ck_cattle_sex",
        "ck_cattle_status",
        "ck_detection_confidence_range",
        "ck_fusion_confidence_range",
        "ck_follow_up_status",
        "uq_cattle_farmer_tag",
        "fk_detection_farmer",
        "fk_fusion_cattle",
        "ix_dashboard_fusion_farmer_created",
        "ix_cluster_risk_jurisdiction_disease",
    ]
    for token in required:
        assert token in text


def test_migration_discipline_seed_and_backup_are_documented():
    text = DOC.read_text()
    assert "alembic -c alembic.ini upgrade head" in text
    assert "Deterministic agency seed flow" in text
    assert "pg_dump" in text
    assert "pg_restore" in text


def test_sqlalchemy_models_expose_hardening_metadata():
    from api.database import Base
    from api import db_models  # noqa: F401

    tables = Base.metadata.tables
    cattle_constraints = {c.name for c in tables["cattle_profiles"].constraints}
    fusion_constraints = {c.name for c in tables["fusion_results"].constraints}
    detection_constraints = {c.name for c in tables["detection_events"].constraints}
    indexes = {
        idx.name
        for table in tables.values()
        for idx in table.indexes
    }

    assert "uq_cattle_farmer_tag" in cattle_constraints
    assert "ck_cattle_sex" in cattle_constraints
    assert "ck_detection_confidence_range" in detection_constraints
    assert "ck_fusion_confidence_range" in fusion_constraints
    assert "ix_dashboard_fusion_farmer_created" in indexes
    assert "ix_cluster_risk_jurisdiction_disease" in indexes


def test_sqlalchemy_models_define_foreign_keys_for_core_records():
    from api.database import Base
    from api import db_models  # noqa: F401

    tables = Base.metadata.tables
    fk_targets = {
        fk.column.table.name
        for fk in tables["fusion_results"].foreign_keys
    }
    assert {"farmer_accounts", "cattle_profiles"}.issubset(fk_targets)
    assert {
        fk.column.table.name for fk in tables["detection_events"].foreign_keys
    } == {"farmer_accounts", "cattle_profiles"}
