import asyncio
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console

from app import __version__
from app.config import (
    DELIVERY_PERIOD_EVENING,
    DELIVERY_PERIOD_MORNING,
    get_settings,
    reload_settings,
    resolve_env_files,
)
from app.database import get_engine, init_db
from app.pipeline import run_collectors, run_morning_evening_job, send_digest_for_period
from app.scheduler import start_scheduler
from app.services.mailer import send_html_email

app = typer.Typer(help="广东省考公/事业单位岗位采集与邮件简报")
console = Console()


def _setup_logging() -> None:
    settings = get_settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(settings.log_dir / "app.log", encoding="utf-8"),
        ],
    )


@app.command()
def version() -> None:
    console.print(f"gd-job-radar {__version__}")


@app.command("init-db")
def init_db_cmd() -> None:
    _setup_logging()
    init_db()
    console.print("数据库表已初始化")


@app.command()
def collect() -> None:
    """仅执行采集与入库。"""
    _setup_logging()
    init_db()
    asyncio.run(run_collectors())
    console.print("采集完成")


@app.command("send-digest")
def send_digest(
    period: str = typer.Option(
        DELIVERY_PERIOD_MORNING,
        "--period",
        "-p",
        help="morning 或 evening",
    ),
) -> None:
    _setup_logging()
    init_db()
    if period not in (DELIVERY_PERIOD_MORNING, DELIVERY_PERIOD_EVENING):
        raise typer.BadParameter("period 必须为 morning 或 evening")
    send_digest_for_period(period)
    console.print(f"简报发送流程已执行（{period}）")


@app.command()
def doctor(
    sources: bool = typer.Option(
        False,
        "--sources",
        help="探活 docs/sources.yaml 中 status=live 的列表页",
    ),
) -> None:
    """检查本地运行条件（不输出密码）。"""
    reload_settings()
    if sources:
        _doctor_sources()
        return

    settings = get_settings()
    env_files = resolve_env_files()
    console.print("[bold]环境文件[/bold]", ", ".join(env_files))
    console.print(f"Python: {sys.version.split()[0]}")
    console.print(f"DATABASE_URL: {_mask_db_url(settings.database_url)}")
    console.print(
        f"SMTP: {settings.smtp_host}:{settings.smtp_port} "
        f"user={settings.smtp_user or '(未设置)'} "
        f"recipients={settings.mail_recipients or '(未设置)'}"
    )
    db_ok = False
    try:
        from sqlalchemy import text

        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        url = settings.database_url.lower()
        label = "SQLite" if url.startswith("sqlite") else "数据库"
        console.print(f"[green]{label} 连接成功[/green]")
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]数据库连接失败[/red]: {exc}")
        console.print(
            "[dim]若刚安装 PostgreSQL，请先运行 scripts/setup-local-db.ps1 创建 radar / gd_job_radar[/dim]"
        )
    if not db_ok:
        raise typer.Exit(code=1)


@app.command("run-now")
def run_now(
    period: str = typer.Option(
        DELIVERY_PERIOD_EVENING,
        "--period",
        "-p",
        help="morning 或 evening",
    ),
    sources: str = typer.Option(
        "gz_rsj",
        "--sources",
        "-s",
        help="采集器 source_id，逗号分隔，默认 gz_rsj",
    ),
) -> None:
    """立即执行：采集 + 按个人条件筛选 + 发送邮件。"""
    reload_settings()
    _setup_logging()
    init_db()
    source_ids = [part.strip() for part in sources.split(",") if part.strip()]
    asyncio.run(run_morning_evening_job(period, source_ids=source_ids))
    console.print(f"已完成采集与邮件发送（period={period}, sources={source_ids}）")


@app.command("test-smtp")
def test_smtp() -> None:
    """发送一封测试 HTML 邮件（用于调试 QQ SMTP）。"""
    reload_settings()
    _setup_logging()
    settings = get_settings()
    if not settings.mail_recipients:
        raise typer.Exit(code=1)
    subject = "【考公雷达】SMTP 测试邮件"
    body = (
        "<p>这是一封 SMTP 调试邮件。</p>"
        f"<p>发件配置：{settings.smtp_user}</p>"
        f"<p>时间：{__import__('datetime').datetime.now().isoformat(timespec='seconds')}</p>"
    )
    send_html_email(subject=subject, html_body=body)
    console.print(f"[green]已发送至[/green] {', '.join(settings.mail_recipients)}")


@app.command()
def serve() -> None:
    """启动 APScheduler，按配置早晚执行任务。"""
    _setup_logging()
    init_db()
    console.print("调度器运行中…")
    start_scheduler()


def _doctor_sources() -> None:
    import httpx

    from app.collectors.browser_headers import DEFAULT_BROWSER_HEADERS
    from app.sources_registry import load_sources, probe_urls_for_source

    entries = load_sources()
    if not entries:
        console.print("[red]未找到 docs/sources.yaml 或 sources 为空[/red]")
        raise typer.Exit(code=1)

    for entry in entries:
        sid = entry.get("id", "?")
        status = entry.get("status", "stub")
        console.print(f"\n[bold]{sid}[/bold] ({status})")
        if str(status).lower() != "live":
            console.print(f"  [dim]跳过探活: {entry.get('notes', '')}[/dim]")
            continue
        urls = probe_urls_for_source(entry)
        headers = DEFAULT_BROWSER_HEADERS if entry.get("needs_browser_ua") else {}
        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as client:
            for url in urls:
                try:
                    response = client.get(url)
                    ok = response.status_code == 200
                    color = "green" if ok else "red"
                    console.print(f"  [{color}]{response.status_code}[/{color}] {url}")
                except Exception as exc:  # noqa: BLE001
                    console.print(f"  [red]ERR[/red] {url} ({exc})")


def _mask_db_url(url: str) -> str:
    if "@" not in url:
        return url
    prefix, rest = url.split("@", 1)
    if "://" in prefix:
        scheme, _cred = prefix.split("://", 1)
        return f"{scheme}://***@{rest}"
    return url


if __name__ == "__main__":
    app()
