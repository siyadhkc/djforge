"""
djforge.config
~~~~~~~~~~~~~~
Dataclasses that hold every decision about a new project.
All values have defaults so `djforge new myapp` works with zero interaction.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


DatabaseBackend  = Literal["postgres", "sqlite"]
CacheBackend     = Literal["redis", "locmem", "dummy"]
AuthStrategy     = Literal["session", "jwt", "both"]
FrontendChoice   = Literal["none", "htmx", "htmx+tailwind", "react"]


@dataclass
class ProjectConfig:
    # ── Identity ──────────────────────────────────────────────────────────────
    project_name:    str  = "myproject"
    description:     str  = "A Django project."
    author:          str  = ""
    python_version:  str  = "3.12"
    django_version:  str  = "5.0"

    # ── Stack ─────────────────────────────────────────────────────────────────
    database:   DatabaseBackend = "postgres"
    cache:      CacheBackend    = "redis"
    auth:       AuthStrategy    = "session"
    frontend:   FrontendChoice  = "none"

    # ── Features (toggle) ─────────────────────────────────────────────────────
    use_celery:    bool = True
    use_docker:    bool = True
    use_whitenoise: bool = True
    use_sentry:    bool = True
    use_drf:       bool = True
    use_swagger:   bool = True
    use_pytest:    bool = True
    use_ruff:      bool = True

    # ── Derived helpers ───────────────────────────────────────────────────────
    @property
    def slug(self) -> str:
        """Python-safe package name."""
        import re
        return re.sub(r"[^a-z0-9_]", "_", self.project_name.lower())

    @property
    def needs_redis(self) -> bool:
        return self.cache == "redis" or self.use_celery

    @property
    def db_package(self) -> str:
        return "psycopg[binary]>=3" if self.database == "postgres" else ""

    @property
    def db_url_example(self) -> str:
        if self.database == "postgres":
            return f"postgres://postgres:postgres@db:5432/{self.slug}"
        return f"sqlite:///db.sqlite3"


# ── Preset profiles ───────────────────────────────────────────────────────────

PRESETS: dict[str, ProjectConfig] = {
    "minimal": ProjectConfig(
        database="sqlite",
        cache="locmem",
        use_celery=False,
        use_docker=False,
        use_sentry=False,
        use_swagger=False,
    ),
    "api": ProjectConfig(
        database="postgres",
        cache="redis",
        auth="jwt",
        use_celery=True,
        use_docker=True,
        use_drf=True,
        use_swagger=True,
    ),
    "fullstack": ProjectConfig(
        database="postgres",
        cache="redis",
        auth="session",
        frontend="htmx+tailwind",
        use_celery=True,
        use_docker=True,
        use_drf=True,
        use_swagger=True,
    ),
}
