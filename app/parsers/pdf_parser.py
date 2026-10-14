from pathlib import Path

import pymupdf

from app.parsers.html_parser import ParsedJobRow


def extract_pdf_text(path: Path) -> str:
    doc = pymupdf.open(path)
    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return "\n".join(parts)


def parse_pdf_announcement(path: Path) -> tuple[str, list[ParsedJobRow]]:
    """
    PDF 公告通常以正文为主；职位明细多在附件 Excel。
    此处返回全文与空岗位列表，供后续规则或人工映射扩展。
    """
    text = extract_pdf_text(path)
    return text, []
