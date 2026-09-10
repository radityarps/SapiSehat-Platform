"""Phone-number farmer account tracer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from api.database import SessionLocal, create_all_tables
from api.db_models import FarmerAccountModel


class FarmerConsentState(str, Enum):
    PRIVATE = "private"
    AGENCY_MONITORING = "agency_monitoring"
    RESEARCH_AND_MONITORING = "research_and_monitoring"


@dataclass(frozen=True)
class FarmerAccount:
    """Farmer identity used by downstream cattle and detection APIs."""

    id: str
    phone_number: str | None
    name: str
    jurisdiction_id: str
    consent_state: FarmerConsentState
    scan_image_storage_notice_accepted: bool = False
    address: str | None = None


class FarmerAccountStore:
    """Farmer account store backed by platform database."""

    def __init__(self) -> None:
        create_all_tables()

    def upsert_by_phone(
        self,
        *,
        phone_number: str,
        name: str,
        jurisdiction_id: str,
        consent_state: FarmerConsentState = FarmerConsentState.PRIVATE,
        address: str | None = None,
        account_id: str | None = None,
    ) -> tuple[FarmerAccount, bool]:
        from api.db_models import AccountModel

        normalized_phone = normalize_phone_number(phone_number)
        with SessionLocal() as session:
            row = (
                session.query(FarmerAccountModel)
                .filter_by(phone_number=normalized_phone)
                .one_or_none()
            )
            if row is not None:
                return _farmer_from_row(row), False

            target_id = account_id
            if target_id is None:
                next_id = session.query(FarmerAccountModel).count() + 1
                target_id = f"farmer-{next_id}"

            if session.get(AccountModel, target_id) is None:
                session.add(
                    AccountModel(
                        id=target_id,
                        account_type="farmer",
                        email=f"{target_id}@farmer.sapisehat.id",
                        name=name,
                        jurisdiction_id=jurisdiction_id,
                        address=address,
                        password_hash="",
                    )
                )

            account = FarmerAccount(
                id=target_id,
                phone_number=normalized_phone,
                name=name,
                address=address,
                jurisdiction_id=jurisdiction_id,
                consent_state=consent_state,
            )
            session.add(
                FarmerAccountModel(
                    id=account.id,
                    phone_number=account.phone_number,
                    name=account.name,
                    address=account.address,
                    jurisdiction_id=account.jurisdiction_id,
                    consent_state=account.consent_state.value,
                    scan_image_storage_notice_accepted=account.scan_image_storage_notice_accepted,
                )
            )
            session.commit()
            return account, True

    def set_scan_image_storage_notice(
        self, farmer_id: str, *, accepted: bool
    ) -> FarmerAccount | None:
        with SessionLocal() as session:
            row = session.get(FarmerAccountModel, farmer_id)
            if row is None:
                return None
            row.scan_image_storage_notice_accepted = accepted
            session.commit()
            session.refresh(row)
            return _farmer_from_row(row)

    def get_by_id(self, farmer_id: str) -> FarmerAccount | None:
        with SessionLocal() as session:
            row = session.get(FarmerAccountModel, farmer_id)
            return None if row is None else _farmer_from_row(row)

    def update_profile(
        self,
        *,
        farmer_id: str,
        name: str,
        jurisdiction_id: str,
        address: str | None,
    ) -> FarmerAccount | None:
        with SessionLocal() as session:
            row = session.get(FarmerAccountModel, farmer_id)
            if row is None:
                return None
            row.name = name
            row.jurisdiction_id = jurisdiction_id
            row.address = address
            session.commit()
            session.refresh(row)
            return _farmer_from_row(row)

    def all_by_id(self) -> dict[str, FarmerAccount]:
        with SessionLocal() as session:
            rows = (
                session.query(FarmerAccountModel).order_by(FarmerAccountModel.id).all()
            )
            return {row.id: _farmer_from_row(row) for row in rows}

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(FarmerAccountModel).delete()
            session.commit()


def _farmer_from_row(row: FarmerAccountModel) -> FarmerAccount:
    return FarmerAccount(
        id=row.id,
        phone_number=row.phone_number,
        name=row.name,
        address=getattr(row, "address", None),
        jurisdiction_id=row.jurisdiction_id,
        consent_state=FarmerConsentState(row.consent_state),
        scan_image_storage_notice_accepted=bool(row.scan_image_storage_notice_accepted),
    )


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
