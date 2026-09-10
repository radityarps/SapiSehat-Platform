"""SQLAlchemy persistence models for platform foundation."""

from __future__ import annotations

import uuid

from sqlalchemy import (  # type: ignore[import-not-found]
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (  # type: ignore[import-not-found]
    Mapped,
    mapped_column,
    relationship,
)

from api.database import Base


class AccountModel(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("account_type", "email", name="uq_accounts_type_email"),
        CheckConstraint(
            "account_type IN ('farmer', 'agency', 'admin')", name="ck_accounts_type"
        ),
        CheckConstraint("length(trim(email)) > 3", name="ck_accounts_email_not_blank"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    jurisdiction_id: Mapped[str] = mapped_column(
        String(120), nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    archived_at: Mapped[str | None] = mapped_column(String(80), nullable=True)


class FarmerAccountModel(Base):
    __tablename__ = "farmer_accounts"
    __table_args__ = (
        CheckConstraint(
            "consent_state IN ('private', 'agency_monitoring', 'research_and_monitoring')",
            name="ck_farmer_accounts_consent_state",
        ),
        Index(
            "ix_dashboard_farmers_jurisdiction_consent",
            "jurisdiction_id",
            "consent_state",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(40), nullable=True, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    jurisdiction_id: Mapped[str] = mapped_column(
        String(120), nullable=False, index=True
    )
    consent_state: Mapped[str] = mapped_column(
        String(80), nullable=False, index=True, default="agency_monitoring"
    )
    scan_image_storage_notice_accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    account: Mapped[AccountModel | None] = relationship(
        "AccountModel",
        lazy="joined",
        uselist=False,
    )


class AgencyJurisdictionModel(Base):
    __tablename__ = "agency_jurisdictions"
    __table_args__ = (
        UniqueConstraint(
            "parent_id",
            "level",
            "name",
            name="uq_agency_jurisdictions_parent_level_name",
        ),
        CheckConstraint(
            "level IN ('province', 'regency_city', 'district_subdistrict', 'village')",
            name="ck_agency_jurisdictions_level",
        ),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    parent_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    level: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)


def generate_agency_user_id() -> str:
    return str(uuid.uuid4())


class AgencyUserModel(Base):
    __tablename__ = "agency_users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'province_officer', 'district_officer', 'village_officer', 'viewer')",
            name="ck_agency_users_role",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        primary_key=True,
        default=generate_agency_user_id,
    )
    role: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    jurisdiction_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    account: Mapped[AccountModel | None] = relationship(
        "AccountModel",
        lazy="joined",
        uselist=False,
    )


class CattleProfileModel(Base):
    __tablename__ = "cattle_profiles"
    __table_args__ = (
        UniqueConstraint("farmer_id", "tag", name="uq_cattle_farmer_tag"),
        CheckConstraint("sex IN ('female', 'male', 'unknown')", name="ck_cattle_sex"),
        CheckConstraint(
            "status IN ('active', 'sold', 'dead', 'lost', 'archived')",
            name="ck_cattle_status",
        ),
        CheckConstraint(
            "age_months IS NULL OR age_months >= 0", name="ck_cattle_age_nonnegative"
        ),
        Index("ix_dashboard_cattle_farmer_status", "farmer_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("farmer_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sex: Mapped[str] = mapped_column(String(20), nullable=False)
    breed: Mapped[str] = mapped_column(String(120), nullable=False)
    color: Mapped[str | None] = mapped_column(String(80), nullable=True)
    age_months: Mapped[int | None]
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    reproductive_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_pregnant: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    birth_year_estimate: Mapped[int | None]
    last_calving_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_vaccination_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_deworming_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    health_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    purchase_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    purchase_price_idr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    jurisdiction_id: Mapped[str] = mapped_column(
        String(120), nullable=False, index=True
    )


class DetectionEventModel(Base):
    __tablename__ = "detection_events"
    __table_args__ = (
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_detection_confidence_range"
        ),
        CheckConstraint(
            "result_label IN ('healthy', 'FMD', 'LSD', 'needs_review')",
            name="ck_detection_result_label",
        ),
        CheckConstraint(
            "source IN ('quick_scan', 'mobile', 'api', 'offline_sync', 'seed')",
            name="ck_detection_source",
        ),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("farmer_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cattle_id: Mapped[str | None] = mapped_column(
        String(80),
        ForeignKey("cattle_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    result_label: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)


class StoredMediaModel(Base):
    __tablename__ = "stored_media"
    __table_args__ = (
        UniqueConstraint("checksum", name="uq_stored_media_checksum"),
        CheckConstraint("byte_size >= 0", name="ck_stored_media_byte_size"),
        CheckConstraint(
            "content_type LIKE 'image/%'", name="ck_stored_media_content_type"
        ),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    cattle_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    detection_id: Mapped[str | None] = mapped_column(
        String(80),
        ForeignKey("detection_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    checksum: Mapped[str] = mapped_column(String(160), nullable=False)
    consent_scope: Mapped[str] = mapped_column(String(80), nullable=False)
    storage_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_backend: Mapped[str] = mapped_column(
        String(80), nullable=False, default="metadata-only"
    )
    object_key: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    content_type: Mapped[str] = mapped_column(
        String(80), nullable=False, default="image/jpeg"
    )
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retention_policy: Mapped[str] = mapped_column(
        String(80), nullable=False, default="first_release_monitoring"
    )
    created_at: Mapped[str] = mapped_column(String(80), nullable=False, default="")


class FusionResultModel(Base):
    __tablename__ = "fusion_results"
    __table_args__ = (
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_fusion_confidence_range"
        ),
        CheckConstraint(
            "inference_mode IN ('online', 'offline', 'hybrid', 'synced_offline')",
            name="ck_fusion_inference_mode",
        ),
        CheckConstraint(
            "disease_class IN ('healthy', 'FMD', 'LSD', 'needs_review')",
            name="ck_fusion_disease_class",
        ),
        CheckConstraint(
            "confidence_level IN ('low', 'medium', 'high')",
            name="ck_fusion_confidence_level",
        ),
        Index("ix_dashboard_fusion_farmer_created", "farmer_id", "created_at"),
        Index("ix_dashboard_fusion_cattle_created", "cattle_id", "created_at"),
        Index("ix_cluster_fusion_disease_created", "disease_class", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    fusion_version: Mapped[str] = mapped_column(String(80), nullable=False)
    inference_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    farmer_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("farmer_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cattle_id: Mapped[str | None] = mapped_column(
        String(80),
        ForeignKey("cattle_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    disease_class: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False)
    reliability: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    handling_advice_key: Mapped[str] = mapped_column(String(160), nullable=False)
    evidence_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)
    conflict_status: Mapped[str] = mapped_column(String(80), nullable=False)
    model_versions: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(80), nullable=False)


class CattleTimelineEventModel(Base):
    __tablename__ = "cattle_timeline_events"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    cattle_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    event_date: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    creator_id: Mapped[str] = mapped_column(String(80), nullable=False)


class OfflineSyncedDetectionModel(Base):
    __tablename__ = "offline_synced_detections"

    local_detection_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    sync_status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    fusion_result_id: Mapped[str] = mapped_column(
        String(80), nullable=False, index=True
    )
    local_created_at: Mapped[str] = mapped_column(String(80), nullable=False)
    synced_at: Mapped[str] = mapped_column(String(80), nullable=False)


class FollowUpModel(Base):
    __tablename__ = "follow_ups"
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'resolved', 'closed', 'cancelled')",
            name="ck_follow_up_status",
        ),
        Index("ix_followups_status_farmer", "status", "farmer_id"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("farmer_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cattle_id: Mapped[str | None] = mapped_column(
        String(80),
        ForeignKey("cattle_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    public_message: Mapped[str] = mapped_column(String(500), nullable=False)
    internal_notes: Mapped[str] = mapped_column(String(1000), nullable=False)


class ClusterRiskSignalModel(Base):
    __tablename__ = "cluster_risk_signals"
    __table_args__ = (
        CheckConstraint("signal_count >= 0", name="ck_cluster_signal_count_positive"),
        CheckConstraint("window_days > 0", name="ck_cluster_window_positive"),
        CheckConstraint(
            "risk_level IN ('baseline_monitoring', 'possible_increased_risk', 'low', 'medium', 'high', 'critical')",
            name="ck_cluster_risk_level",
        ),
        Index(
            "ix_cluster_risk_jurisdiction_disease",
            "jurisdiction_id",
            "disease_class",
            "risk_level",
        ),
    )

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    jurisdiction_id: Mapped[str] = mapped_column(
        String(120), nullable=False, index=True
    )
    disease_class: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    signal_count: Mapped[int] = mapped_column(Integer, nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(80), nullable=False)
    summary_label: Mapped[str] = mapped_column(String(160), nullable=False)
    source_result_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class RateLimitRequestModel(Base):
    __tablename__ = "rate_limit_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_key: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    requested_at: Mapped[float] = mapped_column(nullable=False, index=True)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(80), nullable=False, index=True)


class FarmerPreferenceModel(Base):
    __tablename__ = "farmer_preferences"

    farmer_id: Mapped[str] = mapped_column(
        String(80), ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    scan_result_notifications: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    sync_notifications: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    area_risk_advisory_notifications: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    follow_up_status_notifications: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    quiet_hours_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    quiet_hours_start: Mapped[str] = mapped_column(
        String(8), nullable=False, default="21:00"
    )
    quiet_hours_end: Mapped[str] = mapped_column(
        String(8), nullable=False, default="06:00"
    )


class GuideCategoryModel(Base):
    __tablename__ = "guide_categories"
    __table_args__ = (
        CheckConstraint(
            "state IN ('active', 'archived')", name="ck_guide_categories_state"
        ),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    state: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    system_owned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String(80), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(80), nullable=False)


class GuideCategoryTranslationModel(Base):
    __tablename__ = "guide_category_translations"
    __table_args__ = (
        UniqueConstraint("category_id", "locale", name="uq_guide_category_locale"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    category_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("guide_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)


class GuideArticleModel(Base):
    __tablename__ = "guide_articles"
    __table_args__ = (
        CheckConstraint(
            "state IN ('draft', 'published', 'unpublished', 'archived')",
            name="ck_guide_articles_state",
        ),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    category_id: Mapped[str] = mapped_column(
        String(80), ForeignKey("guide_categories.id"), nullable=False, index=True
    )
    state: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    published_at: Mapped[str | None] = mapped_column(
        String(80), nullable=True, index=True
    )
    published_document: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(String(80), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(80), nullable=False)


class GuideArticleTranslationModel(Base):
    __tablename__ = "guide_article_translations"
    __table_args__ = (
        UniqueConstraint("article_id", "locale", name="uq_guide_article_locale"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    article_id: Mapped[str] = mapped_column(
        String(80),
        ForeignKey("guide_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    blocks: Mapped[list[dict]] = mapped_column(JSON, nullable=False)


class GuideMediaModel(Base):
    __tablename__ = "guide_media"
    __table_args__ = (
        CheckConstraint(
            "mime_type IN ('image/jpeg', 'image/png', 'image/webp')",
            name="ck_guide_media_type",
        ),
        CheckConstraint(
            "byte_size >= 0 AND width > 0 AND height > 0",
            name="ck_guide_media_dimensions",
        ),
        UniqueConstraint("sha256", name="uq_guide_media_sha256"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(40), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[str] = mapped_column(String(80), nullable=False)


class GuideManifestModel(Base):
    __tablename__ = "guide_manifests"

    version: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    created_at: Mapped[str] = mapped_column(String(80), nullable=False)
    catalog: Mapped[dict] = mapped_column(JSON, nullable=False)


class GuideEditorialAuditEventModel(Base):
    __tablename__ = "guide_editorial_audit_events"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(80), nullable=False, index=True)


class NotificationModel(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    account_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(String(500), nullable=False)
    link: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
