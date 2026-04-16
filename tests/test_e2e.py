"""
End-to-end tests: invoke the CLI and verify generated output on disk.
"""
import subprocess
import sys

import pytest


def run(*args, cwd=None):
    """Run djforge CLI via subprocess and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "djforge.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


# ── new --yes (all defaults) ──────────────────────────────────────────────────

def test_new_yes_creates_project(tmp_path):
    r = run("new", "smokeapp", "--yes", "--no-git", "--output", str(tmp_path))
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "smokeapp" / "manage.py").exists()


def test_new_yes_writes_env(tmp_path):
    run("new", "envtest", "--yes", "--no-git", "--output", str(tmp_path))
    assert (tmp_path / "envtest" / ".env").exists()
    assert (tmp_path / "envtest" / ".env.example").exists()


def test_new_yes_all_settings_files(tmp_path):
    run("new", "settingstest", "--yes", "--no-git", "--output", str(tmp_path))
    base = tmp_path / "settingstest" / "settingstest" / "settings"
    for name in ("base.py", "development.py", "production.py", "test.py"):
        assert (base / name).exists(), f"Missing settings/{name}"


def test_new_yes_apps_exist(tmp_path):
    run("new", "appstest", "--yes", "--no-git", "--output", str(tmp_path))
    apps = tmp_path / "appstest" / "appstest" / "apps"
    assert (apps / "users" / "models.py").exists()
    assert (apps / "core" / "views.py").exists()


def test_new_yes_docker_files(tmp_path):
    run("new", "dockertest", "--yes", "--no-git", "--output", str(tmp_path))
    root = tmp_path / "dockertest"
    assert (root / "Dockerfile").exists()
    assert (root / "docker-compose.yml").exists()


def test_new_yes_makefile(tmp_path):
    run("new", "maketest", "--yes", "--no-git", "--output", str(tmp_path))
    content = (tmp_path / "maketest" / "Makefile").read_text()
    assert "make dev" in content or "dev:" in content
    assert "make test" in content or "test:" in content


def test_new_exits_if_dir_exists(tmp_path):
    run("new", "exists", "--yes", "--no-git", "--output", str(tmp_path))
    r = run("new", "exists", "--yes", "--no-git", "--output", str(tmp_path))
    assert r.returncode != 0


# ── presets ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("preset", ["minimal", "api", "fullstack"])
def test_preset_generates(tmp_path, preset):
    r = run("new", f"{preset}proj", "--preset", preset, "--no-git", "--output", str(tmp_path))
    assert r.returncode == 0, r.stderr
    assert (tmp_path / f"{preset}proj" / "manage.py").exists()


def test_minimal_preset_no_dockerfile(tmp_path):
    run("new", "minapp", "--preset", "minimal", "--no-git", "--output", str(tmp_path))
    assert not (tmp_path / "minapp" / "Dockerfile").exists()


def test_api_preset_jwt_in_settings(tmp_path):
    run("new", "apiapp", "--preset", "api", "--no-git", "--output", str(tmp_path))
    content = (tmp_path / "apiapp" / "apiapp" / "settings" / "base.py").read_text()
    assert "simplejwt" in content


def test_fullstack_preset_has_docker(tmp_path):
    run("new", "fullapp", "--preset", "fullstack", "--no-git", "--output", str(tmp_path))
    assert (tmp_path / "fullapp" / "Dockerfile").exists()


# ── version / list-presets commands ──────────────────────────────────────────

def test_version_command():
    r = run("version")
    assert r.returncode == 0
    assert "djforge" in r.stdout


def test_list_presets_command():
    r = run("list-presets")
    assert r.returncode == 0
    for preset in ("minimal", "api", "fullstack"):
        assert preset in r.stdout


# ── generated project is importable (syntax check) ───────────────────────────

def test_manage_py_syntax_valid(tmp_path):
    run("new", "syntaxtest", "--yes", "--no-git", "--output", str(tmp_path))
    r = subprocess.run(
        [sys.executable, "-m", "py_compile", "manage.py"],
        cwd=tmp_path / "syntaxtest",
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr


def test_settings_base_syntax_valid(tmp_path):
    run("new", "syntest2", "--yes", "--no-git", "--output", str(tmp_path))
    settings = tmp_path / "syntest2" / "syntest2" / "settings" / "base.py"
    r = subprocess.run(
        [sys.executable, "-m", "py_compile", str(settings)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
