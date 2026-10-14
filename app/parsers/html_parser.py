from dataclasses import dataclass
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup


@dataclass
class ParsedJobRow:
    job_code: str | None
    organization: str | None
    job_title: str
    city: str | None
    district: str | None
    work_location: str | None
    recruitment_count: int | None
    education: str | None
    degree: str | None
    major: str | None
    age_requirement: str | None
    candidate_type: str | None
    registration_start: datetime | None
    registration_deadline: datetime | None
    raw: dict[str, Any]


def extract_text_summary(html: str, max_length: int = 2000) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ", strip=True).split())
    return text[:max_length]


def parse_html_job_table(html: str) -> list[ParsedJobRow]:
    """解析 HTML 表格型职位表（列名因站点而异，需按源站映射扩展）。"""
    soup = BeautifulSoup(html, "lxml")
    rows: list[ParsedJobRow] = []
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if not headers:
            continue
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cells) != len(headers):
                continue
            raw = dict(zip(headers, cells, strict=False))
            title = raw.get("岗位名称") or raw.get("职位名称") or raw.get("招聘岗位") or ""
            if not title:
                continue
            rows.append(
                ParsedJobRow(
                    job_code=raw.get("岗位代码") or raw.get("职位代码"),
                    organization=raw.get("招聘单位") or raw.get("用人单位"),
                    job_title=title,
                    city=raw.get("城市") or raw.get("工作地点"),
                    district=raw.get("区县"),
                    work_location=raw.get("工作地点"),
                    recruitment_count=_parse_int(raw.get("招聘人数") or raw.get("招聘名额")),
                    education=raw.get("学历"),
                    degree=raw.get("学位"),
                    major=raw.get("专业"),
                    age_requirement=raw.get("年龄"),
                    candidate_type=raw.get("招聘对象"),
                    registration_start=None,
                    registration_deadline=None,
                    raw=raw,
                )
            )
    return rows


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else None
