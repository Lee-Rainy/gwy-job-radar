"""东莞市官方招考补充来源。"""

from app.collectors.base import BaseCollector, RawAnnouncement


class DgCollector(BaseCollector):
    source_id = "dg_official"
    announcement_type = "事业单位"
    base_url = "https://www.dg.gov.cn"

    async def fetch_list(self) -> list[RawAnnouncement]:
        return []

    async def enrich(self, item: RawAnnouncement) -> RawAnnouncement:
        return item
