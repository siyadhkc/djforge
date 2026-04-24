"""End-to-end tests for the djforge CLI."""

import subprocess
import sys

import pytest


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "djforge.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_new_yes_creates_minimal_project(workspace_tmp):
    result = run_cli(
        "new", "smoke-app", "--yes", "--no-git", "--output", str(workspace_tmp)
    )
    assert result.returncode == 0, result.stderr
    root = workspace_tmp / "smoke_app"
    assert (root / "manage.py").exists()
    assert (root / "smoke_app" / "settings.py").exists()
    assert (root / "smoke_app" / "core" / "views.py").exists()


def test_new_yes_writes_env_files(workspace_tmp):
    result = run_cli(
        "new", "envtest", "--yes", "--no-git", "--output", str(workspace_tmp)
    )
    assert result.returncode == 0, result.stderr
    assert (workspace_tmp / "envtest" / ".env").exists()
    assert (workspace_tmp / "envtest" / ".env.example").exists()


def test_new_exits_if_dir_exists(workspace_tmp):
    run_cli("new", "exists", "--yes", "--no-git", "--output", str(workspace_tmp))
    result = run_cli(
        "new", "exists", "--yes", "--no-git", "--output", str(workspace_tmp)
    )
    assert result.returncode != 0
    assert "already exists" in result.stdout


@pytest.mark.parametrize("preset", ["minimal", "api", "fullstack"])
def test_presets_generate(workspace_tmp, preset):
    result = run_cli(
        "new",
        f"{preset}-project",
        "--yes",
        "--preset",
        preset,
        "--no-git",
        "--output",
        str(workspace_tmp),
    )
    assert result.returncode == 0, result.stderr
    assert (workspace_tmp / f"{preset}_project" / "manage.py").exists()


def test_minimal_preset_skips_api_and_docker(workspace_tmp):
    run_cli(
        "new",
        "minapp",
        "--yes",
        "--preset",
        "minimal",
        "--no-git",
        "--output",
        str(workspace_tmp),
    )
    root = workspace_tmp / "minapp"
    assert not (root / "Dockerfile").exists()
    settings = (root / "minapp" / "settings.py").read_text(encoding="utf-8")
    assert "rest_framework" not in settings


def test_api_preset_includes_drf(workspace_tmp):
    run_cli(
        "new",
        "apiapp",
        "--yes",
        "--preset",
        "api",
        "--no-git",
        "--output",
        str(workspace_tmp),
    )
    root = workspace_tmp / "apiapp"
    settings = (root / "apiapp" / "settings.py").read_text(encoding="utf-8")
    requirements = (root / "requirements.txt").read_text(encoding="utf-8")
    assert "rest_framework" in settings
    assert "djangorestframework" in requirements


def test_fullstack_preset_has_docker_and_postgres(workspace_tmp):
    run_cli(
        "new",
        "fullapp",
        "--yes",
        "--preset",
        "fullstack",
        "--no-git",
        "--output",
        str(workspace_tmp),
    )
    root = workspace_tmp / "fullapp"
    assert (root / "Dockerfile").exists()
    assert "psycopg" in (root / "requirements.txt").read_text(encoding="utf-8")


def test_version_command():
    result = run_cli("version")
    assert result.returncode == 0
    assert "djforge" in result.stdout


def test_list_presets_command():
    result = run_cli("list-presets")
    assert result.returncode == 0
    for preset in ("minimal", "api", "fullstack"):
        assert preset in result.stdout


def test_generated_python_files_are_syntax_valid(workspace_tmp):
    result = run_cli(
        "new",
        "syntaxapp",
        "--yes",
        "--preset",
        "api",
        "--no-git",
        "--output",
        str(workspace_tmp),
    )
    assert result.returncode == 0, result.stderr
    root = workspace_tmp / "syntaxapp"
    for path in [
        root / "manage.py",
        root / "syntaxapp" / "settings.py",
        root / "syntaxapp" / "urls.py",
        root / "syntaxapp" / "core" / "views.py",
    ]:
        compiled = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
        )
        assert compiled.returncode == 0, compiled.stderr
