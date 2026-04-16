"""
djforge.tui
~~~~~~~~~~~
Interactive prompts using questionary + rich.
Only shown when the user did NOT pass --yes / --preset.
"""
from __future__ import annotations

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from djforge.config import ProjectConfig

console = Console()

STYLE = questionary.Style([
    ("qmark",        "fg:#f4c542 bold"),
    ("question",     "bold"),
    ("answer",       "fg:#62d4a0 bold"),
    ("pointer",      "fg:#f4c542 bold"),
    ("highlighted",  "fg:#f4c542 bold"),
    ("selected",     "fg:#62d4a0"),
    ("separator",    "fg:#555555"),
    ("instruction",  "fg:#888888"),
])


def prompt(cfg: ProjectConfig) -> ProjectConfig:
    """Walk the user through every configurable option."""

    console.print()
    console.print(Panel(
        Text("⚡  djforge", style="bold yellow") +
        Text("  —  fast Django project generator", style="dim white"),
        border_style="yellow",
        padding=(0, 2),
    ))
    console.print()

    # ── project name ─────────────────────────────────────────────────────────
    cfg.project_name = questionary.text(
        "Project name:",
        default=cfg.project_name,
        validate=lambda v: bool(v.strip()) or "Name cannot be empty",
        style=STYLE,
    ).ask() or cfg.project_name

    cfg.description = questionary.text(
        "Short description:",
        default=cfg.description,
        style=STYLE,
    ).ask() or cfg.description

    cfg.author = questionary.text(
        "Author name / org:",
        default=cfg.author,
        style=STYLE,
    ).ask() or cfg.author

    # ── database ─────────────────────────────────────────────────────────────
    cfg.database = questionary.select(
        "Database:",
        choices=[
            questionary.Choice("PostgreSQL  (recommended)", value="postgres"),
            questionary.Choice("SQLite      (quick start)", value="sqlite"),
        ],
        default="postgres",
        style=STYLE,
    ).ask() or cfg.database  # type: ignore[assignment]

    # ── cache ─────────────────────────────────────────────────────────────────
    cfg.cache = questionary.select(
        "Cache backend:",
        choices=[
            questionary.Choice("Redis       (recommended)", value="redis"),
            questionary.Choice("LocMem      (dev only)",    value="locmem"),
            questionary.Choice("None / dummy",              value="dummy"),
        ],
        default="redis",
        style=STYLE,
    ).ask() or cfg.cache  # type: ignore[assignment]

    # ── auth ─────────────────────────────────────────────────────────────────
    cfg.auth = questionary.select(
        "Authentication strategy:",
        choices=[
            questionary.Choice("Session     (classic Django)",    value="session"),
            questionary.Choice("JWT         (djangorestframework-simplejwt)", value="jwt"),
            questionary.Choice("Both        (session + JWT)",     value="both"),
        ],
        style=STYLE,
    ).ask() or cfg.auth  # type: ignore[assignment]

    # ── frontend ──────────────────────────────────────────────────────────────
    cfg.frontend = questionary.select(
        "Frontend:",
        choices=[
            questionary.Choice("None        (API only)",           value="none"),
            questionary.Choice("HTMX        (server-side hypermedia)", value="htmx"),
            questionary.Choice("HTMX + Tailwind CSS",              value="htmx+tailwind"),
            questionary.Choice("React       (separate SPA)",       value="react"),
        ],
        style=STYLE,
    ).ask() or cfg.frontend  # type: ignore[assignment]

    # ── feature toggles ───────────────────────────────────────────────────────
    console.print()
    console.print("  [dim]— Optional features —[/dim]")
    console.print()

    toggles = questionary.checkbox(
        "Include:",
        choices=[
            questionary.Choice("Celery  (async tasks)",      value="celery",    checked=True),
            questionary.Choice("Docker  (Dockerfile + Compose)", value="docker", checked=True),
            questionary.Choice("Sentry  (error tracking)",   value="sentry",    checked=True),
            questionary.Choice("DRF     (REST framework)",   value="drf",       checked=True),
            questionary.Choice("Swagger (drf-spectacular)",  value="swagger",   checked=True),
            questionary.Choice("Whitenoise (static files)",  value="whitenoise",checked=True),
            questionary.Choice("pytest  (test suite)",       value="pytest",    checked=True),
            questionary.Choice("Ruff    (fast linter)",      value="ruff",      checked=True),
        ],
        style=STYLE,
    ).ask() or []

    cfg.use_celery     = "celery"     in toggles
    cfg.use_docker     = "docker"     in toggles
    cfg.use_sentry     = "sentry"     in toggles
    cfg.use_drf        = "drf"        in toggles
    cfg.use_swagger    = "swagger"    in toggles
    cfg.use_whitenoise = "whitenoise" in toggles
    cfg.use_pytest     = "pytest"     in toggles
    cfg.use_ruff       = "ruff"       in toggles

    return cfg
