"""Notification persistence and creation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from api.database import SessionLocal, create_all_tables
from api.db_models import NotificationModel


@dataclass(frozen=True)
class Notification:
    id: str
    account_id: str
    account_type: str
    title: str
    body: str
    link: str | None
    is_read: bool
    created_at: str


class NotificationStore:
    def __init__(self) -> None:
        create_all_tables()

    def create(
        self,
        *,
        account_id: str,
        account_type: str,
        title: str,
        body: str,
        link: str | None = None,
        created_at: str | None = None,
    ) -> Notification:
        with SessionLocal() as session:
            next_id = session.query(NotificationModel).count() + 1
            notification = Notification(
                id=f"notification-{next_id}",
                account_id=account_id,
                account_type=account_type,
                title=title,
                body=body,
                link=link,
                is_read=False,
                created_at=created_at or "",
            )
            session.add(NotificationModel(**notification.__dict__))
            session.commit()
            return notification

    def list_for_account(
        self,
        account_id: str,
        account_type: str,
        *,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        with SessionLocal() as session:
            query = session.query(NotificationModel).filter_by(
                account_id=account_id, account_type=account_type
            )
            if unread_only:
                query = query.filter_by(is_read=False)
            rows = (
                query.order_by(NotificationModel.created_at.desc())
                .limit(limit)
                .all()
            )
            return [_notification_from_row(row) for row in rows]

    def get_by_id(self, notification_id: str) -> Notification | None:
        with SessionLocal() as session:
            row = session.get(NotificationModel, notification_id)
            return _notification_from_row(row) if row is not None else None

    def mark_read(
        self, notification_id: str, account_id: str, account_type: str
    ) -> Notification | None:
        with SessionLocal() as session:
            row = (
                session.query(NotificationModel)
                .filter_by(
                    id=notification_id,
                    account_id=account_id,
                    account_type=account_type,
                )
                .first()
            )
            if row is None:
                return None
            row.is_read = True
            session.commit()
            session.refresh(row)
            return _notification_from_row(row)

    def mark_all_read(self, account_id: str, account_type: str) -> int:
        with SessionLocal() as session:
            count = (
                session.query(NotificationModel)
                .filter_by(account_id=account_id, account_type=account_type, is_read=False)
                .update({"is_read": True})
            )
            session.commit()
            return count

    def unread_count(self, account_id: str, account_type: str) -> int:
        with SessionLocal() as session:
            return (
                session.query(NotificationModel)
                .filter_by(account_id=account_id, account_type=account_type, is_read=False)
                .count()
            )

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(NotificationModel).delete()
            session.commit()


def _notification_from_row(row: NotificationModel) -> Notification:
    return Notification(
        id=row.id,
        account_id=row.account_id,
        account_type=row.account_type,
        title=row.title,
        body=row.body,
        link=row.link,
        is_read=row.is_read,
        created_at=row.created_at,
    )


notification_store = NotificationStore()
