"""postgresql hardening constraints and dashboard indexes

Revision ID: 0018_postgresql_hardening
Revises: 0017_farmer_preferences_archive
Create Date: 2026-06-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0018_postgresql_hardening"
down_revision = "0017_farmer_preferences_archive"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Bring older Alembic chain up to current ORM shape before constraints.
    op.add_column("accounts", sa.Column("address", sa.String(length=300), nullable=True))
    op.add_column("farmer_accounts", sa.Column("address", sa.String(length=300), nullable=True))
    op.add_column("agency_jurisdictions", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("agency_jurisdictions", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("cattle_profiles", sa.Column("name", sa.String(length=120), nullable=True))
    op.add_column("cattle_profiles", sa.Column("color", sa.String(length=80), nullable=True))
    op.add_column("cattle_profiles", sa.Column("weight_kg", sa.Float(), nullable=True))
    op.add_column("cattle_profiles", sa.Column("reproductive_status", sa.String(length=40), nullable=True))
    op.add_column("cattle_profiles", sa.Column("is_pregnant", sa.Boolean(), nullable=True))
    op.add_column("cattle_profiles", sa.Column("last_calving_date", sa.String(length=40), nullable=True))
    op.add_column("cattle_profiles", sa.Column("last_vaccination_date", sa.String(length=40), nullable=True))
    op.add_column("cattle_profiles", sa.Column("last_deworming_date", sa.String(length=40), nullable=True))
    op.add_column("cattle_profiles", sa.Column("health_notes", sa.String(length=1000), nullable=True))
    op.add_column("cattle_profiles", sa.Column("purchase_date", sa.String(length=40), nullable=True))
    op.add_column("cattle_profiles", sa.Column("purchase_price_idr", sa.Integer(), nullable=True))
    op.add_column("cattle_profiles", sa.Column("notes", sa.String(length=1000), nullable=True))

    # PostgreSQL-first hardening. Existing dev SQLite creates remain model-driven.
    op.create_check_constraint("ck_accounts_type", "accounts", "account_type IN ('farmer', 'agency', 'admin')")
    op.create_check_constraint("ck_accounts_email_not_blank", "accounts", "length(trim(email)) > 3")
    op.create_check_constraint("ck_farmer_accounts_consent_state", "farmer_accounts", "consent_state IN ('private', 'agency_monitoring', 'research_and_monitoring')")
    op.create_check_constraint("ck_agency_jurisdictions_level", "agency_jurisdictions", "level IN ('province', 'regency_city', 'district_subdistrict', 'village')")
    op.create_unique_constraint("uq_agency_jurisdictions_parent_level_name", "agency_jurisdictions", ["parent_id", "level", "name"])
    op.create_check_constraint("ck_agency_users_role", "agency_users", "role IN ('admin', 'province_officer', 'district_officer', 'village_officer', 'viewer')")

    op.create_unique_constraint("uq_cattle_farmer_tag", "cattle_profiles", ["farmer_id", "tag"])
    op.create_check_constraint("ck_cattle_sex", "cattle_profiles", "sex IN ('female', 'male', 'unknown')")
    op.create_check_constraint("ck_cattle_status", "cattle_profiles", "status IN ('active', 'sold', 'dead', 'lost', 'archived')")
    op.create_check_constraint("ck_cattle_age_nonnegative", "cattle_profiles", "age_months IS NULL OR age_months >= 0")

    op.create_check_constraint("ck_detection_confidence_range", "detection_events", "confidence >= 0 AND confidence <= 1")
    op.create_check_constraint("ck_detection_result_label", "detection_events", "result_label IN ('healthy', 'FMD', 'LSD', 'needs_review')")
    op.create_check_constraint("ck_detection_source", "detection_events", "source IN ('quick_scan', 'mobile', 'api', 'offline_sync', 'seed')")

    op.create_unique_constraint("uq_stored_media_checksum", "stored_media", ["checksum"])
    op.create_check_constraint("ck_stored_media_byte_size", "stored_media", "byte_size >= 0")
    op.create_check_constraint("ck_stored_media_content_type", "stored_media", "content_type LIKE 'image/%'")

    op.create_check_constraint("ck_fusion_confidence_range", "fusion_results", "confidence >= 0 AND confidence <= 1")
    op.create_check_constraint("ck_fusion_inference_mode", "fusion_results", "inference_mode IN ('online', 'offline', 'hybrid', 'synced_offline')")
    op.create_check_constraint("ck_fusion_disease_class", "fusion_results", "disease_class IN ('healthy', 'FMD', 'LSD', 'needs_review')")
    op.create_check_constraint("ck_fusion_confidence_level", "fusion_results", "confidence_level IN ('low', 'medium', 'high')")

    op.create_check_constraint("ck_follow_up_status", "follow_ups", "status IN ('scheduled', 'in_progress', 'resolved', 'closed', 'cancelled')")
    op.create_check_constraint("ck_cluster_signal_count_positive", "cluster_risk_signals", "signal_count >= 0")
    op.create_check_constraint("ck_cluster_window_positive", "cluster_risk_signals", "window_days > 0")
    op.create_check_constraint("ck_cluster_risk_level", "cluster_risk_signals", "risk_level IN ('baseline_monitoring', 'possible_increased_risk', 'low', 'medium', 'high', 'critical')")

    op.create_foreign_key("fk_cattle_farmer", "cattle_profiles", "farmer_accounts", ["farmer_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_detection_farmer", "detection_events", "farmer_accounts", ["farmer_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_detection_cattle", "detection_events", "cattle_profiles", ["cattle_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_media_detection", "stored_media", "detection_events", ["detection_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_fusion_farmer", "fusion_results", "farmer_accounts", ["farmer_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_fusion_cattle", "fusion_results", "cattle_profiles", ["cattle_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_follow_up_farmer", "follow_ups", "farmer_accounts", ["farmer_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_follow_up_cattle", "follow_ups", "cattle_profiles", ["cattle_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_preferences_farmer", "farmer_preferences", "accounts", ["farmer_id"], ["id"], ondelete="CASCADE")

    op.create_index("ix_dashboard_farmers_jurisdiction_consent", "farmer_accounts", ["jurisdiction_id", "consent_state"])
    op.create_index("ix_dashboard_cattle_farmer_status", "cattle_profiles", ["farmer_id", "status"])
    op.create_index("ix_dashboard_fusion_farmer_created", "fusion_results", ["farmer_id", "created_at"])
    op.create_index("ix_dashboard_fusion_cattle_created", "fusion_results", ["cattle_id", "created_at"])
    op.create_index("ix_cluster_fusion_disease_created", "fusion_results", ["disease_class", "created_at"])
    op.create_index("ix_cluster_risk_jurisdiction_disease", "cluster_risk_signals", ["jurisdiction_id", "disease_class", "risk_level"])
    op.create_index("ix_followups_status_farmer", "follow_ups", ["status", "farmer_id"])


def downgrade() -> None:
    for name, table in [
        ("ix_followups_status_farmer", "follow_ups"),
        ("ix_cluster_risk_jurisdiction_disease", "cluster_risk_signals"),
        ("ix_cluster_fusion_disease_created", "fusion_results"),
        ("ix_dashboard_fusion_cattle_created", "fusion_results"),
        ("ix_dashboard_fusion_farmer_created", "fusion_results"),
        ("ix_dashboard_cattle_farmer_status", "cattle_profiles"),
        ("ix_dashboard_farmers_jurisdiction_consent", "farmer_accounts"),
    ]:
        op.drop_index(name, table_name=table)
    for name, table in [
        ("fk_preferences_farmer", "farmer_preferences"), ("fk_follow_up_cattle", "follow_ups"), ("fk_follow_up_farmer", "follow_ups"),
        ("fk_fusion_cattle", "fusion_results"), ("fk_fusion_farmer", "fusion_results"), ("fk_media_detection", "stored_media"),
        ("fk_detection_cattle", "detection_events"), ("fk_detection_farmer", "detection_events"), ("fk_cattle_farmer", "cattle_profiles"),
    ]:
        op.drop_constraint(name, table, type_="foreignkey")
    for name, table in [
        ("ck_cluster_risk_level", "cluster_risk_signals"), ("ck_cluster_window_positive", "cluster_risk_signals"), ("ck_cluster_signal_count_positive", "cluster_risk_signals"),
        ("ck_follow_up_status", "follow_ups"), ("ck_fusion_confidence_level", "fusion_results"), ("ck_fusion_disease_class", "fusion_results"),
        ("ck_fusion_inference_mode", "fusion_results"), ("ck_fusion_confidence_range", "fusion_results"), ("ck_stored_media_content_type", "stored_media"),
        ("ck_stored_media_byte_size", "stored_media"), ("uq_stored_media_checksum", "stored_media"), ("ck_detection_source", "detection_events"),
        ("ck_detection_result_label", "detection_events"), ("ck_detection_confidence_range", "detection_events"), ("ck_cattle_age_nonnegative", "cattle_profiles"),
        ("ck_cattle_status", "cattle_profiles"), ("ck_cattle_sex", "cattle_profiles"), ("uq_cattle_farmer_tag", "cattle_profiles"),
        ("ck_agency_users_role", "agency_users"), ("uq_agency_jurisdictions_parent_level_name", "agency_jurisdictions"), ("ck_agency_jurisdictions_level", "agency_jurisdictions"),
        ("ck_farmer_accounts_consent_state", "farmer_accounts"), ("ck_accounts_email_not_blank", "accounts"), ("ck_accounts_type", "accounts"),
    ]:
        op.drop_constraint(name, table, type_="check" if name.startswith("ck_") else "unique")
    for column in [
        "notes", "purchase_price_idr", "purchase_date", "health_notes",
        "last_deworming_date", "last_vaccination_date", "last_calving_date",
        "is_pregnant", "reproductive_status", "weight_kg", "color", "name",
    ]:
        op.drop_column("cattle_profiles", column)
    op.drop_column("agency_jurisdictions", "longitude")
    op.drop_column("agency_jurisdictions", "latitude")
    op.drop_column("farmer_accounts", "address")
    op.drop_column("accounts", "address")
