from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

from app.collectors.browser_headers import DEFAULT_BROWSER_HEADERS
from app.config import get_settings


@dataclass
class RawAttachment:
    url: str
    filename: str | None = None
    content_type: str | None = None


@dataclass
class RawAnnouncement:
    """采集器输出的原始公告，尚未入库。"""

    source_id: str
    title: str
    source_url: str
    announcement_type: str
    canonical_url: str | None = None
    published_at: datetime | None = None
    html_body: str | None = None
    text_summary: str | None = None
    attachments: list[RawAttachment] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectorResult:
    announcements: list[RawAnnouncement]
    errors: list[str] = field(default_factory=list)


class BaseCollector(ABC):
    """官方网站采集器抽象接口。"""

    source_id: str
    announcement_type: str
    base_url: str

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> "BaseCollector":
        if self._client is None:
            settings = get_settings()
            headers = {**DEFAULT_BROWSER_HEADERS, "User-Agent": settings.http_user_agent}
            if settings.http_user_agent == "gd-job-radar/0.1":
                headers = DEFAULT_BROWSER_HEADERS.copy()
            self._client = httpx.AsyncClient(
                timeout=settings.http_timeout_seconds,
                headers=headers,
                follow_redirects=True,
            )
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Collector client not initialized; use async with")
        return self._client

    @abstractmethod
    async def fetch_list(self) -> list[RawAnnouncement]:
        """拉取列表页，返回待解析的公告条目（可不含正文）。"""

    @abstractmethod
    async def enrich(self, item: RawAnnouncement) -> RawAnnouncement:
        """进入详情页，补充正文与附件链接。"""

    async def collect(self) -> CollectorResult:
        errors: list[str] = []
        enriched: list[RawAnnouncement] = []
        try:
            items = await self.fetch_list()
        except Exception as exc:  # noqa: BLE001 — 采集层记录错误继续
            return CollectorResult(announcements=[], errors=[f"{self.source_id}: {exc}"])

        for item in items:
            try:
                enriched.append(await self.enrich(item))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{self.source_id} {item.source_url}: {exc}")
        return CollectorResult(announcements=enriched, errors=errors)

    def normalize_url(self, url: str) -> str:
        if url.startswith("http"):
            return url
        return f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
