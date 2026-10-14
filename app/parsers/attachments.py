from pathlib import Path

import httpx

from app.collectors.browser_headers import DEFAULT_BROWSER_HEADERS
from app.config import get_settings
from app.parsers.excel_parser import parse_excel_jobs
from app.parsers.html_parser import ParsedJobRow


def download_attachment(url: str, filename: str | None = None) -> Path:
    settings = get_settings()
    target_dir = settings.data_dir / "attachments"
    target_dir.mkdir(parents=True, exist_ok=True)
    name = filename or url.split("/")[-1]
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)
    path = target_dir / safe_name
    if path.exists() and path.stat().st_size > 0:
        return path
    with httpx.Client(headers=DEFAULT_BROWSER_HEADERS, timeout=60, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        path.write_bytes(response.content)
    return path


def parse_attachment_rows(url: str, filename: str | None = None) -> list[ParsedJobRow]:
    path = download_attachment(url, filename)
    lower = path.name.lower()
    if lower.endswith((".xls", ".xlsx")):
        return parse_excel_jobs(path)
    return []
