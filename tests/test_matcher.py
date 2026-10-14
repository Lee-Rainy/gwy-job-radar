from datetime import datetime, timedelta

from app.database import Announcement, Job
from app.services.matcher import city_matches, is_registration_open


def _job(**kwargs: object) -> Job:
    ann = Announcement(
        id=1,
        source_id="t",
        title="t",
        source_url="http://x",
        canonical_url="http://x",
        announcement_type="公务员",
        content_hash="h",
        status="正常",
    )
    defaults = {
        "id": 1,
        "announcement_id": 1,
        "job_title": "岗位",
        "job_type": "civil_service",
        "province": "广东",
        "record_hash": "r",
        "announcement": ann,
    }
    defaults.update(kwargs)
    return Job(**defaults)


def test_city_matches_guangzhou() -> None:
    job = _job(city="广州市天河区")
    assert city_matches(job, ["广州"])


def test_registration_open_with_deadline() -> None:
    now = datetime(2026, 10, 12, 12, 0)
    job = _job(registration_deadline=now + timedelta(days=1))
    assert is_registration_open(job, now)
