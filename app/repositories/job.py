from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import Job


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_announcement_and_hash(self, announcement_id: int, record_hash: str) -> Job | None:
        stmt = select(Job).where(
            Job.announcement_id == announcement_id,
            Job.record_hash == record_hash,
        )
        return self.session.scalars(stmt).first()

    def upsert(self, announcement_id: int, fields: dict, record_hash: str) -> Job:
        existing = self.get_by_announcement_and_hash(announcement_id, record_hash)
        now = datetime.now()
        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
            existing.record_hash = record_hash
            existing.updated_at = now
            return existing

        row = Job(announcement_id=announcement_id, record_hash=record_hash, **fields)
        self.session.add(row)
        self.session.flush()
        return row

    def list_with_announcements(self) -> list[Job]:
        stmt = select(Job).options(joinedload(Job.announcement))
        return list(self.session.scalars(stmt).all())

    def list_created_since(self, since: datetime) -> list[Job]:
        stmt = (
            select(Job)
            .options(joinedload(Job.announcement))
            .where(Job.created_at >= since)
        )
        return list(self.session.scalars(stmt).all())
