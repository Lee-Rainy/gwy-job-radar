from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import ANNOUNCEMENT_STATUS_ACTIVE
from app.database import Announcement


class AnnouncementRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_source_and_url(self, source_id: str, canonical_url: str) -> Announcement | None:
        stmt = select(Announcement).where(
            Announcement.source_id == source_id,
            Announcement.canonical_url == canonical_url,
        )
        return self.session.scalars(stmt).first()

    def upsert(
        self,
        *,
        source_id: str,
        title: str,
        source_url: str,
        canonical_url: str,
        published_at: datetime | None,
        announcement_type: str,
        content_hash: str,
        status: str = ANNOUNCEMENT_STATUS_ACTIVE,
    ) -> Announcement:
        existing = self.get_by_source_and_url(source_id, canonical_url)
        now = datetime.now()
        if existing:
            existing.title = title
            existing.source_url = source_url
            existing.published_at = published_at or existing.published_at
            existing.content_hash = content_hash
            existing.last_seen_at = now
            existing.status = status
            return existing

        row = Announcement(
            source_id=source_id,
            title=title,
            source_url=source_url,
            canonical_url=canonical_url,
            published_at=published_at,
            announcement_type=announcement_type,
            content_hash=content_hash,
            first_seen_at=now,
            last_seen_at=now,
            status=status,
        )
        self.session.add(row)
        self.session.flush()
        return row
