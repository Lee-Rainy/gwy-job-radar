import asyncio
import json
import logging
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.collectors import collectors_for_run
from app.collectors.base import RawAnnouncement
from app.config import (
    ANNOUNCEMENT_STATUS_PARSE_FAILED,
    DELIVERY_PERIOD_EVENING,
    DELIVERY_PERIOD_MORNING,
    DELIVERY_STATUS_SENT,
    get_settings,
)
from app.database import Job, get_session_factory
from app.parsers.attachments import parse_attachment_rows
from app.parsers.html_parser import extract_text_summary, parse_html_job_table
from app.repositories import AnnouncementRepository, DeliveryRepository, JobRepository
from app.services.deduplicate import content_hash_from_text, record_hash_from_job
from app.services.digest import build_digest_context, compute_digest_hash, render_digest_html
from app.services.mailer import send_html_email
from app.services.matcher import is_registration_open, split_new_and_open
from app.services.normalize import infer_job_type, normalize_job_row
from app.services.profile import get_user_profile, job_matches_profile

logger = logging.getLogger(__name__)


async def run_collectors(source_ids: list[str] | None = None) -> None:
    settings = get_settings()
    session_factory = get_session_factory()
    errors: list[str] = []
    selected = collectors_for_run(source_ids or settings.collector_sources or None)

    for collector_cls in selected:
        async with collector_cls() as collector:
            result = await collector.collect()
            errors.extend(result.errors)
            with session_factory() as session:
                _persist_announcements(session, result.announcements)
                session.commit()
        await asyncio.sleep(settings.collector_rate_limit_seconds)

    for err in errors:
        logger.warning("collector error: %s", err)


def _persist_announcements(session: Session, items: list[RawAnnouncement]) -> None:
    ann_repo = AnnouncementRepository(session)
    job_repo = JobRepository(session)

    for item in items:
        canonical = item.canonical_url or item.source_url
        summary = item.text_summary or (
            extract_text_summary(item.html_body) if item.html_body else item.title
        )
        content_hash = content_hash_from_text(summary)

        try:
            announcement = ann_repo.upsert(
                source_id=item.source_id,
                title=item.title,
                source_url=item.source_url,
                canonical_url=canonical,
                published_at=item.published_at,
                announcement_type=item.announcement_type,
                content_hash=content_hash,
            )
            job_type = infer_job_type(item.announcement_type, item.metadata)
            rows = parse_html_job_table(item.html_body) if item.html_body else []
            for attachment in item.attachments:
                if attachment.url.lower().endswith((".xls", ".xlsx")):
                    if "岗位" in (attachment.filename or "") or "职位" in (attachment.filename or ""):
                        rows.extend(parse_attachment_rows(attachment.url, attachment.filename))
            if not rows:
                rows.extend(_fallback_rows_from_title(item))
            ann_start, ann_end = _registration_from_metadata(item.metadata)
            conditions = item.metadata.get("conditions_text")
            for row in rows:
                fields = normalize_job_row(row, job_type=job_type)
                fields["city"] = fields.get("city") or "广州"
                _apply_announcement_schedule(fields, ann_start, ann_end, conditions)
                rhash = record_hash_from_job(fields)
                job_repo.upsert(announcement.id, fields, rhash)
        except Exception as exc:  # noqa: BLE001
            logger.exception("parse failed %s: %s", item.source_url, exc)
            ann_repo.upsert(
                source_id=item.source_id,
                title=item.title,
                source_url=item.source_url,
                canonical_url=canonical,
                published_at=item.published_at,
                announcement_type=item.announcement_type,
                content_hash=content_hash,
                status=ANNOUNCEMENT_STATUS_PARSE_FAILED,
            )


def _registration_from_metadata(metadata: dict) -> tuple[datetime | None, datetime | None]:
    start = _parse_metadata_datetime(metadata.get("registration_start"))
    end = _parse_metadata_datetime(metadata.get("registration_deadline"))
    return start, end


def _parse_metadata_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _apply_announcement_schedule(
    fields: dict,
    ann_start: datetime | None,
    ann_end: datetime | None,
    conditions: str | None,
) -> None:
    if not fields.get("registration_start") and ann_start:
        fields["registration_start"] = ann_start
    if not fields.get("registration_deadline") and ann_end:
        fields["registration_deadline"] = ann_end
    if conditions:
        raw = fields.get("raw_data")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw}
        if not isinstance(payload, dict):
            payload = {}
        payload["conditions_text"] = conditions
        fields["raw_data"] = json.dumps(payload, ensure_ascii=False)
        haystack = conditions
        if not fields.get("education") and "本科" in haystack:
            fields["education"] = "本科"
        if not fields.get("candidate_type"):
            if "社会" in haystack:
                fields["candidate_type"] = "社会人员"
            elif "应届" in haystack:
                fields["candidate_type"] = "应届毕业生"


def _fallback_rows_from_title(item: RawAnnouncement):
    from app.parsers.html_parser import ParsedJobRow

    return [
        ParsedJobRow(
            job_code=None,
            organization="广州市人社局及相关单位",
            job_title=item.title,
            city="广州",
            district=None,
            work_location="广州",
            recruitment_count=None,
            education=None,
            degree=None,
            major=None,
            age_requirement=None,
            candidate_type=None,
            registration_start=None,
            registration_deadline=None,
            raw={"announcement_title": item.title, "source_url": item.source_url},
        )
    ]


def send_digest_for_period(period: str, *, profile_only: bool = True) -> None:
    settings = get_settings()
    session_factory = get_session_factory()
    digest_date = date.today()
    since = _window_start_for_period(period)
    profile = get_user_profile()

    with session_factory() as session:
        job_repo = JobRepository(session)
        delivery_repo = DeliveryRepository(session)
        all_jobs = job_repo.list_with_announcements()
        new_jobs, open_jobs = split_new_and_open(
            all_jobs,
            new_since=since,
            cities=settings.target_cities,
        )
        if profile_only:
            new_jobs = [j for j in new_jobs if job_matches_profile(j, profile)]
            open_jobs = [j for j in open_jobs if job_matches_profile(j, profile)]
            if not open_jobs:
                open_jobs = [
                    j
                    for j in all_jobs
                    if job_matches_profile(j, profile) and is_registration_open(j)
                ]

        context = build_digest_context(
            digest_date=digest_date,
            period=period,
            new_jobs=new_jobs,
            open_jobs=open_jobs,
            profile=profile,
        )
        content_hash = compute_digest_hash(context)
        html = render_digest_html(context)
        city_label = "·".join(settings.target_cities[:3]) if settings.target_cities else "广东"
        subject = (
            f"【考公雷达·{city_label}{settings.crawl_target_year}】{digest_date.isoformat()} "
            f"{'早报' if period == DELIVERY_PERIOD_MORNING else '晚报'}"
            f" 新{len(new_jobs)}·开放{len(open_jobs)}"
        )

        for recipient in settings.mail_recipients:
            delivery = delivery_repo.create_pending(
                digest_date=digest_date,
                period=period,
                recipient=recipient,
                content_hash=content_hash,
            )
            if delivery.status == DELIVERY_STATUS_SENT:
                continue
            try:
                send_html_email(subject=subject, html_body=html, recipients=[recipient])
                delivery_repo.mark_sent(delivery)
            except Exception as exc:  # noqa: BLE001
                delivery_repo.mark_failed(delivery, str(exc))
                logger.error("mail failed for %s: %s", recipient, exc)
                logger.exception("mail failed detail for %s", recipient)
        session.commit()


def _window_start_for_period(period: str) -> datetime:
    now = datetime.now()
    if period == DELIVERY_PERIOD_MORNING:
        return datetime(now.year, now.month, now.day) - timedelta(days=1, hours=12)
    return datetime(now.year, now.month, now.day)


async def run_morning_evening_job(period: str, *, source_ids: list[str] | None = None) -> None:
    await run_collectors(source_ids)
    send_digest_for_period(period)
