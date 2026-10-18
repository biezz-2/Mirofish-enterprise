"""
Unit tests for Startup Security Fail-Fast Guard (P0-2 / P0-4)
Validates that MiroFish rejects booting when SECRET_KEY is missing/dangerous or
DEVELOPMENT_MODE is enabled during production execution (FLASK_DEBUG=false/0).
"""

import os
import sys
import secrets
import pytest

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from app import create_app, validate_startup_security


def test_production_rejects_empty_secret_key(monkeypatch):
    """Production mode must reject empty SECRET_KEY."""
    monkeypatch.setenv("FLASK_DEBUG", "false")
    monkeypatch.setenv("SECRET_KEY", "")
    monkeypatch.setenv("DEVELOPMENT_MODE", "false")

    with pytest.raises(RuntimeError) as exc_info:
        create_app()
    assert "FATAL: Insecure SECRET_KEY detected in production mode" in str(exc_info.value)


def test_production_rejects_unset_secret_key(monkeypatch):
    """Production mode with unset SECRET_KEY in environ must fail fast."""
    monkeypatch.setenv("FLASK_DEBUG", "0")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DEVELOPMENT_MODE", "false")

    with pytest.raises(RuntimeError) as exc_info:
        validate_startup_security()
    assert "FATAL: Insecure SECRET_KEY detected in production mode" in str(exc_info.value)


@pytest.mark.parametrize("insecure_key", [
    "example",
    "example-secret-key-12345",
    "EXAMPLE_KEY_FOR_TESTING",
    "test",
    "test-secret",
    "UNIT_TEST_KEY_2026",
    "mirofish-enterprise-secret-key-2026",
    "prefix-mirofish-enterprise-secret-key-2026-suffix",
])
def test_production_rejects_insecure_pattern_secret_keys(monkeypatch, insecure_key):
    """Production mode must reject keys containing 'example', 'test', or 'mirofish-enterprise-secret-key-2026'."""
    monkeypatch.setenv("FLASK_DEBUG", "false")
    monkeypatch.setenv("SECRET_KEY", insecure_key)
    monkeypatch.setenv("DEVELOPMENT_MODE", "false")

    with pytest.raises(RuntimeError) as exc_info:
        create_app()
    assert "FATAL: Insecure SECRET_KEY detected in production mode" in str(exc_info.value)


@pytest.mark.parametrize("dev_mode_val", ["true", "True", "TRUE", "1"])
def test_production_rejects_development_mode_enabled(monkeypatch, dev_mode_val):
    """Production mode must reject DEVELOPMENT_MODE=true or 1."""
    secure_key = secrets.token_hex(32)
    monkeypatch.setenv("FLASK_DEBUG", "false")
    monkeypatch.setenv("SECRET_KEY", secure_key)
    monkeypatch.setenv("DEVELOPMENT_MODE", dev_mode_val)

    with pytest.raises(RuntimeError) as exc_info:
        create_app()
    assert "FATAL: DEVELOPMENT_MODE cannot be enabled in production (FLASK_DEBUG=false)." in str(exc_info.value)


def test_production_accepts_valid_configuration(monkeypatch):
    """Production mode boots cleanly when SECRET_KEY is cryptographically secure and DEVELOPMENT_MODE=false."""
    secure_key = secrets.token_hex(32)
    monkeypatch.setenv("FLASK_DEBUG", "false")
    monkeypatch.setenv("SECRET_KEY", secure_key)
    monkeypatch.setenv("DEVELOPMENT_MODE", "false")

    # Should not raise exception
    validate_startup_security()
    app = create_app()
    assert app is not None
    assert app.config["SECRET_KEY"] == secure_key


def test_development_mode_bypasses_guard(monkeypatch):
    """When FLASK_DEBUG=true, development values and mock keys are permitted without raising RuntimeError."""
    monkeypatch.setenv("FLASK_DEBUG", "true")
    monkeypatch.setenv("SECRET_KEY", "test-key-development-only")
    monkeypatch.setenv("DEVELOPMENT_MODE", "true")

    # Should not raise exception
    validate_startup_security()
    app = create_app()
    assert app is not None
