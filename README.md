# djforge

A small CLI that generates simple Django starter projects. Think of it as a tiny,
focused cousin of cookiecutter-django: fewer questions, fewer files, quick output.

## Install

```bash
pip install djforge
```

For local development:

```bash
pip install -e ".[dev]"
```

## Usage

Create a basic Django project with SQLite:

```bash
djforge new mysite --yes
```

Create an API starter with Django REST Framework:

```bash
djforge new myapi --preset api --yes
```

Create a fuller Docker/PostgreSQL starter:

```bash
djforge new myshop --preset fullstack --yes
```

Use prompts instead of `--yes`:

```bash
djforge new mysite
```

List available presets:

```bash
djforge list-presets
```

## Presets

| Preset | Database | API | Docker |
| --- | --- | --- | --- |
| minimal | SQLite | no | no |
| api | SQLite | yes | no |
| fullstack | PostgreSQL | yes | yes |

## Generated Project

The generated project includes:

- `manage.py`
- one Django settings module
- a `core` app with a JSON health endpoint
- `.env.example` and copied `.env`
- `requirements.txt`
- `Makefile`
- `pyproject.toml`
- optional DRF, Dockerfile, and docker-compose.yml

Example:

```text
mysite/
├── manage.py
├── requirements.txt
├── Makefile
├── .env.example
├── pyproject.toml
└── mysite/
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    ├── wsgi.py
    └── core/
        ├── apps.py
        ├── urls.py
        ├── views.py
        └── tests.py
```

## Development

```bash
python -m pytest -p no:cacheprovider
python -m py_compile djforge\config.py djforge\renderer.py djforge\cli.py
```

## Release

1. Update `version` in `pyproject.toml` and `__version__` in `djforge/__init__.py`.
2. Add a changelog entry.
3. Run checks:

```bash
python -m pytest tests/test_core.py tests/test_e2e.py -q -p no:cacheprovider
python -m ruff check djforge tests
python -m hatch build
```

4.Upload only the new version files:

```bash
python -m twine upload dist/djforge-0.2.0.tar.gz dist/djforge-0.2.0-py3-none-any.whl
```
