# ⚡ djforge

> The fast, modern Django project generator. Zero config. Sensible defaults.

```bash
pipx run djforge new myapp
```

---

## Why djforge?

[cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django) is powerful but heavy — it takes minutes to fill out, generates files you'll never use, and requires installing `cookiecutter` first.

**djforge** takes 30 seconds.

```
djforge new myapp          # interactive TUI
djforge new myapp --yes    # zero prompts, full defaults
djforge new myapp --preset api      # pure REST API stack
djforge new myapp --preset minimal  # SQLite, no Docker
```

---

## Install

```bash
# Recommended (no venv needed, globally available)
pipx install djforge

# Or plain pip
pip install djforge
```

---

## Usage

### Interactive mode (default)

```
$ djforge new myshop

⚡ djforge — fast Django project generator

  Project name:      myshop
  Short description: A Django project.
  Database:          ▸ PostgreSQL   SQLite
  Cache:             ▸ Redis        LocMem   None
  Auth:              ▸ Session      JWT      Both
  Frontend:          ▸ None         HTMX     HTMX+Tailwind   React
  Include:           [✓] Celery  [✓] Docker  [✓] DRF  [✓] Sentry ...

✅ myshop created!

  cd myshop
  make install && make migrate && make dev
```

### Non-interactive

```bash
# Accept all defaults
djforge new myapp --yes

# Use a preset
djforge new myapp --preset api
djforge new myapp --preset fullstack
djforge new myapp --preset minimal

# Custom output directory
djforge new myapp --output ~/projects

# With virtualenv creation
djforge new myapp --yes --venv

# Skip git init
djforge new myapp --yes --no-git
```

### List presets

```bash
djforge list-presets
```

| Preset | Database | Cache | Auth | Celery | Docker |
|--------|----------|-------|------|--------|--------|
| minimal | SQLite | locmem | session | — | — |
| api | PostgreSQL | Redis | JWT | ✓ | ✓ |
| fullstack | PostgreSQL | Redis | session | ✓ | ✓ |

---

## What you get

```
myapp/
├── manage.py
├── Makefile                    ← make dev / test / migrate / lint
├── Dockerfile                  ← multi-stage, non-root
├── docker-compose.yml          ← web + postgres + redis + celery
├── .env / .env.example
├── pyproject.toml              ← black + ruff + pytest config
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
└── myapp/
    ├── settings/
    │   ├── base.py             ← django-environ, DRF, Celery, cache
    │   ├── development.py      ← debug toolbar, console email
    │   ├── production.py       ← HTTPS headers, Sentry
    │   └── test.py             ← in-memory SQLite, fast hashers
    ├── celery.py
    ├── urls.py                 ← admin + API v1 + Swagger
    └── apps/
        ├── core/               ← /api/v1/health/
        └── users/              ← custom User (email login) + /api/v1/users/me/
```

### Included by default

| Feature | Details |
|---------|---------|
| **Custom User model** | Email-based login, set before first migration |
| **Split settings** | base / development / production / test |
| **Security headers** | HSTS, secure cookies, SSL redirect (production) |
| **DRF** | Django REST Framework + django-filter |
| **OpenAPI** | drf-spectacular → `/api/docs/` Swagger UI |
| **Celery** | Async tasks + beat scheduler via Redis |
| **Whitenoise** | Static files without nginx |
| **Sentry** | Auto-init from `SENTRY_DSN` env var |
| **Docker** | Multi-stage build, non-root user |
| **pytest** | `--reuse-db`, coverage, factory-boy |
| **Makefile** | `make dev`, `make test`, `make lint`, `make format` |

---

## Stack comparison

| | djforge | cookiecutter-django |
|--|---------|---------------------|
| Time to first project | ~10s | 3–5 min |
| Config required | Zero (`--yes`) | Long questionnaire |
| Install required | `pipx run djforge` | `pip install cookiecutter` + clone |
| Jinja templates | Yes | Yes |
| Interactive TUI | Yes (questionary) | Text prompts |
| Presets | Yes | No |
| Django version | 5.x | 4.x + 5.x |
| Python version | 3.11+ | 3.10+ |

---

## Development

```bash
git clone https://github.com/siyadhkc/djforge
cd djforge
pip install -e ".[dev]"
pytest
```

### Project structure

```
djforge/
├── djforge/
│   ├── cli.py        ← typer CLI entry point
│   ├── config.py     ← ProjectConfig dataclass + presets
│   ├── renderer.py   ← Jinja2 template engine + file map
│   └── tui/
│       └── prompts.py  ← questionary interactive prompts
└── tests/
    └── test_core.py
```

---

## Contributing

PRs welcome! Please open an issue first for large changes.

1. Fork the repo
2. Create a feature branch
3. Add tests
4. `pytest && ruff check .`
5. Open a PR

---

## License

MIT © djforge contributors
