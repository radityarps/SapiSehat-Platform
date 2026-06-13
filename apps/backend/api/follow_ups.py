"""Agency follow-up status persistence."""

from __future__ import annotations

from dataclasses import dataclass

from api.database import SessionLocal, create_all_tables
from api.db_models import FollowUpModel


@dataclass(frozen=True)
class FollowUp:
    id: str
    farmer_id: str
    cattle_id: str | None
    status: str
    public_message: str
    internal_notes: str


class FollowUpStore:
    def __init__(self) -> None:
        create_all_tables()

    def create(
        self,
        *,
        farmer_id: str,
        cattle_id: str | None,
        status: str,
        public_message: str,
        internal_notes: str,
    ) -> FollowUp:
        with SessionLocal() as session:
            next_id = session.query(FollowUpModel).count() + 1
            follow_up = FollowUp(
                id=f"follow-up-{next_id}",
                farmer_id=farmer_id,
                cattle_id=cattle_id,
                status=status,
                public_message=public_message,
                internal_notes=internal_notes,
            )
            session.add(FollowUpModel(**follow_up.__dict__))
            session.commit()
            return follow_up

    def list_by_farmer(self, farmer_id: str) -> list[FollowUp]:
        with SessionLocal() as session:
            rows = (
                session.query(FollowUpModel)
                .filter_by(farmer_id=farmer_id)
                .order_by(FollowUpModel.id)
                .all()
            )
            return [_follow_up_from_row(row) for row in rows]

    def list_all(self) -> list[FollowUp]:
        with SessionLocal() as session:
            rows = session.query(FollowUpModel).order_by(FollowUpModel.id).all()
            return [_follow_up_from_row(row) for row in rows]

    def get_by_id(self, follow_up_id: str) -> FollowUp | None:
        with SessionLocal() as session:
            row = session.get(FollowUpModel, follow_up_id)
            return _follow_up_from_row(row) if row is not None else None

    def update(
        self,
        follow_up_id: str,
        *,
        status: str | None = None,
        public_message: str | None = None,
        internal_notes: str | None = None,
    ) -> FollowUp | None:
        with SessionLocal() as session:
            row = session.get(FollowUpModel, follow_up_id)
            if row is None:
                return None
            if status is not None:
                row.status = status
            if public_message is not None:
                row.public_message = public_message
            if internal_notes is not None:
                row.internal_notes = internal_notes
            session.commit()
            session.refresh(row)
            return _follow_up_from_row(row)

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(FollowUpModel).delete()
            session.commit()


def _follow_up_from_row(row: FollowUpModel) -> FollowUp:
    return FollowUp(
        id=row.id,
        farmer_id=row.farmer_id,
        cattle_id=row.cattle_id,
        status=row.status,
        public_message=row.public_message,
        internal_notes=row.internal_notes,
    )


follow_up_store = FollowUpStore()
