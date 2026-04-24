"""Small interactive prompt layer for djforge."""

from __future__ import annotations

from dataclasses import replace

import questionary

from djforge.config import ProjectConfig


def prompt(cfg: ProjectConfig) -> ProjectConfig:
    """Ask only the questions that change the generated starter."""
    project_name = questionary.text(
        "Project name",
        default=cfg.project_name,
        validate=lambda value: bool(value.strip()) or "Project name is required",
    ).ask()
    if project_name is None:
        raise KeyboardInterrupt

    description = questionary.text(
        "Description",
        default=cfg.description,
    ).ask()
    if description is None:
        raise KeyboardInterrupt

    database = questionary.select(
        "Database",
        choices=[
            questionary.Choice("SQLite", value="sqlite"),
            questionary.Choice("PostgreSQL", value="postgres"),
        ],
        default=cfg.database,
    ).ask()
    if database is None:
        raise KeyboardInterrupt

    include_api = questionary.confirm(
        "Include Django REST Framework API?",
        default=cfg.include_api,
    ).ask()
    if include_api is None:
        raise KeyboardInterrupt

    include_docker = questionary.confirm(
        "Include Docker files?",
        default=cfg.include_docker,
    ).ask()
    if include_docker is None:
        raise KeyboardInterrupt

    return replace(
        cfg,
        project_name=project_name,
        description=description or cfg.description,
        database=database,
        include_api=include_api,
        include_docker=include_docker,
    )
