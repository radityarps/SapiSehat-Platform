"""Audit log persistence for sensitive backend actions."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from api.database import SessionLocal, create_all_tables
from api.db_models import AuditLogModel

@dataclass(frozen=True)
class AuditLog:
    id: str
    actor_type: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    metadata_json: dict
    created_at: str

class AuditLogStore:
    def __init__(self) -> None:
        create_all_tables()

    def record(self, *, actor_type: str, actor_id: str, action: str, resource_type: str, resource_id: str, metadata_json: dict | None = None) -> AuditLog:
        event = AuditLog(
            id=f"audit-{uuid4().hex}",
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata_json or {},
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with SessionLocal() as session:
            session.add(AuditLogModel(**event.__dict__))
            session.commit()
        return event

    def list_by_action(self, action: str) -> list[AuditLog]:
        with SessionLocal() as session:
            rows = session.query(AuditLogModel).filter(AuditLogModel.action == action).order_by(AuditLogModel.created_at).all()
            return [_from_row(row) for row in rows]

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(AuditLogModel).delete()
            session.commit()

def _from_row(row: AuditLogModel) -> AuditLog:
    return AuditLog(
        id=row.id,
        actor_type=row.actor_type,
        actor_id=row.actor_id,
        action=row.action,
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        metadata_json=row.metadata_json,
        created_at=row.created_at,
    )

audit_log_store = AuditLogStore()
