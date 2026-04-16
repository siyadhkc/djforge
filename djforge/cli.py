"""
djforge.cli
~~~~~~~~~~~
Entry point:  djforge new <name>  /  djforge new  (interactive)
"""
from __future__ import annotations

from copy import deepcopy
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from djforge.config import ProjectConfig, PRESETS
from djforge.renderer import build_file_map, write_tree

app = typer.Typer(
    name="djforge",
    help="⚡  Fast, modern Django project generator.",
    add_completion=True,
    no_args_is_help=False,
)

_con = Console()


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _banner():
    _con.print()
    _con.print(Panel(
        "[bold yellow]⚡  djforge[/]  [dim white]—  fast Django project generator[/]",
        border_style="yellow", padding=(0, 3),
    ))
    _con.print()


def _summary(cfg: ProjectConfig):
    t = Table.grid(padding=(0, 2))
    t.add_column(style="dim")
    t.add_column(style="bold green")
    rows = [
        ("project",  cfg.project_name),
        ("database", cfg.database),
        ("cache",    cfg.cache),
        ("auth",     cfg.auth),
        ("celery",   "yes" if cfg.use_celery    else "no"),
        ("docker",   "yes" if cfg.use_docker    else "no"),
        ("drf",      "yes" if cfg.use_drf       else "no"),
        ("sentry",   "yes" if cfg.use_sentry    else "no"),
    ]
    for k, v in rows:
        t.add_row(k, v)
    _con.print(Panel(t, title="[bold]Project config[/]", border_style="dim", padding=(1, 3)))
    _con.print()


def _post_message(cfg: ProjectConfig, target: Path):
    _con.print()
    _con.print(Panel(
        f"[bold green]✅  {cfg.project_name} created![/]\n\n"
        f"  [dim]cd[/]  [bold]{target.name}[/]\n"
        f"  [dim]then run[/]  [bold yellow]make install && make migrate && make dev[/]",
        border_style="green",
        padding=(1, 3),
    ))
    _con.print()


# ══════════════════════════════════════════════════════════════════════════════
# Commands
# ══════════════════════════════════════════════════════════════════════════════

@app.command("new")
def new(
    name: Annotated[Optional[str], typer.Argument(help="Project name")] = None,
    output_dir: Annotated[Path, typer.Option("--output", "-o", help="Where to create the project")] = Path("."),
    preset: Annotated[Optional[str], typer.Option("--preset", "-p", help="minimal | api | fullstack")] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Accept all defaults, no prompts")] = False,
    venv: Annotated[bool, typer.Option("--venv", help="Create a virtualenv after generation")] = False,
    git: Annotated[bool, typer.Option("--git/--no-git", help="Run git init after generation")] = True,
):
    """Generate a new Django project."""
    _banner()

    # ── resolve config ────────────────────────────────────────────────────────
    if preset:
        if preset not in PRESETS:
            _con.print(f"[red]Unknown preset '{preset}'. Available: {', '.join(PRESETS)}[/]")
            raise typer.Exit(1)
        cfg = deepcopy(PRESETS[preset])
        if name:
            cfg.project_name = name
    else:
        cfg = ProjectConfig(project_name=name or "myproject")

    # ── interactive prompts ───────────────────────────────────────────────────
    if not yes and not preset:
        try:
            from djforge.tui.prompts import prompt
            cfg = prompt(cfg)
        except (KeyboardInterrupt, EOFError):
            _con.print("\n[yellow]Aborted.[/]")
            raise typer.Exit(0)

    # ── validate target dir ───────────────────────────────────────────────────
    target = output_dir / cfg.slug
    if target.exists():
        _con.print(f"[red]Directory '{target}' already exists. Remove it first.[/]")
        raise typer.Exit(1)

    _summary(cfg)

    # ── write files ───────────────────────────────────────────────────────────
    file_map = build_file_map(cfg)
    written: list[str] = []

    with Progress(
        SpinnerColumn(spinner_name="dots", style="yellow"),
        TextColumn("[progress.description]{task.description}"),
        console=_con,
        transient=True,
    ) as progress:
        task = progress.add_task("Generating project…", total=len(file_map))
        for rel in write_tree(target, file_map, cfg):
            written.append(rel)
            progress.update(task, advance=1, description=f"  [dim]{rel}[/dim]")

    # copy .env.example → .env
    env_src = target / ".env.example"
    if env_src.exists():
        shutil.copy(env_src, target / ".env")

    _con.print(f"  [dim]Wrote {len(written)} files.[/]")

    # ── git init ──────────────────────────────────────────────────────────────
    if git:
        try:
            subprocess.run(
                ["git", "init", "-q"],
                cwd=target, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["git", "add", "-A"],
                cwd=target, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            _con.print("  [dim green]✔  git init[/]")
        except (subprocess.CalledProcessError, FileNotFoundError):
            _con.print("  [dim yellow]⚠  git not found — skipping[/]")

    # ── optional venv ─────────────────────────────────────────────────────────
    if venv:
        with Progress(
            SpinnerColumn(spinner_name="dots", style="yellow"),
            TextColumn("[progress.description]{task.description}"),
            console=_con, transient=True,
        ) as p:
            p.add_task("Creating virtualenv…")
            subprocess.run(
                [sys.executable, "-m", "venv", ".venv"],
                cwd=target, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        _con.print("  [dim green]✔  .venv created[/]")

    _post_message(cfg, target)


@app.command("list-presets")
def list_presets():
    """Show available presets."""
    _banner()
    t = Table("Preset", "Database", "Cache", "Auth", "Celery", "Docker", border_style="dim")
    for name, p in PRESETS.items():
        t.add_row(
            f"[bold yellow]{name}[/]",
            p.database, p.cache, p.auth,
            "✓" if p.use_celery else "—",
            "✓" if p.use_docker else "—",
        )
    _con.print(t)
    _con.print()
    _con.print("  [dim]Usage:[/]  [bold]djforge new myapp --preset api[/]")
    _con.print()


@app.command("version")
def version():
    """Show djforge version."""
    from importlib.metadata import version as _v
    try:
        v = _v("djforge")
    except Exception:
        v = "0.1.0-dev"
    _con.print(f"[bold yellow]djforge[/] [dim]{v}[/]")


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    app()


if __name__ == "__main__":
    main()
