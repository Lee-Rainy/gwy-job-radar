import typer
from rich.console import Console

from gwy_job_radar import __version__

app = typer.Typer(
    name="gwy-job-radar",
    help="公务员招考信息监测与提醒",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """显示当前版本。"""
    console.print(f"gwy-job-radar {__version__}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
