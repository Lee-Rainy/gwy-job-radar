from datetime import datetime

from app.database import Announcement, Job
from app.services.matcher import announcement_reference_time, split_new_and_open


def _job(published: datetime | None, created: datetime, first_seen: datetime | None = None) -> Job:
    ann = Announcement(
        id=1,
        source_id="t",
        title="t",
        source_url="http://x",
        canonical_url="http://x",
        announcement_type="事业单位",
        content_hash="h",
        status="正常",
        published_at=published,
        first_seen_at=first_seen or created,
    )
    return Job(
        id=1,
        announcement_id=1,
        job_title="岗",
        job_type="public_institution",
        province="广东",
        city="广州",
        record_hash="r",
        created_at=created,
        announcement=ann,
    )


def test_new_jobs_use_published_at() -> None:
    published = datetime(2026, 3, 14, 10, 0, 0)
    created = datetime(2026, 1, 1)
    job = _job(published, created)
    since = datetime(2026, 3, 14, 0, 0, 0)
    new_jobs, _ = split_new_and_open([job], new_since=since, cities=["广州"])
    assert job in new_jobs
    assert announcement_reference_time(job) == published
