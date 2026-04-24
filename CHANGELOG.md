# Changelog

## [0.2.0] - 2026-04-24

### Changed
- Rebuilt djforge as a small cookiecutter-style Django CLI.
- Simplified generated projects to a clean single-settings Django layout.
- Replaced the heavy scaffold with `minimal`, `api`, and `fullstack` presets.
- Kept generated output focused: `manage.py`, `requirements.txt`, `.env`, `Makefile`, `pyproject.toml`, and a `core` health endpoint.
- Made API and Docker/PostgreSQL support optional through presets.
- Updated tests around the new generator behavior.
- Updated README for the new CLI workflow.

## [0.1.0] — 2026-04

### Added
- `djforge new <name>` — generate a Django project
- Interactive TUI (questionary) with database, cache, auth, frontend, feature toggles
- `--yes` flag for zero-prompt generation
- `--preset minimal|api|fullstack` presets
- `--venv` flag to create a virtualenv post-generation
- `--output` flag for custom output directory
- `djforge list-presets` command
- `djforge version` command
- Jinja2-based template renderer with full config context
- Docker + Docker Compose (multi-stage, non-root)
- Split settings: base / development / production / test
- Custom User model (email-based login)
- Django REST Framework + drf-spectacular (Swagger)
- Celery + Redis support
- Whitenoise static files
- Sentry integration (production)
- pytest + coverage setup
- Makefile shortcuts
- git init on generation
