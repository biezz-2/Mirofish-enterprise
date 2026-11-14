"""Shared fixtures for the MiroFish test suite.

The suite is written defensively: sibling modules under mirofish/ may still
be in progress, so tests must use ``pytest.importorskip`` (or import inside
test functions) and skip cleanly when a module/attribute is unavailable.
"""

import sys
from pathlib import Path

import pytest
import yaml

# Ensure the repo root is importable regardless of how pytest is invoked.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PLATFORMS_DIR = ROOT / "platforms"


def import_attr(module_name, attr, skip_reason=None):
    """Import ``module_name`` and return ``attr`` or skip the test.

    Returns ``None``-safe: raises ``pytest.skip`` when the module cannot be
    imported or the attribute is missing.
    """
    module = pytest.importorskip(module_name, reason=skip_reason or f"{module_name} not available yet")
    obj = getattr(module, attr, None)
    if obj is None:
        pytest.skip(f"{module_name}.{attr} not implemented yet")
    return obj


@pytest.fixture
def platform_specs_dir() -> Path:
    return PLATFORMS_DIR


@pytest.fixture
def platform_yaml_files(platform_specs_dir) -> list:
    return sorted(platform_specs_dir.glob("*.yaml"))


@pytest.fixture
def load_platform_yaml():
    def _load(path):
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    return _load


@pytest.fixture
def tmp_project(tmp_path) -> Path:
    """A scratch project dir for store/cache/manifest tests."""
    proj = tmp_path / "proj"
    proj.mkdir()
    return proj


def pytest_configure(config):
    config.addinivalue_line("markers", "mirofish: tests for the mirofish package")


def pytest_collection_modifyitems(config, items):
    # Mark the whole suite with a custom marker for selective runs.
    for item in items:
        item.add_marker(pytest.mark.mirofish)
