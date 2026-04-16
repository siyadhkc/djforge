"""
djforge.renderer
~~~~~~~~~~~~~~~~
Renders the project tree from Jinja2 templates (or plain strings)
into the target directory.
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import BaseLoader, Environment

from djforge.config import ProjectConfig


def _env() -> Environment:
    return Environment(
        loader=BaseLoader(),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render(template: str, cfg: ProjectConfig) -> str:
    """Render a Jinja2 template string with config context."""
    return _env().from_string(template).render(c=cfg, cfg=cfg)


def write_tree(root: Path, files: dict[str, str], cfg: ProjectConfig) -> list[str]:
    """
    Write every key→value in `files` under `root`.
    Keys are relative paths; values are Jinja2 template strings.
    Returns list of written relative paths.
    """
    written: list[str] = []
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(content, cfg), encoding="utf-8")
        written.append(rel)
    return written


# ── Tiny helper so templates stay readable ───────────────────────────────────

def _t(s: str) -> str:
    """Strip leading newline from triple-quoted strings."""
    return s.lstrip("\n")


# ══════════════════════════════════════════════════════════════════════════════
# FILE TEMPLATES
# Every value is a Jinja2 template; `c` is the ProjectConfig.
# ══════════════════════════════════════════════════════════════════════════════

def build_file_map(cfg: ProjectConfig) -> dict[str, str]:
    slug = cfg.slug
    files: dict[str, str] = {}

    # ── manage.py ────────────────────────────────────────────────────────────
    files["manage.py"] = _t("""
#!/usr/bin/env python
import os, sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ c.slug }}.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django.") from exc
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
""")

    # ── requirements ─────────────────────────────────────────────────────────
    files["requirements/base.txt"] = _t("""
Django~={{ c.django_version }}
django-environ>=0.11
{% if c.use_drf %}
djangorestframework>=3.15
django-filter>=24
{% endif %}
{% if c.use_swagger and c.use_drf %}
drf-spectacular>=0.27
{% endif %}
{% if c.auth in ("jwt","both") and c.use_drf %}
djangorestframework-simplejwt>=5
{% endif %}
django-extensions>=3.2
Pillow>=10
gunicorn>=22
{% if c.database == "postgres" %}
psycopg[binary]>=3
{% endif %}
{% if c.needs_redis %}
redis>=5
{% endif %}
{% if c.use_celery %}
celery[redis]>=5
{% endif %}
{% if c.use_whitenoise %}
whitenoise[brotli]>=6
{% endif %}
""")

    files["requirements/development.txt"] = _t("""
-r base.txt
django-debug-toolbar>=4
ipython
{% if c.use_pytest %}
pytest-django>=4
pytest-cov
factory-boy>=3
{% endif %}
black
isort
{% if c.use_ruff %}
ruff
{% endif %}
""")

    files["requirements/production.txt"] = _t("""
-r base.txt
{% if c.use_sentry %}
sentry-sdk[django]>=2
{% endif %}
""")

    # ── .env.example ──────────────────────────────────────────────────────────
    files[".env.example"] = _t("""
# ── Django ───────────────────────────────────────────
DJANGO_ENV=development
DJANGO_SECRET_KEY=changeme-replace-with-python-secrets-token-hex-64
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# ── Database ─────────────────────────────────────────
DATABASE_URL={{ c.db_url_example }}

{% if c.needs_redis %}
# ── Redis ─────────────────────────────────────────────
REDIS_URL=redis://{% if c.use_docker %}redis{% else %}127.0.0.1{% endif %}:6379/0
{% endif %}

# ── Email ─────────────────────────────────────────────
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@example.com

{% if c.use_sentry %}
# ── Sentry ────────────────────────────────────────────
SENTRY_DSN=
{% endif %}
""")

    # ── settings/base.py ─────────────────────────────────────────────────────
    files[f"{slug}/settings/__init__.py"] = ""
    files[f"{slug}/settings/base.py"] = _t("""
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY    = env("DJANGO_SECRET_KEY")
DEBUG         = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost"])

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    {% if c.use_drf %}"rest_framework",{% endif %}
    {% if c.use_swagger and c.use_drf %}"drf_spectacular",{% endif %}
    {% if c.use_drf %}"django_filters",{% endif %}
    "django_extensions",
]

LOCAL_APPS = [
    "{{ c.slug }}.apps.core",
    "{{ c.slug }}.apps.users",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    {% if c.use_whitenoise %}"whitenoise.middleware.WhiteNoiseMiddleware",{% endif %}
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF      = "{{ c.slug }}.urls"
WSGI_APPLICATION  = "{{ c.slug }}.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

DATABASES = {
    "default": env.db("DATABASE_URL", default="{{ c.db_url_example }}")
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"]    = env.int("CONN_MAX_AGE", default=60)

{% if c.cache == "redis" %}
CACHES = {
    "default": {
        "BACKEND":  "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/0"),
    }
}
{% elif c.cache == "locmem" %}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
{% endif %}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE     = "UTC"
USE_I18N      = True
USE_TZ        = True

STATIC_URL   = "/static/"
STATIC_ROOT  = BASE_DIR / "staticfiles"
MEDIA_URL    = "/media/"
MEDIA_ROOT   = BASE_DIR / "media"

{% if c.use_whitenoise %}
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}
{% endif %}

{% if c.use_drf %}
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        {% if c.auth in ("jwt","both") %}
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        {% endif %}
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    {% if c.use_swagger %}
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    {% endif %}
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
{% endif %}

{% if c.use_swagger and c.use_drf %}
SPECTACULAR_SETTINGS = {
    "TITLE":   "{{ c.project_name|title }} API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
{% endif %}

{% if c.use_celery %}
CELERY_BROKER_URL        = env("REDIS_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND    = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT    = ["json"]
CELERY_TASK_SERIALIZER   = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE          = TIME_ZONE
{% endif %}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
""")

    files[f"{slug}/settings/development.py"] = _t("""
from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += ["debug_toolbar"]  # noqa
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE  # noqa
INTERNAL_IPS = ["127.0.0.1"]

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
""")

    files[f"{slug}/settings/production.py"] = _t("""
from .base import *  # noqa
import environ
env = environ.Env()

DEBUG = False

SECURE_SSL_REDIRECT            = True
SECURE_PROXY_SSL_HEADER        = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS            = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD            = True
SESSION_COOKIE_SECURE          = True
CSRF_COOKIE_SECURE             = True

{% if c.use_sentry %}
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if dsn := env("SENTRY_DSN", default=""):
    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
{% endif %}
""")

    files[f"{slug}/settings/test.py"] = _t("""
from .development import *  # noqa

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
}
""")

    # ── urls.py ───────────────────────────────────────────────────────────────
    files[f"{slug}/urls.py"] = _t("""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
{% if c.use_swagger and c.use_drf %}
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
{% endif %}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("{{ c.slug }}.apps.core.urls")),
    {% if c.use_drf %}
    path("api/v1/users/", include("{{ c.slug }}.apps.users.urls")),
    {% endif %}
    {% if c.use_swagger and c.use_drf %}
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    {% endif %}
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
""")

    # ── wsgi / asgi ───────────────────────────────────────────────────────────
    files[f"{slug}/wsgi.py"] = _t("""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ c.slug }}.settings.production")
application = get_wsgi_application()
""")

    files[f"{slug}/asgi.py"] = _t("""
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ c.slug }}.settings.production")
application = get_asgi_application()
""")

    # ── package init ──────────────────────────────────────────────────────────
    files[f"{slug}/__init__.py"] = (
        "from .celery import app as celery_app\n__all__ = ('celery_app',)\n"
        if cfg.use_celery else ""
    )

    # ── celery ────────────────────────────────────────────────────────────────
    if cfg.use_celery:
        files[f"{slug}/celery.py"] = _t("""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ c.slug }}.settings.development")
app = Celery("{{ c.slug }}")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
""")

    # ── apps/users ────────────────────────────────────────────────────────────
    files[f"{slug}/apps/__init__.py"] = ""
    files[f"{slug}/apps/users/__init__.py"] = ""
    files[f"{slug}/apps/users/migrations/__init__.py"] = ""
    files[f"{slug}/apps/users/migrations/0001_initial.py"] = _t("""
from django.contrib.auth.models import UserManager
import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("username", models.CharField(error_messages={"unique": "A user with that username already exists."}, help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.", max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name="username")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
            managers=[
                ("objects", UserManager()),
            ],
        ),
    ]
""")

    files[f"{slug}/apps/users/models.py"] = _t("""
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name       = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email
""")

    files[f"{slug}/apps/users/serializers.py"] = _t("""
{% if c.use_drf %}
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ["id", "username", "email", "first_name", "last_name", "date_joined"]
        read_only_fields = ["id", "date_joined"]
{% else %}
# DRF is disabled for this project preset.
{% endif %}
""")

    files[f"{slug}/apps/users/views.py"] = _t("""
{% if c.use_drf %}
from rest_framework import generics, permissions
from .serializers import UserSerializer

class MeView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
{% else %}
# DRF is disabled for this project preset.
{% endif %}
""")

    files[f"{slug}/apps/users/urls.py"] = _t("""
{% if c.use_drf %}
from django.urls import path
from .views import MeView

urlpatterns = [
    path("me/", MeView.as_view(), name="users-me"),
]
{% else %}
urlpatterns = []
{% endif %}
""")

    files[f"{slug}/apps/users/admin.py"] = _t("""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as Base
from .models import User

@admin.register(User)
class UserAdmin(Base):
    list_display  = ("email", "username", "is_staff", "date_joined")
    search_fields = ("email", "username")
    ordering      = ("-date_joined",)
""")

    files[f"{slug}/apps/users/apps.py"] = _t("""
from django.apps import AppConfig

class UsersConfig(AppConfig):
    name = "{{ c.slug }}.apps.users"
    default_auto_field = "django.db.models.BigAutoField"
""")

    files[f"{slug}/apps/users/tests/__init__.py"] = ""
    files[f"{slug}/apps/users/tests/test_views.py"] = _t("""
{% if c.use_drf %}
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_me_unauthenticated(client):
    assert client.get(reverse("users-me")).status_code == 403

@pytest.mark.django_db
def test_me_authenticated(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="alice", email="alice@example.com", password="pass"
    )
    client.force_login(user)
    r = client.get(reverse("users-me"))
    assert r.status_code == 200
    assert r.data["email"] == "alice@example.com"
{% else %}
def test_placeholder():
    assert True
{% endif %}
""")

    # ── apps/core ────────────────────────────────────────────────────────────
    files[f"{slug}/apps/core/__init__.py"] = ""
    files[f"{slug}/apps/core/migrations/__init__.py"] = ""

    files[f"{slug}/apps/core/apps.py"] = _t("""
from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = "{{ c.slug }}.apps.core"
""")

    files[f"{slug}/apps/core/models.py"] = _t("""
# Place shared abstract models here, e.g.:
#
# from django.db import models
#
# class TimestampedModel(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     class Meta:
#         abstract = True
""")

    files[f"{slug}/apps/core/views.py"] = _t("""
{% if c.use_drf %}
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok"})
{% else %}
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "ok"})
{% endif %}
""")

    files[f"{slug}/apps/core/urls.py"] = _t("""
from django.urls import path
from .views import health_check

urlpatterns = [
    path("health/", health_check, name="health-check"),
]
""")

    # ── Docker ────────────────────────────────────────────────────────────────
    if cfg.use_docker:
        files["Dockerfile"] = _t("""
FROM python:{{ c.python_version }}-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements/production.txt .
RUN pip install --upgrade pip && pip wheel --no-cache-dir --wheel-dir /wheels -r production.txt

FROM python:{{ c.python_version }}-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && \\
    rm -rf /var/lib/apt/lists/* && \\
    addgroup --system django && adduser --system --ingroup django django

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

COPY . .
RUN python manage.py collectstatic --noinput --settings={{ c.slug }}.settings.production

USER django
EXPOSE $PORT
CMD ["sh", "-c", "gunicorn {{ c.slug }}.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 60 --access-logfile -"]
""")

        files["docker-compose.yml"] = _t("""
version: "3.9"

services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes: [".:/app"]
    ports: ["8000:8000"]
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: {{ c.slug }}.settings.development
    depends_on:
      {% if c.database == "postgres" %}- db{% endif %}
      {% if c.needs_redis %}- redis{% endif %}
    restart: unless-stopped

  {% if c.database == "postgres" %}
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    volumes: ["postgres_data:/var/lib/postgresql/data"]
    environment:
      POSTGRES_DB: {{ c.slug }}
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
  {% endif %}

  {% if c.needs_redis %}
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports: ["6379:6379"]
  {% endif %}

  {% if c.use_celery %}
  celery:
    build: .
    command: celery -A {{ c.slug }} worker -l info
    env_file: .env
    depends_on: [db, redis]
    restart: unless-stopped

  celery-beat:
    build: .
    command: celery -A {{ c.slug }} beat -l info
    env_file: .env
    depends_on: [db, redis]
    restart: unless-stopped
  {% endif %}

{% if c.database == "postgres" %}
volumes:
  postgres_data:
{% endif %}
""")

        files[".dockerignore"] = _t("""
__pycache__/
*.pyc
.env
.venv
venv/
*.egg-info/
staticfiles/
media/
.pytest_cache/
.coverage
htmlcov/
.git
""")

    # ── tooling ───────────────────────────────────────────────────────────────
    files["pyproject.toml"] = _t("""
[tool.black]
line-length = 88
target-version = ["py{{ c.python_version | replace('.','') }}"]

{% if c.use_ruff %}
[tool.ruff]
line-length = 88
select = ["E","F","I","UP","B","C4","N"]
ignore = ["E501"]

[tool.ruff.per-file-ignores]
"*/migrations/*.py" = ["ALL"]
"*/settings/*.py"   = ["F403","F405"]
{% endif %}

{% if c.use_pytest %}
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "{{ c.slug }}.settings.test"
python_files = ["test_*.py","*_tests.py"]
addopts = "--reuse-db -x"

[tool.coverage.run]
source = ["{{ c.slug }}"]
omit   = ["*/migrations/*","*/tests/*","manage.py"]
{% endif %}
""")

    files[".gitignore"] = _t("""
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.Python
.git
.env
.env.*
!.env.example
.venv
venv/
db.sqlite3
media/
staticfiles/
.coverage
htmlcov/
.pytest_cache/
.vscode/
.idea/
""")

    files["Makefile"] = _t("""
.DEFAULT_GOAL := help
.PHONY: help install dev migrate superuser test lint format shell \
{% if c.use_docker %}docker-up docker-down{% endif %}


help:
\t@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \\
\t awk 'BEGIN {FS=":.*?## "}; {printf "\\033[36m%-18s\\033[0m %s\\n",$$1,$$2}'

install: ## Install dev dependencies
\tpip install -r requirements/development.txt

dev: ## Run dev server
\tDJANGO_SETTINGS_MODULE={{ c.slug }}.settings.development python manage.py runserver

migrate: ## Run migrations
\tpython manage.py migrate

makemigrations: ## Make migrations
\tpython manage.py makemigrations

superuser: ## Create superuser
\tpython manage.py createsuperuser

{% if c.use_pytest %}
test: ## Run test suite
\tpytest --cov={{ c.slug }} --cov-report=html
{% endif %}

lint: ## Lint code
\t{% if c.use_ruff %}ruff check . && {% endif %}isort --check-only .

format: ## Auto-format
\tblack . && isort .

shell: ## Django shell
\tpython manage.py shell_plus

{% if c.use_docker %}
docker-up: ## Start Docker services
\tdocker compose up -d

docker-down: ## Stop Docker services
\tdocker compose down

docker-logs: ## Tail Docker logs
\tdocker compose logs -f
{% endif %}
""")

    # ── README ────────────────────────────────────────────────────────────────
    files["README.md"] = _t("""
# {{ c.project_name }}

> {{ c.description }}
> Generated with [djforge](https://github.com/siyadhkc/djforge) ⚡

## Stack

| Layer | Choice |
|-------|--------|
| Framework | Django {{ c.django_version }} |
| Database  | {{ c.database | title }} |
| Cache     | {{ c.cache | title }} |
| Auth      | {{ c.auth | title }} |
{% if c.use_drf %}| API       | Django REST Framework |{% endif %}
{% if c.use_celery %}| Tasks     | Celery + Redis |{% endif %}
{% if c.use_docker %}| Container | Docker + Compose |{% endif %}

## Quick start

```bash
cp .env.example .env    # ← fill in your values
make install
make migrate
make superuser
make dev
```

{% if c.use_docker %}
## Docker

```bash
cp .env.example .env
docker compose up --build
```
{% endif %}

## API

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/health/` | Public health check |
| GET/PATCH | `/api/v1/users/me/` | Auth required |
{% if c.use_swagger %}| GET | `/api/docs/` | Swagger UI |{% endif %}
| ANY | `/admin/` | Django admin |

## Settings

```
{{ c.slug }}.settings.development  ← local dev
{{ c.slug }}.settings.production   ← deploy
{{ c.slug }}.settings.test         ← pytest
```
""")

    return files
