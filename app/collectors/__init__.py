from app.collectors.base import BaseCollector, CollectorResult, RawAnnouncement
from app.collectors.dg import DgCollector
from app.collectors.fs import FsCollector
from app.collectors.gd_gwy import GdGwyCollector
from app.collectors.gd_sydw import GdSydwCollector
from app.collectors.gz import GzCollector

ALL_COLLECTORS: list[type[BaseCollector]] = [
    GdGwyCollector,
    GdSydwCollector,
    GzCollector,
    DgCollector,
    FsCollector,
]

COLLECTOR_REGISTRY: dict[str, type[BaseCollector]] = {cls.source_id: cls for cls in ALL_COLLECTORS}


def collectors_for_run(source_ids: list[str] | None = None) -> list[type[BaseCollector]]:
    if not source_ids:
        return ALL_COLLECTORS
    selected: list[type[BaseCollector]] = []
    for sid in source_ids:
        cls = COLLECTOR_REGISTRY.get(sid)
        if cls:
            selected.append(cls)
    return selected or ALL_COLLECTORS

__all__ = [
    "ALL_COLLECTORS",
    "BaseCollector",
    "CollectorResult",
    "RawAnnouncement",
    "GdGwyCollector",
    "GdSydwCollector",
    "GzCollector",
    "DgCollector",
    "FsCollector",
]
