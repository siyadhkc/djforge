"""Test fixtures that avoid the locked system temp directory on this machine."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def workspace_tmp():
    root = Path.cwd() / ".test-output" / uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=False)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)
