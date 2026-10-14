"""佛山市官方招考补充来源。"""

from app.collectors.base import BaseCollector, RawAnnouncement


class FsCollector(BaseCollector):
    source_id = "fs_official"
    announcement_type = "事业单位"
    base_url = "https://www.foshan.gov.cn"

    async def fetch_list(self) -> list[RawAnnouncement]:
        return []

    async def enrich(self, item: RawAnnouncement) -> RawAnnouncement:
        return item
