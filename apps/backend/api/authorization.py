"""Role-jurisdiction-consent authorization tracer for agency access."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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


ROLE_ACCESS_DEPTH = {
    AgencyRole.ADMIN: None,
    AgencyRole.PROVINCE_OFFICER: None,
    AgencyRole.DISTRICT_OFFICER: None,
    AgencyRole.VILLAGE_OFFICER: 0,
    AgencyRole.VIEWER: 0,
}


def _is_same_or_descendant(
    *,
    target_jurisdiction_id: str,
    agency_jurisdiction_id: str,
    jurisdictions: dict[str, AdministrativeJurisdiction],
) -> bool:
    """Return true when target jurisdiction is agency jurisdiction or below it."""

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
    """Authorize agency visibility using role, jurisdiction, and consent.

    All three gates must pass:
    - role must allow monitoring reads
    - farmer jurisdiction must be inside agency jurisdiction scope
    - farmer consent must allow agency monitoring
    """

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
    """Return only farmer records visible to agency user."""

    return [
        farmer
        for farmer in farmers
        if can_agency_access_farmer(agency, farmer, jurisdictions)
    ]


DEMO_JURISDICTIONS = {
    "central-java": AdministrativeJurisdiction("central-java", None, "province", "Jawa Tengah"),
    "semarang-city": AdministrativeJurisdiction("semarang-city", "central-java", "regency_city", "Kota Semarang"),
    "tembalang": AdministrativeJurisdiction("tembalang", "semarang-city", "district_subdistrict", "Tembalang"),
    "banyumanik": AdministrativeJurisdiction("banyumanik", "semarang-city", "district_subdistrict", "Banyumanik"),
    "west-java": AdministrativeJurisdiction("west-java", None, "province", "Jawa Barat"),
}

DEMO_FARMERS = [
    FarmerRecord("farmer-1", "Pak Tono", "tembalang", ConsentTier.AGENCY_MONITORING),
    FarmerRecord("farmer-2", "Bu Sari", "banyumanik", ConsentTier.PRIVATE),
    FarmerRecord("farmer-3", "Pak Asep", "west-java", ConsentTier.AGENCY_MONITORING),
]

DEMO_AGENCY_USERS = {
    "semarang-officer": AgencyUser("semarang-officer", AgencyRole.DISTRICT_OFFICER, "semarang-city"),
    "tembalang-viewer": AgencyUser("tembalang-viewer", AgencyRole.VIEWER, "tembalang"),
    "central-java-admin": AgencyUser("central-java-admin", AgencyRole.ADMIN, "central-java"),
}
