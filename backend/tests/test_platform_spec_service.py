# backend/tests/test_platform_spec_service.py
"""Tests for PlatformSpecService — adapter PlatformSpec -> pipeline profile."""
import importlib.util
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

SERVICE_PATH = BACKEND_ROOT / "app" / "services" / "simulation" / "platform_spec_service.py"


def _load_service():
    """Load the service module without triggering ``app/__init__`` (flask)."""
    spec = importlib.util.spec_from_file_location("platform_spec_service", SERVICE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PlatformSpecService


@pytest.fixture(scope="module")
def service_cls():
    return _load_service()


def test_all_eleven_platforms_load(service_cls):
    svc = service_cls()
    platforms = svc.list_platforms()
    expected = {"x", "threads", "instagram", "facebook", "linkedin", "tiktok",
                "youtube", "whatsapp", "telegram", "bluesky", "mastodon"}
    assert expected <= set(platforms)


def test_validate_all_clean(service_cls):
    svc = service_cls()
    issues = svc.validate_all()
    assert issues == {} or all(not v for v in issues.values())


def test_pipeline_profile_whatsapp_push(service_cls):
    svc = service_cls()
    profile = svc.to_pipeline_profile("whatsapp")
    assert profile["delivery_mode"] == "push"
    assert profile["privacy_tier"] == "private"
    assert profile["regimes"]["regular"]["max_chars"] == 65536
    assert "platform_spec" in profile


def test_pipeline_profile_x_ranked(service_cls):
    svc = service_cls()
    profile = svc.to_pipeline_profile("x")
    assert profile["feed_kind"] == "hybrid"
    assert profile["scorer_plugin"] == "custom:phoenix"
    assert len(profile["signal_schema"]) > 0
