import inspect

from app.collectors import ALL_COLLECTORS
from app.collectors.base import BaseCollector


def test_all_collectors_subclass_base() -> None:
    for cls in ALL_COLLECTORS:
        assert issubclass(cls, BaseCollector)
        assert cls.source_id
        assert inspect.isabstract(cls) is False
