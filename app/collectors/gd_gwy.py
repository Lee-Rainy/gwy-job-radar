"""广东省公务员考试公告 / 职位表（官方源占位，按实际栏目 URL 实现列表解析）。"""

from datetime import datetime

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, RawAnnouncement
from app.config import JOB_TYPE_CIVIL_SERVICE


class GdGwyCollector(BaseCollector):
    """
    信息源示例（需以当期官网栏目为准）：
    - 广东省公务员考试专题 / 人社厅、组织部相关栏目
    实现时仅解析公开列表与附件，遵守 robots 与访问频率限制。
    """

    source_id = "gd_gwy"
    announcement_type = "公务员"
    base_url = "https://www.gd.gov.cn"

    async def fetch_list(self) -> list[RawAnnouncement]:
        # TODO: 替换为当期官方列表页 URL 与选择器
        list_url = f"{self.base_url}/"
        response = await self.client.get(list_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        items: list[RawAnnouncement] = []
        for link in soup.select("a[href]")[:0]:
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if not title or not href:
                continue
            items.append(
                RawAnnouncement(
                    source_id=self.source_id,
                    title=title,
                    source_url=self.normalize_url(href),
                    announcement_type=self.announcement_type,
                    canonical_url=self.normalize_url(href),
                    published_at=None,
                    metadata={"job_type": JOB_TYPE_CIVIL_SERVICE},
                )
            )
        return items

    async def enrich(self, item: RawAnnouncement) -> RawAnnouncement:
        response = await self.client.get(item.source_url)
        response.raise_for_status()
        item.html_body = response.text
        item.published_at = item.published_at or datetime.now()
        return item
