"""Surface-specific account auth for farmer mobile and agency web."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from config import settings
from jose import JWTError, jwt
from passlib.context import CryptContext  # type: ignore[import-not-found]
from sqlalchemy import select  # type: ignore[import-not-found]

from api.database import SessionLocal, create_all_tables
from api.db_models import AccountModel

DEFAULT_AGENCY_ADMIN_ID = "a1000000-0000-4000-8000-000000000001"
DEFAULT_AGENCY_OFFICER_ID = "a2000000-0000-4000-8000-000000000002"
DEFAULT_AGENCY_VIEWER_ID = "a3000000-0000-4000-8000-000000000003"
DEFAULT_FARMER_DEMO_ID = "f1000000-0000-4000-8000-000000000001"
DEFAULT_FARMER_DEMO_TWO_ID = "f2000000-0000-4000-8000-000000000002"

TOKEN_ALGORITHM = "HS256"
password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


@dataclass(frozen=True)
class SurfaceAccount:
    id: str
    account_type: str
    email: str
    name: str
    jurisdiction_id: str
    password_hash: str
    is_active: bool = True
    archived_at: str | None = None
    address: str | None = None


class SurfaceAccountStore:
    """Account store keyed separately by surface account type and email."""

    def __init__(self) -> None:
        create_all_tables()

    def register_farmer(
        self,
        *,
        email: str,
        password: str,
        name: str,
        jurisdiction_id: str,
        address: str | None = None,
        phone_number: str | None = None,
        account_id: str | None = None,
    ) -> SurfaceAccount:
        return self._create(
            account_type="farmer",
            email=email,
            password=password,
            name=name,
            jurisdiction_id=jurisdiction_id,
            address=address,
            account_id=account_id,
            phone_number=phone_number,
        )

    def seed_farmer(
        self,
        *,
        email: str,
        password: str,
        name: str,
        jurisdiction_id: str,
        address: str | None = None,
        account_id: str | None = None,
        phone_number: str | None = None,
    ) -> SurfaceAccount:
        from api.db_models import FarmerAccountModel
        from api.farmer_accounts import FarmerConsentState

        existing = self.get(account_type="farmer", email=email)
        if existing is not None:
            if account_id is not None and existing.id != account_id:
                with SessionLocal() as session:
                    old_farmer = session.get(FarmerAccountModel, existing.id)
                    if old_farmer is not None:
                        session.delete(old_farmer)
                    old_account = session.get(AccountModel, existing.id)
                    if old_account is not None:
                        session.delete(old_account)
                    session.commit()
            else:
                with SessionLocal() as session:
                    farmer_row = session.get(FarmerAccountModel, existing.id)
                    if farmer_row is None:
                        session.add(
                            FarmerAccountModel(
                                id=existing.id,
                                phone_number=phone_number,
                                name=existing.name,
                                address=existing.address,
                                jurisdiction_id=existing.jurisdiction_id,
                                consent_state=FarmerConsentState.AGENCY_MONITORING.value,
                                scan_image_storage_notice_accepted=False,
                            )
                        )
                        session.commit()
                return existing
        return self._create(
            account_type="farmer",
            email=email,
            password=password,
            name=name,
            jurisdiction_id=jurisdiction_id,
            address=address,
            account_id=account_id,
            phone_number=phone_number,
        )

    def seed_agency(
        self,
        *,
        email: str,
        password: str,
        name: str,
        jurisdiction_id: str,
        account_id: str | None = None,
    ) -> SurfaceAccount:
        from api.db_models import AgencyUserModel

        existing = self.get(account_type="agency", email=email)
        if existing is not None:
            if account_id is not None and existing.id != account_id:
                with SessionLocal() as session:
                    old_agency_user = session.get(AgencyUserModel, existing.id)
                    if old_agency_user is not None:
                        session.delete(old_agency_user)
                    old_account = session.get(AccountModel, existing.id)
                    if old_account is not None:
                        session.delete(old_account)
                    session.commit()
            else:
                return existing
        return self._create(
            account_type="agency",
            email=email,
            password=password,
            name=name,
            jurisdiction_id=jurisdiction_id,
            account_id=account_id,
        )

    def register_agency(
        self,
        *,
        email: str,
        password: str = "agency-password",
        name: str,
        jurisdiction_id: str,
        account_id: str | None = None,
    ) -> SurfaceAccount:
        return self._create(
            account_type="agency",
            email=email,
            password=password,
            name=name,
            jurisdiction_id=jurisdiction_id,
            account_id=account_id,
        )

    def _create(
        self,
        *,
        account_type: str,
        email: str,
        password: str,
        name: str,
        jurisdiction_id: str,
        address: str | None = None,
        account_id: str | None = None,
        phone_number: str | None = None,
    ) -> SurfaceAccount:
        normalized_email = normalize_email(email)
        if self.get(account_type=account_type, email=normalized_email) is not None:
            raise ValueError(f"{account_type} account already exists")
        with SessionLocal() as session:
            if account_id is None or session.get(AccountModel, account_id) is not None:
                account_id = str(uuid.uuid4())
                while session.get(AccountModel, account_id) is not None:
                    account_id = str(uuid.uuid4())
            account = SurfaceAccount(
                id=account_id,
                account_type=account_type,
                email=normalized_email,
                name=name,
                jurisdiction_id=jurisdiction_id,
                address=address,
                password_hash=hash_password(password),
            )
            session.add(AccountModel(**account.__dict__))
            if account_type == "farmer":
                from api.db_models import FarmerAccountModel
                from api.farmer_accounts import FarmerConsentState

                if session.get(FarmerAccountModel, account_id) is None:
                    session.add(
                        FarmerAccountModel(
                            id=account_id,
                            phone_number=phone_number,
                            name=name,
                            address=address,
                            jurisdiction_id=jurisdiction_id,
                            consent_state=FarmerConsentState.AGENCY_MONITORING.value,
                            scan_image_storage_notice_accepted=False,
                        )
                    )
            session.commit()
            return account

    def get(self, *, account_type: str, email: str) -> SurfaceAccount | None:
        with SessionLocal() as session:
            row = session.scalar(
                select(AccountModel).where(
                    AccountModel.account_type == account_type,
                    AccountModel.email == normalize_email(email),
                )
            )
            return _account_from_row(row) if row is not None else None

    def get_by_id(self, *, account_type: str, account_id: str) -> SurfaceAccount | None:
        with SessionLocal() as session:
            row = session.get(AccountModel, account_id)
            if row is None or row.account_type != account_type:
                return None
            return _account_from_row(row)

    def authenticate(
        self, *, account_type: str, email: str, password: str
    ) -> SurfaceAccount | None:
        account = self.get(account_type=account_type, email=email)
        if account is None:
            return None
        if not account.is_active:
            raise ValueError(f"{account_type} account is archived")
        if not verify_password(password, account.password_hash):
            return None
        return account

    def update_farmer_profile(
        self,
        *,
        account_id: str,
        name: str,
        jurisdiction_id: str,
        address: str | None = None,
    ) -> SurfaceAccount:
        from api.db_models import FarmerAccountModel

        with SessionLocal() as session:
            row = session.get(AccountModel, account_id)
            if row is None or row.account_type != "farmer" or not row.is_active:
                raise ValueError("farmer account not found")
            row.name = name
            row.jurisdiction_id = jurisdiction_id
            if address is not None:
                row.address = address

            farmer_row = session.get(FarmerAccountModel, account_id)
            if farmer_row is not None:
                farmer_row.name = name
                farmer_row.jurisdiction_id = jurisdiction_id
                if address is not None:
                    farmer_row.address = address
            session.commit()
            session.refresh(row)
            return _account_from_row(row)

    def update_profile(self, *, account_id: str, name: str) -> SurfaceAccount:
        with SessionLocal() as session:
            row = session.get(AccountModel, account_id)
            if row is None or not row.is_active:
                raise ValueError("account not found")
            row.name = name
            session.commit()
            session.refresh(row)
            return _account_from_row(row)

    def change_password(
        self, *, account_id: str, current_password: str, new_password: str
    ) -> SurfaceAccount:
        with SessionLocal() as session:
            row = session.get(AccountModel, account_id)
            if row is None or not row.is_active:
                raise ValueError("account not found")
            if not verify_password(current_password, row.password_hash):
                raise ValueError("current password is incorrect")
            row.password_hash = hash_password(new_password)
            session.commit()
            session.refresh(row)
            return _account_from_row(row)

    def reset_password(
        self, *, account_id: str, new_password: str = "agency-password"
    ) -> SurfaceAccount:
        with SessionLocal() as session:
            row = session.get(AccountModel, account_id)
            if row is None or not row.is_active:
                raise ValueError("account not found")
            row.password_hash = hash_password(new_password)
            session.commit()
            session.refresh(row)
            return _account_from_row(row)

    def archive_farmer(
        self, *, account_id: str, password: str | None = None
    ) -> SurfaceAccount:
        with SessionLocal() as session:
            row = session.get(AccountModel, account_id)
            if row is None or row.account_type != "farmer" or not row.is_active:
                raise ValueError("farmer account not found")
            if password is None or not verify_password(password, row.password_hash):
                raise ValueError("password confirmation failed")
            row.is_active = False
            row.archived_at = datetime.now(timezone.utc).isoformat()
            session.commit()
            session.refresh(row)
            return _account_from_row(row)

    def clear(self) -> None:
        from api.db_models import AgencyUserModel, FarmerAccountModel

        with SessionLocal() as session:
            session.query(AgencyUserModel).delete()
            session.query(FarmerAccountModel).delete()
            session.query(AccountModel).delete()
            session.commit()


def seed_default_farmer_accounts() -> None:
    from config import settings

    from api.db_models import FarmerAccountModel
    from api.farmer_accounts import FarmerConsentState

    # Ensure any existing active farmer account has a FarmerAccountModel record
    with SessionLocal() as session:
        farmers_in_accounts = (
            session.query(AccountModel)
            .filter(AccountModel.account_type == "farmer")
            .all()
        )
        for acc in farmers_in_accounts:
            if session.get(FarmerAccountModel, acc.id) is None:
                session.add(
                    FarmerAccountModel(
                        id=acc.id,
                        phone_number=None,
                        name=acc.name,
                        address=acc.address,
                        jurisdiction_id=acc.jurisdiction_id,
                        consent_state=FarmerConsentState.AGENCY_MONITORING.value,
                        scan_image_storage_notice_accepted=False,
                    )
                )
        session.commit()

    # Farmers only seed in staging/development, never production.
    if settings.resolved_seed_tier == "production":
        return

    # Clean up obsolete legacy farmer IDs if they exist
    with SessionLocal() as session:
        for legacy_id in ("farmer-1", "farmer-2", "farmer-3", "farmer-4", "farmer-5"):
            acc = session.get(AccountModel, legacy_id)
            if acc is not None and acc.email in (
                "farmer@example.com",
                "farmer2@example.com",
            ):
                old_f = session.get(FarmerAccountModel, legacy_id)
                if old_f is not None:
                    session.delete(old_f)
                session.delete(acc)
        session.commit()

    surface_account_store.seed_farmer(
        email="farmer@example.com",
        password="strong-password",
        name="Demo Farmer",
        jurisdiction_id="tembalang",
        address="Jl. Ngesrep Timur V No. 12, Tembalang",
        account_id=DEFAULT_FARMER_DEMO_ID,
    )
    surface_account_store.seed_farmer(
        email="farmer2@example.com",
        password="strong-password",
        name="Demo Farmer Two",
        jurisdiction_id="banyumanik",
        address="Jl. Banyumanik Raya No. 22, Banyumanik",
        account_id=DEFAULT_FARMER_DEMO_TWO_ID,
    )


def seed_default_agency_accounts() -> None:
    from config import settings

    from api.authorization import AgencyRole, _agency_user_store, refresh_agency_users
    from api.db_models import AgencyUserModel

    # Clean up obsolete legacy central-java-admin or legacy seeded accounts if present
    with SessionLocal() as session:
        for legacy_id in (
            "central-java-admin",
            "semarang-officer",
            "tembalang-viewer",
            "agency-1",
        ):
            legacy_u = session.get(AgencyUserModel, legacy_id)
            if legacy_u is not None:
                session.delete(legacy_u)
            legacy_a = session.get(AccountModel, legacy_id)
            if legacy_a is not None:
                session.delete(legacy_a)
        session.commit()

    # Master admin is always seeded, credentials from env in every tier.
    admin = surface_account_store.seed_agency(
        email=settings.master_admin_email,
        password=settings.master_admin_password,
        name=settings.master_admin_name,
        jurisdiction_id=settings.master_admin_jurisdiction,
        account_id=DEFAULT_AGENCY_ADMIN_ID,
    )
    _agency_user_store.ensure_exists(
        admin.id, AgencyRole.ADMIN.value, settings.master_admin_jurisdiction
    )

    # District officer and Viewer only seed in staging/development, never production.
    if settings.resolved_seed_tier != "production":
        officer = surface_account_store.seed_agency(
            email="semarang-officer@sapisehat.test",
            password="agency-password",
            name="Semarang Officer",
            jurisdiction_id="semarang-city",
            account_id=DEFAULT_AGENCY_OFFICER_ID,
        )
        _agency_user_store.ensure_exists(
            officer.id, AgencyRole.DISTRICT_OFFICER.value, "semarang-city"
        )

        viewer = surface_account_store.seed_agency(
            email="tembalang-viewer@sapisehat.test",
            password="agency-password",
            name="Tembalang Viewer",
            jurisdiction_id="tembalang",
            account_id=DEFAULT_AGENCY_VIEWER_ID,
        )
        _agency_user_store.ensure_exists(
            viewer.id, AgencyRole.VIEWER.value, "tembalang"
        )

    refresh_agency_users()


def _account_from_row(row: AccountModel) -> SurfaceAccount:
    return SurfaceAccount(
        id=row.id,
        account_type=row.account_type,
        email=row.email,
        name=row.name,
        address=getattr(row, "address", None),
        jurisdiction_id=row.jurisdiction_id,
        password_hash=row.password_hash,
        is_active=getattr(row, "is_active", True),
        archived_at=getattr(row, "archived_at", None),
    )


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized:
        raise ValueError("email must be valid")
    return normalized


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if len(password) < 8:
        return False
    return password_context.verify(password, password_hash)


def issue_token(account: SurfaceAccount) -> str:
    payload = {
        "sub": account.id,
        "account_type": account.account_type,
        "email": account.email,
        "iat": int(time.time()),
    }
    try:
        return jwt.encode(payload, settings.jwt_secret, algorithm=TOKEN_ALGORITHM)
    except Exception as exc:
        raise ValueError("could not issue token") from exc


def read_token(token: str) -> dict[str, object]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[TOKEN_ALGORITHM])
    except JWTError as exc:
        raise ValueError("invalid token") from exc


surface_account_store = SurfaceAccountStore()
