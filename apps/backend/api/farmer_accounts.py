"""Phone-number farmer account tracer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class FarmerConsentState(str, Enum):
    PRIVATE = "private"
    AGENCY_MONITORING = "agency_monitoring"
    RESEARCH_AND_MONITORING = "research_and_monitoring"


@dataclass(frozen=True)
class FarmerAccount:
    """Farmer identity used by downstream cattle and detection APIs."""

    id: str
    phone_number: str
    name: str
    jurisdiction_id: str
    consent_state: FarmerConsentState


class FarmerAccountStore:
    """In-memory account store for tracer implementation."""

    def __init__(self) -> None:
        self._accounts_by_phone: dict[str, FarmerAccount] = {}
        self._next_id = 1

    def upsert_by_phone(
        self,
        *,
        phone_number: str,
        name: str,
        jurisdiction_id: str,
        consent_state: FarmerConsentState = FarmerConsentState.PRIVATE,
    ) -> tuple[FarmerAccount, bool]:
        normalized_phone = normalize_phone_number(phone_number)
        existing = self._accounts_by_phone.get(normalized_phone)
        if existing is not None:
            return existing, False

        account = FarmerAccount(
            id=f"farmer-{self._next_id}",
            phone_number=normalized_phone,
            name=name,
            jurisdiction_id=jurisdiction_id,
            consent_state=consent_state,
        )
        self._next_id += 1
        self._accounts_by_phone[normalized_phone] = account
        return account, True

    def get_by_id(self, farmer_id: str) -> FarmerAccount | None:
        for account in self._accounts_by_phone.values():
            if account.id == farmer_id:
                return account
        return None

    def all_by_id(self) -> dict[str, FarmerAccount]:
        return {account.id: account for account in self._accounts_by_phone.values()}

    def clear(self) -> None:
        self._accounts_by_phone.clear()
        self._next_id = 1


def normalize_phone_number(phone_number: str) -> str:
    """Normalize Indonesian phone number identity to +62 format."""

    digits = re.sub(r"\D", "", phone_number)
    if digits.startswith("62"):
        return f"+{digits}"
    if digits.startswith("0"):
        return f"+62{digits[1:]}"
    if digits.startswith("8"):
        return f"+62{digits}"
    raise ValueError("Phone number must be Indonesian +62, 62, 0, or 8 prefix")


farmer_account_store = FarmerAccountStore()
