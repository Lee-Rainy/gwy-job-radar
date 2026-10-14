"""广东省事业单位公开招聘（官方源占位）。"""

from datetime import datetime

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, RawAnnouncement
from app.config import JOB_TYPE_PUBLIC_INSTITUTION


class GdSydwCollector(BaseCollector):
    source_id = "gd_sydw"
    announcement_type = "事业单位"
    base_url = "https://www.gd.gov.cn"

    async def fetch_list(self) -> list[RawAnnouncement]:
        list_url = f"{self.base_url}/"
        response = await self.client.get(list_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        items: list[RawAnnouncement] = []
        for link in soup.select("a[href]")[:0]:
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if not title:
                continue
            items.append(
                RawAnnouncement(
                    source_id=self.source_id,
                    title=title,
                    source_url=self.normalize_url(href),
                    announcement_type=self.announcement_type,
                    canonical_url=self.normalize_url(href),
                    metadata={"job_type": JOB_TYPE_PUBLIC_INSTITUTION},
                )
            )
        return items

    async def enrich(self, item: RawAnnouncement) -> RawAnnouncement:
        response = await self.client.get(item.source_url)
        response.raise_for_status()
        item.html_body = response.text
        item.published_at = item.published_at or datetime.now()
        return item
