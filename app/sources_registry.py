from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import yaml

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "docs" / "sources.yaml"


def load_sources() -> list[dict[str, Any]]:
    if not _REGISTRY_PATH.is_file():
        return []
    data = yaml.safe_load(_REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return []
    sources = data.get("sources")
    if not isinstance(sources, list):
        return []
    return [entry for entry in sources if isinstance(entry, dict)]


def source_by_id(source_id: str) -> dict[str, Any] | None:
    for entry in load_sources():
        if entry.get("id") == source_id:
            return entry
    return None


def probe_urls_for_source(entry: dict[str, Any]) -> list[str]:
    """生成用于 doctor 探活的首页列表 URL。"""
    status = str(entry.get("status") or "stub").lower()
    if status != "live":
        return []

    base = str(entry.get("base_url") or "").rstrip("/")
    if not base:
        return []

    explicit = entry.get("list_pages")
    if isinstance(explicit, list) and explicit:
        return [str(url) for url in explicit if url]

    sections = entry.get("list_sections")
    template = str(entry.get("list_path_template") or "")
    if not isinstance(sections, list) or not template:
        return []

    urls: list[str] = []
    for section in sections:
        path = template.replace("{section}", str(section))
        urls.append(urljoin(base + "/", path.lstrip("/")))
    return urls
