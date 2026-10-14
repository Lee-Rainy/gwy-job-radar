import json
import re
from datetime import datetime

from app.config import JOB_TYPE_CIVIL_SERVICE, JOB_TYPE_PUBLIC_INSTITUTION
from app.parsers.html_parser import ParsedJobRow


CITY_ALIASES: dict[str, str] = {
    "广州市": "广州",
    "东莞市": "东莞",
    "佛山市": "佛山",
    "gd_gz": "广州",
    "gd_dg": "东莞",
    "gd_fs": "佛山",
}


def normalize_city(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    for alias, canonical in CITY_ALIASES.items():
        if alias in text:
            return canonical
    for name in ("广州", "东莞", "佛山"):
        if name in text:
            return name
    return text


def infer_job_type(announcement_type: str, metadata: dict | None = None) -> str:
    if metadata and metadata.get("job_type"):
        return str(metadata["job_type"])
    if "事业" in announcement_type:
        return JOB_TYPE_PUBLIC_INSTITUTION
    return JOB_TYPE_CIVIL_SERVICE


def normalize_job_row(
    row: ParsedJobRow,
    *,
    job_type: str,
    province: str = "广东",
) -> dict:
    city = normalize_city(row.city or row.work_location)
    return {
        "job_code": _clean(row.job_code),
        "organization": _clean(row.organization),
        "job_title": _clean(row.job_title) or "",
        "job_type": job_type,
        "province": province,
        "city": city,
        "district": _clean(row.district),
        "work_location": _clean(row.work_location),
        "recruitment_count": row.recruitment_count,
        "education": _clean(row.education),
        "degree": _clean(row.degree),
        "major": _clean(row.major),
        "age_requirement": _clean(row.age_requirement),
        "candidate_type": _clean(row.candidate_type),
        "registration_start": row.registration_start,
        "registration_deadline": row.registration_deadline,
        "establishment_status": None,
        "raw_data": json.dumps(row.raw, ensure_ascii=False),
    }


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", value.strip())
    return text or None


def parse_chinese_datetime(text: str | None) -> datetime | None:
    if not text:
        return None
    patterns = [
        r"(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            y, m, d = map(int, match.groups())
            return datetime(y, m, d)
    return None
