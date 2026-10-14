"""从 rsj 详情及报名外链页面抽取报名时间与招聘条件文本。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.collectors.browser_headers import DEFAULT_BROWSER_HEADERS
from app.services.normalize import parse_chinese_datetime

_LINK_POSITIVE = (
    "报名",
    "报考",
    "应聘",
    "申请",
    "人事考试",
    "事业单位招聘",
    "公招",
)
_LINK_NEGATIVE = (
    "成绩",
    "公示",
    "体检",
    "缴费",
    "准考证",
    "面试",
    "调剂",
    "递补",
    "附件",
    ".xls",
    ".xlsx",
    ".pdf",
    ".doc",
)


@dataclass(frozen=True)
class AnnouncementSchedule:
    external_url: str | None
    registration_start: datetime | None
    registration_deadline: datetime | None
    conditions_text: str | None


def pick_registration_url(html: str, page_url: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    base_host = urlparse(page_url).netloc
    candidates: list[tuple[int, str]] = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript"):
            continue
        text = anchor.get_text(strip=True)
        combined = f"{text} {href}"
        lower = combined.lower()
        if any(neg in combined for neg in _LINK_NEGATIVE):
            continue
        score = 0
        for word in _LINK_POSITIVE:
            if word in combined:
                score += 10
        if "/attachment/" in lower:
            continue
        if urlparse(urljoin(page_url, href)).netloc == base_host and "/content/post_" not in href:
            if score == 0:
                continue
        absolute = urljoin(page_url, href)
        if score > 0:
            candidates.append((score, absolute))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][1]


def parse_registration_window(text: str) -> tuple[datetime | None, datetime | None]:
    if not text:
        return None, None

    range_patterns = [
        r"(?:网上)?报名时间[：:为]?\s*(\d{4}[年\-/]\d{1,2}[月\-/]\d{1,2}日?)\s*(?:至|到|—|–|-)\s*(\d{4}[年\-/]\d{1,2}[月\-/]\d{1,2}日?)",
        r"(?:报名时间为|报名时间自)\s*(\d{4}[年\-/]\d{1,2}[月\-/]\d{1,2}日?).*?(?:至|到)\s*(\d{4}[年\-/]\d{1,2}[月\-/]\d{1,2}日?)",
    ]
    for pattern in range_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            start = parse_chinese_datetime(match.group(1))
            end = parse_chinese_datetime(match.group(2))
            return start, end

    deadline_patterns = [
        r"(?:报名)?截止(?:时间)?[：:为]?\s*(\d{4}[年\-/]\d{1,2}[月\-/]\d{1,2}日?)",
        r"(\d{4}[年\-/]\d{1,2}[月\-/]\d{1,2}日?)\s*(?:24:00)?\s*前报名",
    ]
    for pattern in deadline_patterns:
        match = re.search(pattern, text)
        if match:
            return None, parse_chinese_datetime(match.group(1))

    return None, None


def extract_conditions_snippet(text: str, max_len: int = 2000) -> str | None:
    if not text:
        return None
    keywords = ("招聘条件", "应聘条件", "报考条件", "招聘对象", "学历", "专业", "年龄")
    snippets: list[str] = []
    for key in keywords:
        idx = text.find(key)
        if idx == -1:
            continue
        snippets.append(text[idx : idx + 400])
    if not snippets:
        return None
    merged = re.sub(r"\s+", " ", " ".join(snippets)).strip()
    return merged[:max_len] if merged else None


def parse_schedule_from_html(html: str, page_url: str) -> AnnouncementSchedule:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    start, end = parse_registration_window(text)
    conditions = extract_conditions_snippet(text)
    return AnnouncementSchedule(
        external_url=None,
        registration_start=start,
        registration_deadline=end,
        conditions_text=conditions,
    )


async def enrich_with_registration_link(
    client: httpx.AsyncClient,
    *,
    html: str,
    page_url: str,
) -> AnnouncementSchedule:
    local = parse_schedule_from_html(html, page_url)
    external_url = pick_registration_url(html, page_url)
    if not external_url:
        return AnnouncementSchedule(
            external_url=None,
            registration_start=local.registration_start,
            registration_deadline=local.registration_deadline,
            conditions_text=local.conditions_text,
        )

    try:
        response = await client.get(external_url, headers=DEFAULT_BROWSER_HEADERS)
        response.raise_for_status()
        remote = parse_schedule_from_html(response.text, external_url)
    except Exception:
        return AnnouncementSchedule(
            external_url=external_url,
            registration_start=local.registration_start,
            registration_deadline=local.registration_deadline,
            conditions_text=local.conditions_text,
        )

    start = remote.registration_start or local.registration_start
    end = remote.registration_deadline or local.registration_deadline
    conditions = remote.conditions_text or local.conditions_text
    if remote.conditions_text and local.conditions_text:
        conditions = f"{local.conditions_text} {remote.conditions_text}"[:2000]

    return AnnouncementSchedule(
        external_url=external_url,
        registration_start=start,
        registration_deadline=end,
        conditions_text=conditions,
    )
