"""Cattle-first profile persistence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from api.authorization import (
    AgencyUser,
    AdministrativeJurisdiction,
    ConsentTier,
    FarmerRecord,
    can_agency_access_farmer,
)
from api.database import SessionLocal, create_all_tables
from api.db_models import CattleProfileModel, CattleTimelineEventModel
from api.farmer_accounts import FarmerAccount


class CattleEventType(str, Enum):
    VACCINATION = "vaccination"
    DEWORMING = "deworming"
    HEALTH_CHECK = "health_check"
    PREGNANCY_CHECK = "pregnancy_check"
    CALVING = "calving"
    WEIGHT_RECORD = "weight_record"
    OTHER = "other"


@dataclass(frozen=True)
class CattleTimelineEvent:
    """Operational cattle timeline event."""

    id: str
    cattle_id: str
    event_type: CattleEventType
    event_date: str
    title: str
    description: str
    payload: dict[str, Any]
    creator_id: str


class CattleSex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class CattleStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    DEAD = "dead"
    LOST = "lost"
    ARCHIVED = "archived"


class ReproductiveStatus(str, Enum):
    OPEN = "open"
    PREGNANT = "pregnant"
    LACTATING = "lactating"
    DRY = "dry"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CattleProfile:
    """Complete-livestock identity profile used before detection starts."""

    id: str
    farmer_id: str
    tag: str
    sex: CattleSex
    breed: str
    age_months: int | None
    birth_year_estimate: int | None
    status: CattleStatus
    jurisdiction_id: str
    # Physical / identity
    name: str | None = None
    color: str | None = None
    weight_kg: float | None = None
    # Reproduction
    reproductive_status: str | None = None
    is_pregnant: bool | None = None
    last_calving_date: str | None = None
    # Health
    last_vaccination_date: str | None = None
    last_deworming_date: str | None = None
    health_notes: str | None = None
    # Economic
    purchase_date: str | None = None
    purchase_price_idr: int | None = None
    notes: str | None = None


class CattleProfileStore:
    """Cattle profile store backed by platform database."""

    def __init__(self) -> None:
        create_all_tables()

    def create(
        self,
        *,
        farmer: FarmerAccount,
        tag: str,
        sex: CattleSex,
        breed: str,
        age_months: int | None,
        birth_year_estimate: int | None,
        status: CattleStatus,
        jurisdiction_id: str,
        name: str | None = None,
        color: str | None = None,
        weight_kg: float | None = None,
        reproductive_status: str | None = None,
        is_pregnant: bool | None = None,
        last_calving_date: str | None = None,
        last_vaccination_date: str | None = None,
        last_deworming_date: str | None = None,
        health_notes: str | None = None,
        purchase_date: str | None = None,
        purchase_price_idr: int | None = None,
        notes: str | None = None,
    ) -> CattleProfile:
        if age_months is None and birth_year_estimate is None:
            raise ValueError("age_months or birth_year_estimate is required")

        with SessionLocal() as session:
            next_id = session.query(CattleProfileModel).count() + 1
            profile = CattleProfile(
                id=f"cattle-{next_id}",
                farmer_id=farmer.id,
                tag=tag,
                sex=sex,
                breed=breed or "unknown",
                age_months=age_months,
                birth_year_estimate=birth_year_estimate,
                status=status,
                jurisdiction_id=jurisdiction_id,
                name=name,
                color=color,
                weight_kg=weight_kg,
                reproductive_status=reproductive_status,
                is_pregnant=is_pregnant,
                last_calving_date=last_calving_date,
                last_vaccination_date=last_vaccination_date,
                last_deworming_date=last_deworming_date,
                health_notes=health_notes,
                purchase_date=purchase_date,
                purchase_price_idr=purchase_price_idr,
                notes=notes,
            )
            session.add(
                CattleProfileModel(
                    id=profile.id,
                    farmer_id=profile.farmer_id,
                    tag=profile.tag,
                    sex=profile.sex.value,
                    breed=profile.breed,
                    age_months=profile.age_months,
                    birth_year_estimate=profile.birth_year_estimate,
                    status=profile.status.value,
                    jurisdiction_id=profile.jurisdiction_id,
                    name=profile.name,
                    color=profile.color,
                    weight_kg=profile.weight_kg,
                    reproductive_status=profile.reproductive_status,
                    is_pregnant=profile.is_pregnant,
                    last_calving_date=profile.last_calving_date,
                    last_vaccination_date=profile.last_vaccination_date,
                    last_deworming_date=profile.last_deworming_date,
                    health_notes=profile.health_notes,
                    purchase_date=profile.purchase_date,
                    purchase_price_idr=profile.purchase_price_idr,
                    notes=profile.notes,
                )
            )
            session.commit()
            return profile

    def list_by_farmer(self, farmer_id: str) -> list[CattleProfile]:
        with SessionLocal() as session:
            rows = (
                session.query(CattleProfileModel)
                .filter_by(farmer_id=farmer_id)
                .order_by(CattleProfileModel.id)
                .all()
            )
            return [
                _cattle_from_row(row)
                for row in rows
                if row.status != CattleStatus.ARCHIVED.value
            ]

    def get_owned(self, *, farmer_id: str, cattle_id: str) -> CattleProfile | None:
        with SessionLocal() as session:
            row = session.get(CattleProfileModel, cattle_id)
            if row is None or row.farmer_id != farmer_id:
                return None
            return _cattle_from_row(row)

    def update(
        self,
        *,
        farmer_id: str,
        cattle_id: str,
        tag: str,
        sex: CattleSex,
        breed: str,
        age_months: int | None,
        birth_year_estimate: int | None,
        status: CattleStatus,
        jurisdiction_id: str,
        name: str | None = None,
        color: str | None = None,
        weight_kg: float | None = None,
        reproductive_status: str | None = None,
        is_pregnant: bool | None = None,
        last_calving_date: str | None = None,
        last_vaccination_date: str | None = None,
        last_deworming_date: str | None = None,
        health_notes: str | None = None,
        purchase_date: str | None = None,
        purchase_price_idr: int | None = None,
        notes: str | None = None,
    ) -> CattleProfile | None:
        if age_months is None and birth_year_estimate is None:
            raise ValueError("age_months or birth_year_estimate is required")

        with SessionLocal() as session:
            row = session.get(CattleProfileModel, cattle_id)
            if row is None or row.farmer_id != farmer_id:
                return None
            row.tag = tag
            row.sex = sex.value
            row.breed = breed or "unknown"
            row.age_months = age_months
            row.birth_year_estimate = birth_year_estimate
            row.status = status.value
            row.jurisdiction_id = jurisdiction_id
            row.name = name
            row.color = color
            row.weight_kg = weight_kg
            row.reproductive_status = reproductive_status
            row.is_pregnant = is_pregnant
            row.last_calving_date = last_calving_date
            row.last_vaccination_date = last_vaccination_date
            row.last_deworming_date = last_deworming_date
            row.health_notes = health_notes
            row.purchase_date = purchase_date
            row.purchase_price_idr = purchase_price_idr
            row.notes = notes
            session.commit()
            session.refresh(row)
            return _cattle_from_row(row)

    def archive(self, *, farmer_id: str, cattle_id: str) -> CattleProfile | None:
        with SessionLocal() as session:
            row = session.get(CattleProfileModel, cattle_id)
            if row is None or row.farmer_id != farmer_id:
                return None
            row.status = CattleStatus.ARCHIVED.value
            session.commit()
            session.refresh(row)
            return _cattle_from_row(row)

    def add_timeline_event(
        self,
        *,
        farmer_id: str,
        cattle_id: str,
        event_type: CattleEventType,
        event_date: str,
        title: str,
        description: str,
        payload: dict[str, Any],
        creator_id: str,
    ) -> CattleTimelineEvent | None:
        profile = self.get_owned(farmer_id=farmer_id, cattle_id=cattle_id)
        if profile is None:
            return None
        with SessionLocal() as session:
            next_id = session.query(CattleTimelineEventModel).count() + 1
            event = CattleTimelineEvent(
                id=f"event-{next_id}",
                cattle_id=cattle_id,
                event_type=event_type,
                event_date=event_date,
                title=title,
                description=description,
                payload=payload,
                creator_id=creator_id,
            )
            session.add(
                CattleTimelineEventModel(
                    id=event.id,
                    cattle_id=event.cattle_id,
                    event_type=event.event_type.value,
                    event_date=event.event_date,
                    title=event.title,
                    description=event.description,
                    payload=event.payload,
                    creator_id=event.creator_id,
                )
            )
            session.commit()
            return event

    def list_timeline_events(self, cattle_id: str) -> list[CattleTimelineEvent]:
        with SessionLocal() as session:
            rows = (
                session.query(CattleTimelineEventModel)
                .filter_by(cattle_id=cattle_id)
                .order_by(
                    CattleTimelineEventModel.event_date.desc(),
                    CattleTimelineEventModel.id.desc(),
                )
                .all()
            )
            return [_timeline_event_from_row(row) for row in rows]

    def list_visible_to_agency(
        self,
        *,
        agency: AgencyUser,
        farmers_by_id: dict[str, FarmerAccount],
        jurisdictions: dict[str, AdministrativeJurisdiction],
    ) -> list[CattleProfile]:
        with SessionLocal() as session:
            profiles = [
                _cattle_from_row(row)
                for row in session.query(CattleProfileModel)
                .filter(CattleProfileModel.status != CattleStatus.ARCHIVED.value)
                .all()
            ]
        visible: list[CattleProfile] = []
        for profile in profiles:
            farmer = farmers_by_id.get(profile.farmer_id)
            if farmer is None:
                continue
            farmer_record = FarmerRecord(
                id=farmer.id,
                name=farmer.name,
                jurisdiction_id=profile.jurisdiction_id,
                consent_tier=ConsentTier(farmer.consent_state.value),
            )
            if can_agency_access_farmer(agency, farmer_record, jurisdictions):
                visible.append(profile)
        return visible

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(CattleTimelineEventModel).delete()
            session.query(CattleProfileModel).delete()
            session.commit()


def _cattle_from_row(row: CattleProfileModel) -> CattleProfile:
    return CattleProfile(
        id=row.id,
        farmer_id=row.farmer_id,
        tag=row.tag,
        sex=CattleSex(row.sex),
        breed=row.breed,
        age_months=row.age_months,
        birth_year_estimate=row.birth_year_estimate,
        status=CattleStatus(row.status),
        jurisdiction_id=row.jurisdiction_id,
        name=getattr(row, "name", None),
        color=getattr(row, "color", None),
        weight_kg=getattr(row, "weight_kg", None),
        reproductive_status=getattr(row, "reproductive_status", None),
        is_pregnant=getattr(row, "is_pregnant", None),
        last_calving_date=getattr(row, "last_calving_date", None),
        last_vaccination_date=getattr(row, "last_vaccination_date", None),
        last_deworming_date=getattr(row, "last_deworming_date", None),
        health_notes=getattr(row, "health_notes", None),
        purchase_date=getattr(row, "purchase_date", None),
        purchase_price_idr=getattr(row, "purchase_price_idr", None),
        notes=getattr(row, "notes", None),
    )


def _timeline_event_from_row(row: CattleTimelineEventModel) -> CattleTimelineEvent:
    return CattleTimelineEvent(
        id=row.id,
        cattle_id=row.cattle_id,
        event_type=CattleEventType(row.event_type),
        event_date=row.event_date,
        title=row.title,
        description=row.description,
        payload=row.payload,
        creator_id=row.creator_id,
    )


cattle_profile_store = CattleProfileStore()
