"""Role-jurisdiction-consent authorization tracer for agency access."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from api.database import SessionLocal, create_all_tables
from api.db_models import (
    AccountModel,
    AgencyJurisdictionModel,
    AgencyUserModel,
    CattleProfileModel,
    FarmerAccountModel,
)


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


class JurisdictionLevel(str, Enum):
    PROVINCE = "province"
    REGENCY_CITY = "regency_city"
    DISTRICT_SUBDISTRICT = "district_subdistrict"
    VILLAGE = "village"


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
    name: str | None = None
    email: str | None = None


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

    def create(
        self,
        *,
        jurisdiction_id: str,
        name: str,
        level: str,
        parent_id: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> AdministrativeJurisdiction:
        with SessionLocal() as session:
            normalized_id = jurisdiction_id.strip().lower()
            normalized_name = name.strip()
            if not normalized_id or not normalized_name:
                raise ValueError("jurisdiction ID and name are required")
            self._validate_parent(session, level, parent_id)
            if session.get(AgencyJurisdictionModel, normalized_id) is not None:
                raise ValueError("jurisdiction ID already exists")
            row = AgencyJurisdictionModel(
                id=normalized_id,
                parent_id=parent_id,
                level=level,
                name=normalized_name,
                latitude=latitude,
                longitude=longitude,
            )
            session.add(row)
            try:
                session.commit()
            except Exception as exc:
                session.rollback()
                raise ValueError("jurisdiction already exists at this level") from exc
            return _jurisdiction_from_row(row)

    @staticmethod
    def _validate_parent(session, level: str, parent_id: str | None) -> None:
        try:
            jurisdiction_level = JurisdictionLevel(level)
        except ValueError as exc:
            raise ValueError("invalid jurisdiction level") from exc

        parent_levels = {
            JurisdictionLevel.PROVINCE: None,
            JurisdictionLevel.REGENCY_CITY: JurisdictionLevel.PROVINCE,
            JurisdictionLevel.DISTRICT_SUBDISTRICT: JurisdictionLevel.REGENCY_CITY,
            JurisdictionLevel.VILLAGE: JurisdictionLevel.DISTRICT_SUBDISTRICT,
        }
        expected_parent_level = parent_levels[jurisdiction_level]
        if expected_parent_level is None:
            if parent_id is not None:
                raise ValueError("province jurisdiction cannot have a parent")
            return
        if parent_id is None:
            raise ValueError(f"{level} jurisdiction requires a parent")
        parent = session.get(AgencyJurisdictionModel, parent_id)
        if parent is None:
            raise ValueError("parent jurisdiction not found")
        if parent.level != expected_parent_level.value:
            raise ValueError(
                f"{level} jurisdiction requires a {expected_parent_level.value} parent"
            )

    def update(
        self,
        jurisdiction_id: str,
        *,
        name: str,
        level: str,
        parent_id: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> AdministrativeJurisdiction | None:
        with SessionLocal() as session:
            row = session.get(AgencyJurisdictionModel, jurisdiction_id)
            if row is None:
                return None
            if parent_id == jurisdiction_id:
                raise ValueError("jurisdiction cannot be its own parent")
            self._validate_parent(session, level, parent_id)
            row.name = name
            row.level = level
            row.parent_id = parent_id
            row.latitude = latitude
            row.longitude = longitude
            try:
                session.commit()
            except Exception as exc:
                session.rollback()
                raise ValueError("jurisdiction already exists at this level") from exc
            session.refresh(row)
            return _jurisdiction_from_row(row)

    def delete(self, jurisdiction_id: str) -> bool:
        with SessionLocal() as session:
            row = session.get(AgencyJurisdictionModel, jurisdiction_id)
            if row is None:
                return False
            if (
                session.query(AgencyJurisdictionModel)
                .filter(AgencyJurisdictionModel.parent_id == jurisdiction_id)
                .first()
                is not None
            ):
                raise ValueError("delete child jurisdictions first")
            if (
                session.query(AgencyUserModel)
                .filter(AgencyUserModel.jurisdiction_id == jurisdiction_id)
                .first()
                is not None
            ):
                raise ValueError("jurisdiction is assigned to an agency user")
            if (
                session.query(AccountModel)
                .filter(AccountModel.jurisdiction_id == jurisdiction_id)
                .first()
                is not None
            ):
                raise ValueError("jurisdiction is referenced by an account")
            if (
                session.query(FarmerAccountModel)
                .filter(FarmerAccountModel.jurisdiction_id == jurisdiction_id)
                .first()
                is not None
            ):
                raise ValueError("jurisdiction is referenced by a farmer record")
            if (
                session.query(CattleProfileModel)
                .filter(CattleProfileModel.jurisdiction_id == jurisdiction_id)
                .first()
                is not None
            ):
                raise ValueError("jurisdiction is referenced by a cattle record")
            session.delete(row)
            session.commit()
            return True


class AgencyUserStore:
    def __init__(self) -> None:
        create_all_tables()

    def seed_defaults(self) -> None:
        from api.surface_auth import seed_default_agency_accounts

        seed_default_agency_accounts()

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
        from api.db_models import AccountModel

        with SessionLocal() as session:
            existing = session.get(AgencyUserModel, user_id)
            if existing is None:
                if session.get(AccountModel, user_id) is None:
                    session.add(
                        AccountModel(
                            id=user_id,
                            account_type="agency",
                            email=f"{user_id}@sapisehat.id",
                            name=user_id,
                            jurisdiction_id=jurisdiction_id,
                            password_hash="",
                        )
                    )
                session.add(
                    AgencyUserModel(
                        id=user_id, role=role, jurisdiction_id=jurisdiction_id
                    )
                )
                session.commit()

    def create(
        self, role: str, jurisdiction_id: str, user_id: str | None = None
    ) -> AgencyUser:
        """Create an agency user with auto-generated ID if omitted."""
        from api.db_models import AccountModel, generate_agency_user_id

        with SessionLocal() as session:
            target_id = user_id or generate_agency_user_id()
            if session.get(AccountModel, target_id) is None:
                session.add(
                    AccountModel(
                        id=target_id,
                        account_type="agency",
                        email=f"{target_id}@sapisehat.id",
                        name=target_id,
                        jurisdiction_id=jurisdiction_id,
                        password_hash="",
                    )
                )
            user = AgencyUserModel(
                id=target_id,
                role=role,
                jurisdiction_id=jurisdiction_id,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return _agency_from_row(user)

    def list_all(self) -> list[AgencyUser]:
        """List all agency users."""
        with SessionLocal() as session:
            rows = session.query(AgencyUserModel).all()
            return [_agency_from_row(row) for row in rows]

    def update_role(
        self,
        user_id: str,
        role: str,
        jurisdiction_id: str | None = None,
        name: str | None = None,
    ) -> AgencyUser | None:
        """Update an agency user's role, jurisdiction, and optionally name."""
        from api.db_models import AccountModel

        with SessionLocal() as session:
            row = session.get(AgencyUserModel, user_id)
            if row is None:
                return None
            row.role = role
            if jurisdiction_id is not None:
                row.jurisdiction_id = jurisdiction_id
            if name is not None:
                account = session.get(AccountModel, user_id)
                if account is not None:
                    account.name = name
                    if jurisdiction_id is not None:
                        account.jurisdiction_id = jurisdiction_id
            session.commit()
            session.refresh(row)
            return _agency_from_row(row)

    def delete(self, user_id: str) -> bool:
        """Delete an agency user and their login account if present."""
        from api.db_models import AccountModel

        with SessionLocal() as session:
            row = session.get(AgencyUserModel, user_id)
            if row is None:
                return False
            account = session.get(AccountModel, user_id)
            session.delete(row)
            if account is not None:
                session.delete(account)
            session.commit()
            return True


_jurisdiction_store = JurisdictionStore()
_agency_user_store = AgencyUserStore()


def _agency_from_row(row: AgencyUserModel) -> AgencyUser:
    account = getattr(row, "account", None)
    return AgencyUser(
        id=row.id,
        role=AgencyRole(row.role),
        jurisdiction_id=row.jurisdiction_id,
        name=account.name if account else None,
        email=account.email if account else None,
    )


DEMO_AGENCY_USERS: dict[str, AgencyUser] = {}


def refresh_agency_users() -> None:
    """Reload DEMO_AGENCY_USERS after new accounts are seeded."""
    DEMO_AGENCY_USERS.clear()
    DEMO_AGENCY_USERS.update(_agency_user_store.all())


_jurisdiction_store.seed_defaults()
_agency_user_store.seed_defaults()
refresh_agency_users()


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


DEMO_JURISDICTIONS = _jurisdiction_store.all_by_id()
DEMO_FARMERS = [
    FarmerRecord("farmer-1", "Pak Tono", "tembalang", ConsentTier.AGENCY_MONITORING),
    FarmerRecord("farmer-2", "Bu Sari", "banyumanik", ConsentTier.PRIVATE),
    FarmerRecord("farmer-3", "Pak Asep", "west-java", ConsentTier.AGENCY_MONITORING),
]
