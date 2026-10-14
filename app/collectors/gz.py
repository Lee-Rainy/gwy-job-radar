"""广州市人力资源和社会保障局 rsj.gz.gov.cn 招聘公告采集。"""

import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, RawAnnouncement, RawAttachment
from app.collectors.browser_headers import DEFAULT_BROWSER_HEADERS
from app.config import JOB_TYPE_PUBLIC_INSTITUTION, get_settings
from app.parsers.registration_extract import enrich_with_registration_link

LIST_SECTIONS = ("tzgg", "gzdt")
MAX_LIST_PAGES = 12
TITLE_KEYWORDS = ("招聘", "招考", "公开", "遴选", "选调", "事业", "岗位", "聘", "雇")
EXCLUDE_TITLE_KEYWORDS = (
    "成绩",
    "体检",
    "拟聘用",
    "递补",
    "公示",
    "面试",
    "资格复审",
    "放弃",
    "调剂",
    "专场活动",
    "招聘会",
)


class GzCollector(BaseCollector):
    source_id = "gz_rsj"
    announcement_type = "事业单位"
    base_url = "https://rsj.gz.gov.cn"

    async def fetch_list(self) -> list[RawAnnouncement]:
        items: list[RawAnnouncement] = []
        seen: set[str] = set()
        for section in LIST_SECTIONS:
            empty_pages = 0
            for page in range(1, MAX_LIST_PAGES + 1):
                path = f"/zwdt/{section}/index.html" if page == 1 else f"/zwdt/{section}/index_{page}.html"
                url = urljoin(self.base_url, path)
                response = await self.client.get(url, headers=DEFAULT_BROWSER_HEADERS)
                if response.status_code != 200:
                    break
                page_items = self._parse_list_html(response.text, section)
                if not page_items:
                    empty_pages += 1
                else:
                    empty_pages = 0
                if empty_pages >= 2 and page > 2:
                    break
                for item in page_items:
                    key = item.canonical_url or item.source_url
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append(item)
        return items

    def _parse_list_html(self, html: str, section: str) -> list[RawAnnouncement]:
        soup = BeautifulSoup(html, "lxml")
        results: list[RawAnnouncement] = []
        for link in soup.find_all("a", href=True):
            title = link.get_text(strip=True)
            if get_settings().crawl_target_year not in title:
                continue
            if not any(key in title for key in TITLE_KEYWORDS):
                continue
            if any(key in title for key in EXCLUDE_TITLE_KEYWORDS):
                continue
            href = self.normalize_url(link["href"])
            if "/content/post_" not in href:
                continue
            results.append(
                RawAnnouncement(
                    source_id=self.source_id,
                    title=title,
                    source_url=href,
                    canonical_url=href,
                    announcement_type=self.announcement_type,
                    metadata={
                        "job_type": JOB_TYPE_PUBLIC_INSTITUTION,
                        "section": section,
                    },
                )
            )
        return results

    async def enrich(self, item: RawAnnouncement) -> RawAnnouncement:
        response = await self.client.get(item.source_url, headers=DEFAULT_BROWSER_HEADERS)
        response.raise_for_status()
        item.html_body = response.text
        item.published_at = self._parse_published_at(response.text) or item.published_at
        item.attachments = self._extract_attachments(response.text, item.source_url)
        item.text_summary = BeautifulSoup(response.text, "lxml").get_text(" ", strip=True)[:3000]

        schedule = await enrich_with_registration_link(
            self.client,
            html=response.text,
            page_url=item.source_url,
        )
        if schedule.external_url:
            item.metadata["external_url"] = schedule.external_url
        if schedule.registration_start:
            item.metadata["registration_start"] = schedule.registration_start.isoformat()
        if schedule.registration_deadline:
            item.metadata["registration_deadline"] = schedule.registration_deadline.isoformat()
        if schedule.conditions_text:
            item.metadata["conditions_text"] = schedule.conditions_text
            item.text_summary = (item.text_summary or "")[:1500] + " " + schedule.conditions_text
            item.text_summary = item.text_summary[:4000]

        return item

    def _extract_attachments(self, html: str, page_url: str) -> list[RawAttachment]:
        soup = BeautifulSoup(html, "lxml")
        attachments: list[RawAttachment] = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            lower = href.lower()
            if not any(ext in lower for ext in (".xls", ".xlsx", ".pdf", ".doc", ".docx")):
                continue
            if "/attachment/" not in lower:
                continue
            filename = link.get_text(strip=True) or href.split("/")[-1]
            if any(skip in filename for skip in ("目录", "指南", "联系方式", "问答")):
                continue
            if not any(ext in lower for ext in (".xls", ".xlsx")):
                continue
            attachments.append(
                RawAttachment(
                    url=self.normalize_url(href),
                    filename=filename,
                )
            )
        return attachments

    def _parse_published_at(self, html: str) -> datetime | None:
        match = re.search(r"发布时间[：:]\s*(\d{4}-\d{1,2}-\d{1,2})", html)
        if not match:
            return None
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d")
        except ValueError:
            return None
