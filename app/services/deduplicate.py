import hashlib
import json
from typing import Any


def content_hash_from_text(text: str) -> str:
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def record_hash_from_job(fields: dict[str, Any]) -> str:
    payload = {
        "job_code": fields.get("job_code"),
        "organization": fields.get("organization"),
        "job_title": fields.get("job_title"),
        "city": fields.get("city"),
        "district": fields.get("district"),
        "work_location": fields.get("work_location"),
        "recruitment_count": fields.get("recruitment_count"),
        "education": fields.get("education"),
        "degree": fields.get("degree"),
        "major": fields.get("major"),
        "registration_deadline": _iso(fields.get("registration_deadline")),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def digest_content_hash(sections: dict[str, Any]) -> str:
    raw = json.dumps(sections, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def job_record_changed(existing_raw: str | None, new_raw: str) -> bool:
    if not existing_raw:
        return True
    return existing_raw != new_raw


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
