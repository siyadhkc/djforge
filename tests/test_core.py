"""Core tests for the djforge generator."""

from dataclasses import FrozenInstanceError

import pytest

from djforge.config import PRESETS, ProjectConfig, slugify_name
from djforge.renderer import build_file_map, render, write_tree


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("my-app", "my_app"),
        ("My Cool App", "my_cool_app"),
        ("123 store", "project_123_store"),
        ("!!!", "django_project"),
    ],
)
def test_slugify_name(name, expected):
    assert slugify_name(name) == expected


def test_project_config_is_immutable():
    cfg = ProjectConfig(project_name="shop")
    with pytest.raises(FrozenInstanceError):
        cfg.project_name = "other"  # type: ignore[misc]


def test_requirements_follow_feature_flags():
    cfg = ProjectConfig(include_api=True, database="postgres")
    requirements = "\n".join(cfg.requirements)
    assert "Django" in requirements
    assert "djangorestframework" in requirements
    assert "psycopg" in requirements


def test_presets_describe_expected_shape():
    assert PRESETS["minimal"].include_api is False
    assert PRESETS["api"].include_api is True
    assert PRESETS["fullstack"].include_docker is True
    assert PRESETS["fullstack"].database == "postgres"


def test_with_name_keeps_preset_options():
    cfg = PRESETS["fullstack"].with_name("Big Shop")
    assert cfg.project_name == "Big Shop"
    assert cfg.slug == "big_shop"
    assert cfg.include_docker is True


def test_render_basic_template():
    cfg = ProjectConfig(project_name="test app")
    assert render("hello {{ c.slug }}", cfg) == "hello test_app"


def test_build_file_map_contains_minimal_project_files():
    cfg = ProjectConfig(project_name="demo")
    files = build_file_map(cfg)
    assert "manage.py" in files
    assert "requirements.txt" in files
    assert "Makefile" in files
    assert "demo/settings.py" in files
    assert "demo/core/views.py" in files


def test_build_file_map_docker_toggle():
    assert "Dockerfile" not in build_file_map(ProjectConfig(include_docker=False))
    assert "Dockerfile" in build_file_map(ProjectConfig(include_docker=True))


def test_build_file_map_api_toggle():
    plain = render(
        build_file_map(ProjectConfig(project_name="plain", include_api=False))[
            "plain/core/views.py"
        ],
        ProjectConfig(project_name="plain", include_api=False),
    )
    api = render(
        build_file_map(ProjectConfig(project_name="api", include_api=True))[
            "api/core/views.py"
        ],
        ProjectConfig(project_name="api", include_api=True),
    )
    assert "JsonResponse" in plain
    assert "rest_framework" in api


def test_write_tree_creates_files(workspace_tmp):
    cfg = ProjectConfig(project_name="write test")
    written = write_tree(workspace_tmp, {"hello.txt": "{{ c.slug }}"}, cfg)
    assert written == ["hello.txt"]
    assert (workspace_tmp / "hello.txt").read_text(encoding="utf-8") == "write_test"


def test_write_tree_full_project(workspace_tmp):
    cfg = ProjectConfig(project_name="full test", include_api=True, include_docker=True)
    written = write_tree(workspace_tmp, build_file_map(cfg), cfg)
    assert len(written) >= 18
    assert (workspace_tmp / "full_test" / "settings.py").exists()
    assert (workspace_tmp / "full_test" / "core" / "views.py").exists()
    assert (workspace_tmp / "Dockerfile").exists()
