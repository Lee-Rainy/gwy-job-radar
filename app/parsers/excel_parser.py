from pathlib import Path
from typing import Any

import pandas as pd

from app.parsers.html_parser import ParsedJobRow


def parse_excel_jobs(path: Path, sheet_name: str | int = 0) -> list[ParsedJobRow]:
    header_row = _detect_header_row(path, sheet_name)
    if header_row is None:
        return []
    df = pd.read_excel(path, sheet_name=sheet_name, header=header_row, dtype=str)
    df = df.fillna("")
    rows: list[ParsedJobRow] = []
    for record in df.to_dict(orient="records"):
        raw: dict[str, Any] = {str(k): str(v) for k, v in record.items()}
        title = _pick(raw, "岗位名称", "职位名称", "招聘岗位")
        if not title or title in ("岗位名称", "职位名称", "招聘岗位"):
            continue
        rows.append(
            ParsedJobRow(
                job_code=_pick(raw, "岗位代码", "职位代码"),
                organization=_pick(raw, "招聘单位", "用人单位", "主管部门"),
                job_title=title,
                city=_pick(raw, "城市", "考区", "工作地点"),
                district=_pick(raw, "区县", "所属区县"),
                work_location=_pick(raw, "工作地点", "工作地址"),
                recruitment_count=_parse_int(_pick(raw, "招聘人数", "招聘名额", "拟招聘人数")),
                education=_pick(raw, "学历", "学历要求"),
                degree=_pick(raw, "学位", "学位要求"),
                major=_pick(raw, "专业", "专业要求"),
                age_requirement=_pick(raw, "年龄", "年龄要求"),
                candidate_type=_pick(raw, "招聘对象", "考生类别"),
                registration_start=None,
                registration_deadline=None,
                raw=raw,
            )
        )
    return rows


def _pick(raw: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        if key in raw and str(raw[key]).strip():
            return str(raw[key]).strip()
    for key in keys:
        for col, val in raw.items():
            if key in col and str(val).strip():
                return str(val).strip()
    return None


def _detect_header_row(path: Path, sheet_name: str | int) -> int | None:
    preview = pd.read_excel(path, sheet_name=sheet_name, header=None, dtype=str).fillna("")
    for idx, row in preview.iterrows():
        line = "".join(str(v) for v in row.tolist())
        if any(key in line for key in ("岗位名称", "职位名称", "招聘岗位")):
            return int(idx)
    return 0


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else None
