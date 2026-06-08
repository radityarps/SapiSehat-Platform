"""SQLAlchemy persistence models for platform foundation."""

from __future__ import annotations

from sqlalchemy import JSON, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base


class AccountModel(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("account_type", "email", name="uq_accounts_type_email"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    jurisdiction_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)

class FarmerAccountModel(Base):
    __tablename__ = "farmer_accounts"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    phone_number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    jurisdiction_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    consent_state: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

class AgencyJurisdictionModel(Base):
    __tablename__ = "agency_jurisdictions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    parent_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    level: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

class AgencyUserModel(Base):
    __tablename__ = "agency_users"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    jurisdiction_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

class CattleProfileModel(Base):
    __tablename__ = "cattle_profiles"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    tag: Mapped[str] = mapped_column(String(80), nullable=False)
    sex: Mapped[str] = mapped_column(String(20), nullable=False)
    breed: Mapped[str] = mapped_column(String(120), nullable=False)
    age_months: Mapped[int | None]
    birth_year_estimate: Mapped[int | None]
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    jurisdiction_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)


class DetectionEventModel(Base):
    __tablename__ = "detection_events"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    cattle_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    result_label: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)


class StoredMediaModel(Base):
    __tablename__ = "stored_media"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    cattle_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    detection_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    checksum: Mapped[str] = mapped_column(String(160), nullable=False)
    consent_scope: Mapped[str] = mapped_column(String(80), nullable=False)
    storage_reference: Mapped[str] = mapped_column(String(500), nullable=False)


class FusionResultModel(Base):
    __tablename__ = "fusion_results"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    fusion_version: Mapped[str] = mapped_column(String(80), nullable=False)
    inference_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    farmer_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    cattle_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
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
    fusion_result_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    local_created_at: Mapped[str] = mapped_column(String(80), nullable=False)
    synced_at: Mapped[str] = mapped_column(String(80), nullable=False)

class FollowUpModel(Base):
    __tablename__ = "follow_ups"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    cattle_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    public_message: Mapped[str] = mapped_column(String(500), nullable=False)
    internal_notes: Mapped[str] = mapped_column(String(1000), nullable=False)


class ClusterRiskSignalModel(Base):
    __tablename__ = "cluster_risk_signals"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    jurisdiction_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
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
