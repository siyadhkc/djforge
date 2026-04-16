"""Tests for djforge core logic."""
from copy import deepcopy

from djforge.config import ProjectConfig, PRESETS
from djforge.renderer import build_file_map, render, write_tree


# ── config ────────────────────────────────────────────────────────────────────


def test_slug_sanitises_hyphens():
    cfg = ProjectConfig(project_name="my-app")
    assert cfg.slug == "my_app"


def test_slug_sanitises_spaces():
    cfg = ProjectConfig(project_name="My Cool App")
    assert cfg.slug == "my_cool_app"


def test_needs_redis_when_celery():
    cfg = ProjectConfig(use_celery=True, cache="locmem")
    assert cfg.needs_redis is True


def test_needs_redis_when_redis_cache():
    cfg = ProjectConfig(use_celery=False, cache="redis")
    assert cfg.needs_redis is True


def test_no_redis_when_both_off():
    cfg = ProjectConfig(use_celery=False, cache="locmem")
    assert cfg.needs_redis is False


def test_db_url_example_sqlite():
    cfg = ProjectConfig(database="sqlite")
    assert "sqlite" in cfg.db_url_example


def test_db_url_example_postgres():
    cfg = ProjectConfig(database="postgres", project_name="shop")
    assert "postgres" in cfg.db_url_example
    assert "shop" in cfg.db_url_example


def test_presets_exist():
    for key in ("minimal", "api", "fullstack"):
        assert key in PRESETS


def test_minimal_preset_no_docker():
    assert PRESETS["minimal"].use_docker is False


def test_api_preset_has_jwt():
    assert PRESETS["api"].auth == "jwt"


# ── renderer ──────────────────────────────────────────────────────────────────


def test_render_basic():
    cfg = ProjectConfig(project_name="testapp")
    result = render("Hello {{ c.slug }}!", cfg)
    assert result == "Hello testapp!"


def test_render_conditional_celery_on():
    cfg = ProjectConfig(use_celery=True)
    tmpl = "{% if c.use_celery %}yes{% else %}no{% endif %}"
    assert render(tmpl, cfg) == "yes"


def test_render_conditional_celery_off():
    cfg = ProjectConfig(use_celery=False)
    tmpl = "{% if c.use_celery %}yes{% else %}no{% endif %}"
    assert render(tmpl, cfg) == "no"


def test_build_file_map_contains_manage(tmp_path):
    cfg = ProjectConfig(project_name="demo")
    files = build_file_map(cfg)
    assert "manage.py" in files


def test_build_file_map_docker_toggle(tmp_path):
    cfg_with = ProjectConfig(project_name="demo", use_docker=True)
    cfg_without = ProjectConfig(project_name="demo", use_docker=False)
    assert "Dockerfile" in build_file_map(cfg_with)
    assert "Dockerfile" not in build_file_map(cfg_without)


def test_write_tree_creates_files(tmp_path):
    cfg = ProjectConfig(project_name="writetest")
    files = {"hello.txt": "{{ c.slug }}"}
    write_tree(tmp_path, files, cfg)
    assert (tmp_path / "hello.txt").read_text() == "writetest"


def test_write_tree_full_project(tmp_path):
    cfg = ProjectConfig(project_name="fulltest")
    files = build_file_map(cfg)
    written = write_tree(tmp_path, files, cfg)
    assert len(written) > 20
    assert (tmp_path / "manage.py").exists()
    assert (tmp_path / "fulltest" / "settings" / "base.py").exists()
    assert (tmp_path / "fulltest" / "apps" / "users" / "models.py").exists()


def test_settings_base_contains_secret_key(tmp_path):
    cfg = ProjectConfig(project_name="sectest")
    files = build_file_map(cfg)
    write_tree(tmp_path, files, cfg)
    content = (tmp_path / "sectest" / "settings" / "base.py").read_text()
    assert "SECRET_KEY" in content
    assert "environ" in content


def test_no_celery_when_disabled(tmp_path):
    cfg = ProjectConfig(project_name="nocelery", use_celery=False)
    files = build_file_map(cfg)
    assert f"{cfg.slug}/celery.py" not in files


def test_celery_file_present_when_enabled(tmp_path):
    cfg = ProjectConfig(project_name="withcelery", use_celery=True)
    files = build_file_map(cfg)
    assert f"{cfg.slug}/celery.py" in files


def test_custom_user_initial_migration_is_generated():
    cfg = ProjectConfig(project_name="migratecheck")
    files = build_file_map(cfg)
    assert f"{cfg.slug}/apps/users/migrations/0001_initial.py" in files


def test_no_drf_project_avoids_rest_framework_imports():
    cfg = ProjectConfig(project_name="nodrf", use_drf=False, use_swagger=False)
    files = build_file_map(cfg)
    assert "rest_framework" not in files[f"{cfg.slug}/apps/core/views.py"]
    assert "rest_framework" not in files[f"{cfg.slug}/apps/users/views.py"]
    assert "rest_framework" not in files[f"{cfg.slug}/apps/users/serializers.py"]


def test_minimal_preset_generates_correctly(tmp_path):
    cfg = deepcopy(PRESETS["minimal"])
    cfg.project_name = "mintest"
    files = build_file_map(cfg)
    write_tree(tmp_path, files, cfg)
    assert (tmp_path / "manage.py").exists()
