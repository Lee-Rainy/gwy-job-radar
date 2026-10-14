from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import DELIVERY_STATUS_FAILED, DELIVERY_STATUS_PENDING, DELIVERY_STATUS_SENT
from app.database import EmailDelivery


class DeliveryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_existing(
        self,
        digest_date: date,
        period: str,
        recipient: str,
        content_hash: str,
    ) -> EmailDelivery | None:
        stmt = select(EmailDelivery).where(
            EmailDelivery.digest_date == digest_date,
            EmailDelivery.period == period,
            EmailDelivery.recipient == recipient,
            EmailDelivery.content_hash == content_hash,
        )
        return self.session.scalars(stmt).first()

    def create_pending(
        self,
        *,
        digest_date: date,
        period: str,
        recipient: str,
        content_hash: str,
    ) -> EmailDelivery:
        existing = self.get_existing(digest_date, period, recipient, content_hash)
        if existing:
            return existing
        row = EmailDelivery(
            digest_date=digest_date,
            period=period,
            recipient=recipient,
            content_hash=content_hash,
            status=DELIVERY_STATUS_PENDING,
            attempts=0,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def mark_sent(self, delivery: EmailDelivery) -> None:
        delivery.status = DELIVERY_STATUS_SENT
        delivery.attempts += 1
        delivery.sent_at = datetime.now()
        delivery.error_message = None

    def mark_failed(self, delivery: EmailDelivery, message: str) -> None:
        delivery.status = DELIVERY_STATUS_FAILED
        delivery.attempts += 1
        delivery.error_message = message[:2000]
