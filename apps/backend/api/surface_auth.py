"""Surface-specific account auth for farmer mobile and agency web."""

from __future__ import annotations

from dataclasses import dataclass
import time
from datetime import datetime, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func, select

from api.database import SessionLocal, create_all_tables
from api.db_models import AccountModel
from config import settings


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


class SurfaceAccountStore:
    """Account store keyed separately by surface account type and email."""

    def __init__(self) -> None:
        create_all_tables()

    def register_farmer(self, *, email: str, password: str, name: str, jurisdiction_id: str) -> SurfaceAccount:
        return self._create(
            account_type="farmer",
            email=email,
            password=password,
            name=name,
            jurisdiction_id=jurisdiction_id,
        )

    def seed_farmer(self, *, email: str, password: str, name: str, jurisdiction_id: str) -> SurfaceAccount:
        existing = self.get(account_type="farmer", email=email)
        if existing is not None:
            return existing
        return self._create(
            account_type="farmer",
            email=email,
            password=password,
            name=name,
            jurisdiction_id=jurisdiction_id,
        )

    def seed_agency(self, *, email: str, password: str, name: str, jurisdiction_id: str) -> SurfaceAccount:
        existing = self.get(account_type="agency", email=email)
        if existing is not None:
            return existing
        return self._create(
            account_type="agency",
            email=email,
            password=password,
            name=name,
            jurisdiction_id=jurisdiction_id,
        )

    def _create(self, *, account_type: str, email: str, password: str, name: str, jurisdiction_id: str) -> SurfaceAccount:
        normalized_email = normalize_email(email)
        if self.get(account_type=account_type, email=normalized_email) is not None:
            raise ValueError(f"{account_type} account already exists")
        with SessionLocal() as session:
            next_num = (session.scalar(select(func.count()).select_from(AccountModel)) or 0) + 1
            account = SurfaceAccount(
                id=f"{account_type}-{next_num}",
                account_type=account_type,
                email=normalized_email,
                name=name,
                jurisdiction_id=jurisdiction_id,
                password_hash=hash_password(password),
            )
            session.add(AccountModel(**account.__dict__))
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

    def authenticate(self, *, account_type: str, email: str, password: str) -> SurfaceAccount | None:
        account = self.get(account_type=account_type, email=email)
        if account is None:
            return None
        if not account.is_active:
            raise ValueError(f"{account_type} account is archived")
        if not verify_password(password, account.password_hash):
            return None
        return account

    def update_farmer_profile(self, *, account_id: str, name: str, jurisdiction_id: str) -> SurfaceAccount:
        with SessionLocal() as session:
            row = session.get(AccountModel, account_id)
            if row is None or row.account_type != "farmer" or not row.is_active:
                raise ValueError("farmer account not found")
            row.name = name
            row.jurisdiction_id = jurisdiction_id
            session.commit()
            session.refresh(row)
            return _account_from_row(row)

    def archive_farmer(self, *, account_id: str, password: str | None = None) -> SurfaceAccount:
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

    def register_farmer_google(self, *, id_token: str, jurisdiction_id: str) -> SurfaceAccount:
        email, name = parse_google_id_token(id_token)
        existing = self.get(account_type="farmer", email=email)
        if existing is not None:
            return existing
        return self._create(
            account_type="farmer",
            email=email,
            password=f"google:{email}",
            name=name,
            jurisdiction_id=jurisdiction_id,
        )

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(AccountModel).delete()
            session.commit()


def seed_default_farmer_accounts() -> None:
    surface_account_store.seed_farmer(
        email="farmer@example.com",
        password="strong-password",
        name="Demo Farmer",
        jurisdiction_id="tembalang",
    )

def seed_default_agency_accounts() -> None:
    surface_account_store.seed_agency(
        email="semarang-officer@sapisehat.test",
        password="agency-password",
        name="Semarang Officer",
        jurisdiction_id="semarang-city",
    )


def _account_from_row(row: AccountModel) -> SurfaceAccount:
    return SurfaceAccount(
        id=row.id,
        account_type=row.account_type,
        email=row.email,
        name=row.name,
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
    return jwt.encode(payload, settings.jwt_secret, algorithm=TOKEN_ALGORITHM)


def read_token(token: str) -> dict[str, object]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[TOKEN_ALGORITHM])
    except JWTError as exc:
        raise ValueError("invalid token") from exc


surface_account_store = SurfaceAccountStore()



def parse_google_id_token(id_token: str) -> tuple[str, str]:
    """Verify a farmer Google ID token and return normalized email/name.

    Development and test keep the legacy `google:email:name` token shape so
    local contract tests and mobile prototypes can run without Google network
    calls. Production requires `GOOGLE_AUTH_ENABLED=true`, `GOOGLE_CLIENT_ID`,
    and a real Google-signed ID token.
    """
    if settings.fastapi_env in {"development", "test"} and id_token.startswith("google:"):
        return _parse_dev_google_token(id_token)

    if not settings.google_auth_enabled:
        raise ValueError("google auth is not enabled")
    if not settings.google_client_id:
        raise ValueError("google client id is not configured")

    claims = verify_google_id_token_claims(id_token)

    issuer = claims.get("iss")
    audience = claims.get("aud")
    email = claims.get("email")
    if issuer not in settings.allowed_google_id_token_issuers:
        raise ValueError("invalid google token issuer")
    if audience != settings.google_client_id:
        raise ValueError("invalid google token audience")
    if not email:
        raise ValueError("google token missing email")
    if claims.get("email_verified") is False:
        raise ValueError("google token email is not verified")

    name = claims.get("name") or email.split("@", 1)[0]
    return normalize_email(email), name


def verify_google_id_token_claims(token: str) -> dict[str, object]:
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token
    except ImportError as exc:
        raise ValueError("google-auth dependency is required for google login") from exc

    try:
        return google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except Exception as exc:  # Google verifier raises several auth/transport errors.
        raise ValueError("invalid google token") from exc


def _parse_dev_google_token(id_token: str) -> tuple[str, str]:
    parts = id_token.split(":", 2)
    if len(parts) != 3 or parts[0] != "google" or not parts[1]:
        raise ValueError("invalid google token")
    return normalize_email(parts[1]), parts[2]
