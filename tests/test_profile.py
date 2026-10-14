from app.config import Settings
from app.database import Announcement, Job
from app.services.profile import job_matches_profile, profile_from_settings


def _job(candidate_type: str | None = None, major: str | None = None, **kwargs: object) -> Job:
    ann = Announcement(
        id=1,
        source_id="t",
        title="t",
        source_url="http://x",
        canonical_url="http://x",
        announcement_type="事业单位",
        content_hash="h",
        status="正常",
    )
    defaults = {
        "id": 1,
        "announcement_id": 1,
        "job_title": "综合管理岗",
        "job_type": "public_institution",
        "province": "广东",
        "record_hash": "r",
        "education": "本科及以上",
        "candidate_type": candidate_type,
        "major": major,
        "announcement": ann,
    }
    defaults.update(kwargs)
    return Job(**defaults)


def test_social_excludes_fresh_only() -> None:
    profile = profile_from_settings(
        Settings(
            profile_is_fresh_graduate=False,
            profile_major="信息管理与信息系统",
        )
    )
    job = _job(candidate_type="仅限应届毕业生报考", major="信息管理")
    assert job_matches_profile(job, profile) is False


def test_fresh_graduate_accepts_yingjie() -> None:
    profile = profile_from_settings(
        Settings(
            profile_is_fresh_graduate=True,
            profile_major="信息管理与信息系统",
        )
    )
    job = _job(candidate_type="应届毕业生", major="信息管理")
    assert job_matches_profile(job, profile) is True
