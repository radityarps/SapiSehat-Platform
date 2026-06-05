"""Cattle-first profile tracer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from api.authorization import AgencyUser, AdministrativeJurisdiction, FarmerRecord, can_agency_access_farmer
from api.farmer_accounts import FarmerAccount, FarmerConsentState


class CattleSex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class CattleStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    DEAD = "dead"
    LOST = "lost"


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


class CattleProfileStore:
    """In-memory cattle store for tracer implementation."""

    def __init__(self) -> None:
        self._profiles_by_id: dict[str, CattleProfile] = {}
        self._next_id = 1

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
    ) -> CattleProfile:
        if age_months is None and birth_year_estimate is None:
            raise ValueError("age_months or birth_year_estimate is required")

        profile = CattleProfile(
            id=f"cattle-{self._next_id}",
            farmer_id=farmer.id,
            tag=tag,
            sex=sex,
            breed=breed or "unknown",
            age_months=age_months,
            birth_year_estimate=birth_year_estimate,
            status=status,
            jurisdiction_id=jurisdiction_id,
        )
        self._next_id += 1
        self._profiles_by_id[profile.id] = profile
        return profile

    def list_by_farmer(self, farmer_id: str) -> list[CattleProfile]:
        return [profile for profile in self._profiles_by_id.values() if profile.farmer_id == farmer_id]

    def get_owned(self, *, farmer_id: str, cattle_id: str) -> CattleProfile | None:
        profile = self._profiles_by_id.get(cattle_id)
        if profile is None or profile.farmer_id != farmer_id:
            return None
        return profile

    def list_visible_to_agency(
        self,
        *,
        agency: AgencyUser,
        farmers_by_id: dict[str, FarmerAccount],
        jurisdictions: dict[str, AdministrativeJurisdiction],
    ) -> list[CattleProfile]:
        visible: list[CattleProfile] = []
        for profile in self._profiles_by_id.values():
            farmer = farmers_by_id.get(profile.farmer_id)
            if farmer is None:
                continue
            farmer_record = FarmerRecord(
                id=farmer.id,
                name=farmer.name,
                jurisdiction_id=profile.jurisdiction_id,
                consent_tier=farmer.consent_state.value,
            )
            if can_agency_access_farmer(agency, farmer_record, jurisdictions):
                visible.append(profile)
        return visible

    def clear(self) -> None:
        self._profiles_by_id.clear()
        self._next_id = 1


cattle_profile_store = CattleProfileStore()
