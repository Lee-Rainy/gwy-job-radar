from datetime import datetime

from app.config import get_settings
from app.database import Job


def city_matches(job: Job, cities: list[str] | None = None) -> bool:
    targets = cities or get_settings().target_cities
    if not targets:
        return True
    haystack = " ".join(
        filter(
            None,
            [job.city, job.district, job.work_location, job.organization],
        )
    )
    return any(city in haystack for city in targets)


def is_registration_open(job: Job, now: datetime | None = None) -> bool:
    reference = now or datetime.now()
    if job.registration_deadline and job.registration_deadline < reference:
        return False
    if job.registration_start and job.registration_start > reference:
        return False
    return True


def filter_jobs_for_digest(
    jobs: list[Job],
    *,
    cities: list[str] | None = None,
    include_open_only: bool = False,
    now: datetime | None = None,
) -> list[Job]:
    result: list[Job] = []
    for job in jobs:
        if not city_matches(job, cities):
            continue
        if include_open_only and not is_registration_open(job, now):
            continue
        result.append(job)
    return result


def announcement_reference_time(job: Job) -> datetime:
    """新发布判定：优先公告发布时间，其次首次入库时间，最后岗位 created_at。"""
    ann = job.announcement
    if ann is not None:
        if ann.published_at is not None:
            return ann.published_at
        if ann.first_seen_at is not None:
            return ann.first_seen_at
    return job.created_at


def split_new_and_open(
    jobs: list[Job],
    *,
    new_since: datetime,
    cities: list[str] | None = None,
    now: datetime | None = None,
) -> tuple[list[Job], list[Job]]:
    scoped = filter_jobs_for_digest(jobs, cities=cities, include_open_only=False, now=now)
    new_jobs = [j for j in scoped if announcement_reference_time(j) >= new_since]
    open_jobs = [j for j in scoped if is_registration_open(j, now)]
    return new_jobs, open_jobs
