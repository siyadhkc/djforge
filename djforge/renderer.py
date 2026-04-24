"""Render a compact Django starter project."""

from __future__ import annotations

from pathlib import Path

from jinja2 import BaseLoader, Environment

from djforge.config import ProjectConfig


def _env() -> Environment:
    return Environment(
        loader=BaseLoader(),
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=True,
    )


def _template(source: str) -> str:
    return source.lstrip("\n")


def render(template: str, cfg: ProjectConfig) -> str:
    return _env().from_string(template).render(c=cfg)


def write_tree(root: Path, files: dict[str, str], cfg: ProjectConfig) -> list[str]:
    written: list[str] = []
    root.mkdir(parents=True, exist_ok=True)
    for rel_path, template in files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(template, cfg), encoding="utf-8", newline="\n")
        written.append(rel_path)
    return written


def build_file_map(cfg: ProjectConfig) -> dict[str, str]:
    package = cfg.package_name
    files = {
        ".gitignore": _template(
            """
__pycache__/
*.py[cod]
.env
.venv/
venv/
db.sqlite3
.pytest_cache/
htmlcov/
.coverage
staticfiles/
media/
"""
        ),
        ".env.example": _template(
            """
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
{% if c.uses_postgres -%}
DATABASE_URL=postgres://postgres:postgres@localhost:5432/{{ c.slug }}
{% else -%}
DATABASE_URL=sqlite:///db.sqlite3
{% endif -%}
"""
        ),
        "README.md": _template(
            """
# {{ c.project_name }}

{{ c.description }}

Generated with djforge.

## Quick Start

```bash
python -m venv .venv
.venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Included

- Django project package: `{{ c.package_name }}`
- Database: `{{ c.database }}`
{% if c.include_api -%}
- Django REST Framework health API at `/api/health/`
{% endif -%}
{% if c.include_docker -%}
- Dockerfile and docker-compose.yml
{% endif -%}
{% if c.include_pytest -%}
- pytest configuration and smoke tests
{% endif -%}
"""
        ),
        "requirements.txt": "\n".join(cfg.requirements) + "\n",
        "Makefile": _template(
            """
.DEFAULT_GOAL := help

.PHONY: help install migrate dev test

help:
\t@python -c "print('install  Install dependencies\\nmigrate  Run migrations\\ndev      Start Django\\ntest     Run tests')"

install:
\tpip install -r requirements.txt

migrate:
\tpython manage.py migrate

dev:
\tpython manage.py runserver

test:
\tpytest
"""
        ),
        "manage.py": _template(
            """
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ c.package_name }}.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
"""
        ),
        f"{package}/__init__.py": "",
        f"{package}/asgi.py": _template(
            """
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ c.package_name }}.settings")

application = get_asgi_application()
"""
        ),
        f"{package}/wsgi.py": _template(
            """
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ c.package_name }}.settings")

application = get_wsgi_application()
"""
        ),
        f"{package}/settings.py": _template(
            """
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
{% if c.include_api %}
    "rest_framework",
{% endif %}
    "{{ c.package_name }}.core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "{{ c.package_name }}.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "{{ c.package_name }}.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default="{% if c.uses_postgres %}postgres://postgres:postgres@localhost:5432/{{ c.slug }}{% else %}sqlite:///db.sqlite3{% endif %}")
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

{% if c.include_api %}
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}
{% endif %}
"""
        ),
        f"{package}/urls.py": _template(
            """
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("{{ c.package_name }}.core.urls")),
]
"""
        ),
        f"{package}/core/__init__.py": "",
        f"{package}/core/apps.py": _template(
            """
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "{{ c.package_name }}.core"
"""
        ),
        f"{package}/core/models.py": _template(
            """
# Create your models here.
"""
        ),
        f"{package}/core/views.py": _template(
            """
{% if c.include_api -%}
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})
{% else -%}
from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})
{% endif -%}
"""
        ),
        f"{package}/core/urls.py": _template(
            """
from django.urls import path

from .views import health

urlpatterns = [
    path("", health, name="home"),
{% if c.include_api %}
    path("api/health/", health, name="api-health"),
{% endif %}
]
"""
        ),
        f"{package}/core/tests.py": _template(
            """
from django.test import SimpleTestCase
from django.urls import reverse


class HealthTests(SimpleTestCase):
    def test_health_endpoint(self):
        response = self.client.get(reverse("home"))
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
"""
        ),
        "pyproject.toml": _template(
            """
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "{{ c.package_name }}.settings"
python_files = ["tests.py", "test_*.py", "*_tests.py"]

[tool.ruff]
line-length = 88
"""
        ),
    }

    if cfg.include_docker:
        files["Dockerfile"] = _template(
            """
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
"""
        )
        files["docker-compose.yml"] = _template(
            """
services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
{% if c.uses_postgres %}
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: {{ c.slug }}
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
{% endif %}
"""
        )
        files[".dockerignore"] = _template(
            """
.git
.env
.venv
__pycache__/
*.pyc
db.sqlite3
staticfiles/
"""
        )

    return files
