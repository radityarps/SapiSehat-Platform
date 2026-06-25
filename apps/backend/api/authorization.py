"""Role-jurisdiction-consent authorization tracer for agency access."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from api.database import SessionLocal, create_all_tables
from api.db_models import AgencyJurisdictionModel, AgencyUserModel


class AgencyRole(str, Enum):
    ADMIN = "admin"
    PROVINCE_OFFICER = "province_officer"
    DISTRICT_OFFICER = "district_officer"
    VILLAGE_OFFICER = "village_officer"
    VIEWER = "viewer"


class ConsentTier(str, Enum):
    PRIVATE = "private"
    AGENCY_MONITORING = "agency_monitoring"
    RESEARCH_AND_MONITORING = "research_and_monitoring"


@dataclass(frozen=True)
class AdministrativeJurisdiction:
    """Indonesia administrative jurisdiction node."""

    id: str
    parent_id: str | None
    level: str
    name: str
    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True)
class AgencyUser:
    """Agency dashboard user identity for authorization decisions."""

    id: str
    role: AgencyRole
    jurisdiction_id: str


@dataclass(frozen=True)
class FarmerRecord:
    """Farmer-owned platform record protected by jurisdiction and consent."""

    id: str
    name: str
    jurisdiction_id: str
    consent_tier: ConsentTier
    address: str | None = None


ROLE_ACCESS_DEPTH = {
    AgencyRole.ADMIN: None,
    AgencyRole.PROVINCE_OFFICER: None,
    AgencyRole.DISTRICT_OFFICER: None,
    AgencyRole.VILLAGE_OFFICER: 0,
    AgencyRole.VIEWER: 0,
}


class JurisdictionStore:
    def __init__(self) -> None:
        create_all_tables()

    def seed_defaults(self) -> None:
        with SessionLocal() as session:
            if session.query(AgencyJurisdictionModel).count() > 0:
                return
            session.add_all(
                [
                    AgencyJurisdictionModel(
                        id="central-java",
                        parent_id=None,
                        level="province",
                        name="Jawa Tengah",
                        latitude=-7.150975,
                        longitude=110.140259,
                    ),
                    AgencyJurisdictionModel(
                        id="semarang-city",
                        parent_id="central-java",
                        level="regency_city",
                        name="Kota Semarang",
                        latitude=-6.966667,
                        longitude=110.416664,
                    ),
                    AgencyJurisdictionModel(
                        id="tembalang",
                        parent_id="semarang-city",
                        level="district_subdistrict",
                        name="Tembalang",
                        latitude=-7.044997,
                        longitude=110.445999,
                    ),
                    AgencyJurisdictionModel(
                        id="banyumanik",
                        parent_id="semarang-city",
                        level="district_subdistrict",
                        name="Banyumanik",
                        latitude=-7.066667,
                        longitude=110.416664,
                    ),
                    AgencyJurisdictionModel(
                        id="west-java",
                        parent_id=None,
                        level="province",
                        name="Jawa Barat",
                        latitude=-6.914744,
                        longitude=107.609810,
                    ),
                ]
            )
            session.commit()

    def all_by_id(self) -> dict[str, AdministrativeJurisdiction]:
        with SessionLocal() as session:
            rows = session.query(AgencyJurisdictionModel).all()
            return {row.id: _jurisdiction_from_row(row) for row in rows}


class AgencyUserStore:
    def __init__(self) -> None:
        create_all_tables()

    def seed_defaults(self) -> None:
        with SessionLocal() as session:
            if session.query(AgencyUserModel).count() > 0:
                return
            session.add_all(
                [
                    AgencyUserModel(
                        id="semarang-officer",
                        role=AgencyRole.DISTRICT_OFFICER.value,
                        jurisdiction_id="semarang-city",
                    ),
                    AgencyUserModel(
                        id="tembalang-viewer",
                        role=AgencyRole.VIEWER.value,
                        jurisdiction_id="tembalang",
                    ),
                    AgencyUserModel(
                        id="central-java-admin",
                        role=AgencyRole.ADMIN.value,
                        jurisdiction_id="central-java",
                    ),
                ]
            )
            session.commit()

    def get(self, user_id: str) -> AgencyUser | None:
        with SessionLocal() as session:
            row = session.get(AgencyUserModel, user_id)
            return None if row is None else _agency_from_row(row)

    def all(self) -> dict[str, AgencyUser]:
        with SessionLocal() as session:
            rows = session.query(AgencyUserModel).all()
            return {row.id: _agency_from_row(row) for row in rows}

    def ensure_exists(self, user_id: str, role: str, jurisdiction_id: str) -> None:
        """Ensure an agency user entry exists for a given account ID."""
        with SessionLocal() as session:
            existing = session.get(AgencyUserModel, user_id)
            if existing is None:
                session.add(
                    AgencyUserModel(
                        id=user_id, role=role, jurisdiction_id=jurisdiction_id
                    )
                )
                session.commit()

    def list_all(self) -> list[AgencyUser]:
        """List all agency users."""
        with SessionLocal() as session:
            rows = session.query(AgencyUserModel).all()
            return [_agency_from_row(row) for row in rows]

    def update_role(
        self, user_id: str, role: str, jurisdiction_id: str | None = None
    ) -> AgencyUser | None:
        """Update an agency user's role and optionally jurisdiction."""
        with SessionLocal() as session:
            row = session.get(AgencyUserModel, user_id)
            if row is None:
                return None
            row.role = role
            if jurisdiction_id is not None:
                row.jurisdiction_id = jurisdiction_id
            session.commit()
            session.refresh(row)
            return _agency_from_row(row)

    def delete(self, user_id: str) -> bool:
        """Delete an agency user."""
        with SessionLocal() as session:
            row = session.get(AgencyUserModel, user_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True


_jurisdiction_store = JurisdictionStore()
_agency_user_store = AgencyUserStore()
_jurisdiction_store.seed_defaults()
_agency_user_store.seed_defaults()


def _is_same_or_descendant(
    *,
    target_jurisdiction_id: str,
    agency_jurisdiction_id: str,
    jurisdictions: dict[str, AdministrativeJurisdiction],
) -> bool:
    current_id: str | None = target_jurisdiction_id
    while current_id is not None:
        if current_id == agency_jurisdiction_id:
            return True
        current = jurisdictions.get(current_id)
        current_id = current.parent_id if current else None
    return False


def can_agency_access_farmer(
    agency: AgencyUser,
    farmer: FarmerRecord,
    jurisdictions: dict[str, AdministrativeJurisdiction],
) -> bool:
    if agency.role not in ROLE_ACCESS_DEPTH:
        return False
    if farmer.consent_tier == ConsentTier.PRIVATE:
        return False
    if agency.role == AgencyRole.ADMIN:
        return True
    return _is_same_or_descendant(
        target_jurisdiction_id=farmer.jurisdiction_id,
        agency_jurisdiction_id=agency.jurisdiction_id,
        jurisdictions=jurisdictions,
    )


def filter_visible_farmers(
    agency: AgencyUser,
    farmers: list[FarmerRecord],
    jurisdictions: dict[str, AdministrativeJurisdiction],
) -> list[FarmerRecord]:
    return [
        farmer
        for farmer in farmers
        if can_agency_access_farmer(agency, farmer, jurisdictions)
    ]


def _jurisdiction_from_row(row: AgencyJurisdictionModel) -> AdministrativeJurisdiction:
    return AdministrativeJurisdiction(
        row.id,
        row.parent_id,
        row.level,
        row.name,
        getattr(row, "latitude", None),
        getattr(row, "longitude", None),
    )


def _agency_from_row(row: AgencyUserModel) -> AgencyUser:
    return AgencyUser(row.id, AgencyRole(row.role), row.jurisdiction_id)


DEMO_JURISDICTIONS = _jurisdiction_store.all_by_id()
DEMO_FARMERS = [
    FarmerRecord("farmer-1", "Pak Tono", "tembalang", ConsentTier.AGENCY_MONITORING),
    FarmerRecord("farmer-2", "Bu Sari", "banyumanik", ConsentTier.PRIVATE),
    FarmerRecord("farmer-3", "Pak Asep", "west-java", ConsentTier.AGENCY_MONITORING),
]
DEMO_AGENCY_USERS = _agency_user_store.all()


def refresh_agency_users() -> None:
    """Reload DEMO_AGENCY_USERS after new accounts are seeded."""
    global DEMO_AGENCY_USERS
    DEMO_AGENCY_USERS.clear()
    DEMO_AGENCY_USERS.update(_agency_user_store.all())
