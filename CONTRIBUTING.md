# Contributing to djforge

Thanks for wanting to improve djforge! This guide covers everything you need.

## Development setup

```bash
git clone https://github.com/siyadhkc/djforge
cd djforge
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Optional dev extras in pyproject.toml

Add this to `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
dev = [
    "pytest", "pytest-cov", "black", "ruff", "isort", "hatch"
]
```

## Project layout

```
djforge/
├── djforge/
│   ├── cli.py          ← typer commands (new, list-presets, version)
│   ├── config.py       ← ProjectConfig dataclass + PRESETS dict
│   ├── renderer.py     ← Jinja2 templates + write_tree()
│   └── tui/
│       └── prompts.py  ← interactive questionary flow
└── tests/
    └── test_core.py
```

## Common tasks

```bash
pytest                          # run all tests
pytest -x -v                    # stop on first failure, verbose
pytest tests/ -k "test_slug"    # run matching tests only

black djforge/ tests/           # format
ruff check djforge/             # lint
isort djforge/ tests/           # import order
```

## Adding a new stack option

Say you want to add `use_dramatiq` as an alternative to Celery.

**1. Add to `config.py`:**
```python
@dataclass
class ProjectConfig:
    ...
    use_dramatiq: bool = False
```

**2. Add to `renderer.py` — `build_file_map()`:**
```python
# In requirements/base.txt template:
{% if c.use_dramatiq %}
dramatiq[redis]>=1.15
{% endif %}
```

**3. Add to `tui/prompts.py`:**
```python
questionary.Choice("Dramatiq (async tasks, alt to Celery)", value="dramatiq", checked=False),
```
and handle the result in the toggle block.

**4. Write tests in `tests/test_core.py`.**

## Adding a preset

In `config.py`, add to the `PRESETS` dict:

```python
PRESETS["mypreset"] = ProjectConfig(
    database="postgres",
    use_celery=False,
    use_docker=True,
    # ...
)
```

Then add a test:

```python
def test_mypreset_has_docker():
    assert PRESETS["mypreset"].use_docker is True
```

## Submitting a PR

1. Fork → branch off `main` → make changes
2. `pytest && ruff check djforge/ && black --check djforge/ tests/`
3. Update `CHANGELOG.md` under `[Unreleased]`
4. Open a PR — fill in the template

## Releasing (maintainers only)

```bash
# Bump version in djforge/__init__.py and pyproject.toml
# Update CHANGELOG.md — rename [Unreleased] → [x.y.z] with date
git tag v0.2.0
git push origin v0.2.0
# GitHub Actions handles the rest (build → PyPI → GitHub Release)
```

## Code style

- **black** for formatting (line length 88)
- **ruff** for linting
- **isort** for import order (profile = black)
- Type hints on all public functions
- Docstrings on modules and non-trivial functions
