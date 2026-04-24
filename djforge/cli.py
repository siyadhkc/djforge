"""Command line interface for djforge."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from djforge import __version__
from djforge.config import PRESETS, ProjectConfig, TemplatePreset
from djforge.renderer import build_file_map, write_tree

app = typer.Typer(
    name="djforge",
    help="A tiny cookiecutter-style Django project generator.",
    no_args_is_help=True,
)
console = Console()


def _copy_config(preset: str, name: str) -> ProjectConfig:
    if preset not in PRESETS:
        choices = ", ".join(PRESETS)
        raise typer.BadParameter(f"unknown preset {preset!r}; choose one of: {choices}")
    return PRESETS[preset].with_name(name)  # type: ignore[index]


def _print_summary(cfg: ProjectConfig, target: Path) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="dim")
    table.add_column(style="bold")
    table.add_row("name", cfg.project_name)
    table.add_row("package", cfg.package_name)
    table.add_row("preset", cfg.preset)
    table.add_row("database", cfg.database)
    table.add_row("api", "yes" if cfg.include_api else "no")
    table.add_row("docker", "yes" if cfg.include_docker else "no")
    table.add_row("target", str(target))
    console.print(Panel(table, title="djforge", border_style="green"))


def _init_git(target: Path) -> bool:
    try:
        subprocess.run(
            ["git", "init", "-q"],
            cwd=target,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "add", "-A"],
            cwd=target,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return True


@app.command()
def new(
    name: Annotated[str, typer.Argument(help="Project name to create.")],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory where the project is created."),
    ] = Path("."),
    preset: Annotated[
        TemplatePreset,
        typer.Option("--preset", "-p", help="Starter preset."),
    ] = "minimal",
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip prompts and use selected preset."),
    ] = False,
    git: Annotated[
        bool,
        typer.Option("--git/--no-git", help="Initialize a git repository."),
    ] = True,
    venv: Annotated[
        bool,
        typer.Option("--venv", help="Create a .venv after rendering."),
    ] = False,
) -> None:
    """Create a new Django project."""
    cfg = _copy_config(preset, name)
    if not yes:
        from djforge.tui.prompts import prompt

        cfg = prompt(cfg)

    target = output.expanduser().resolve() / cfg.slug
    if target.exists():
        console.print(f"[red]Target already exists:[/] {target}")
        raise typer.Exit(1)

    _print_summary(cfg, target)
    written = write_tree(target, build_file_map(cfg), cfg)

    env_example = target / ".env.example"
    if cfg.include_env and env_example.exists():
        shutil.copyfile(env_example, target / ".env")

    console.print(f"[green]Created {len(written)} files.[/]")

    if git:
        if _init_git(target):
            console.print("[dim]Initialized git repository.[/]")
        else:
            console.print("[yellow]git was unavailable; skipped repository init.[/]")

    if venv:
        subprocess.run([sys.executable, "-m", "venv", ".venv"], cwd=target, check=True)
        console.print("[dim]Created .venv.[/]")

    console.print()
    console.print(f"[bold green]Done.[/] cd {target.name}")
    console.print("Run: pip install -r requirements.txt && python manage.py migrate")


@app.command("list-presets")
def list_presets() -> None:
    """Show available presets."""
    table = Table("Preset", "Database", "API", "Docker", border_style="dim")
    for name, cfg in PRESETS.items():
        table.add_row(
            name,
            cfg.database,
            "yes" if cfg.include_api else "no",
            "yes" if cfg.include_docker else "no",
        )
    console.print(table)


@app.command()
def version() -> None:
    """Show the installed version."""
    console.print(f"djforge {__version__}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
