from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.database import Job
from app.services.deduplicate import digest_content_hash
from app.services.profile import UserProfile


def _template_env() -> Environment:
    templates_dir = Path(__file__).resolve().parent.parent / "templates"
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def build_digest_context(
    *,
    digest_date: date,
    period: str,
    new_jobs: list[Job],
    open_jobs: list[Job],
    profile: UserProfile | None = None,
) -> dict:
    return {
        "digest_date": digest_date.isoformat(),
        "period": period,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "new_jobs": [_job_to_dict(j) for j in new_jobs],
        "open_jobs": [_job_to_dict(j) for j in open_jobs],
        "new_count": len(new_jobs),
        "open_count": len(open_jobs),
        "profile": profile,
    }


def render_digest_html(context: dict) -> str:
    env = _template_env()
    template = env.get_template("daily_digest.html")
    return template.render(**context)


def compute_digest_hash(context: dict) -> str:
    return digest_content_hash(
        {
            "new": [j["record_hash"] for j in context["new_jobs"]],
            "open": [j["record_hash"] for j in context["open_jobs"]],
        }
    )


def _job_to_dict(job: Job) -> dict:
    return {
        "job_title": job.job_title,
        "organization": job.organization,
        "city": job.city,
        "district": job.district,
        "job_type": job.job_type,
        "registration_deadline": _fmt(job.registration_deadline),
        "education": job.education,
        "major": job.major,
        "announcement_title": job.announcement.title if job.announcement else None,
        "source_url": job.announcement.source_url if job.announcement else None,
        "record_hash": job.record_hash,
    }


def _fmt(dt: datetime | None) -> str | None:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else None
