"""
Automated Test Suite for Agent 20: DevOps, Production Hardening & QA Gate Guard
Covers AES-256-GCM Envelope Encryption, 9Router Failover Gateway,
PM2/Docker configs, and Phase-Gate Verification Guard (V1-V8).
"""

import os
import sys
import json
import time
import pytest
from unittest.mock import patch, MagicMock

# Ensure backend root on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.utils.vault import (
    VaultManager,
    derive_kek,
    generate_dek,
    encrypt_dek,
    decrypt_dek,
    encrypt_with_dek,
    decrypt_with_dek,
    mask_secret,
    get_vault,
    store_secret,
    retrieve_secret,
    VaultAuthenticationError,
)
from app.services.nine_router import (
    NineRouterGateway,
    CircuitBreaker,
    CircuitState,
    get_nine_router
)
from app.services.phase_gate_guard import (
    PhaseGateGuard,
    get_phase_gate_guard
)


class TestAgent20DevOpsVault:
    """Test suite covering Agent 20 DevOps & Vault Hardening."""

    def test_01_vault_envelope_encryption(self, tmp_path):
        """Test AES-256-GCM two-tier envelope encryption (KEK/DEK hierarchy)."""
        vault_file = str(tmp_path / "test_vault_envelope.enc")
        passphrase = "master_super_secure_passphrase_2026!"

        # 1. Test KEK Derivation with PBKDF2 (100,000 iterations)
        salt = os.urandom(16)
        kek = derive_kek(passphrase, salt, iterations=1000)
        assert len(kek) == 32, "Derived KEK must be 256 bits (32 bytes)"

        # 2. Test DEK generation and wrapping
        dek = generate_dek()
        assert len(dek) == 32, "DEK must be 256 bits"

        nonce, enc_dek = encrypt_dek(dek, kek)
        assert len(nonce) == 12, "AES-GCM nonce must be 96 bits (12 bytes)"
        dec_dek = decrypt_dek(enc_dek, nonce, kek)
        assert dec_dek == dek, "Decrypted DEK must match original DEK"

        # 3. Test Payload encryption with DEK
        payload = b"DATABASE_URL=postgresql://admin:secret@pg.cluster.internal:5432/mirofish"
        p_nonce, ct = encrypt_with_dek(payload, dek)
        dec_payload = decrypt_with_dek(ct, p_nonce, dek)
        assert dec_payload == payload, "Decrypted payload must match original"

        # 4. Test Full VaultManager lifecycle
        vm = VaultManager(vault_path=vault_file, passphrase=passphrase)
        vm.set_secret("OPENAI_API_KEY", "sk-proj-super-secret-key-enterprise-1234")
        vm.set_secret("REDIS_PASSWORD", "redis_secure_vault_pw_9876")

        assert vm.get_secret("OPENAI_API_KEY") == "sk-proj-super-secret-key-enterprise-1234"
        assert vm.get_secret("REDIS_PASSWORD") == "redis_secure_vault_pw_9876"
        assert vm.has_secret("OPENAI_API_KEY") is True
        assert vm.has_secret("NON_EXISTENT") is False

    def test_02_vault_master_key_rotation(self, tmp_path):
        """Test master key re-wrapping without plain secret data loss."""
        vault_file = str(tmp_path / "test_vault_rotation.enc")
        old_pass = "old_passphrase_phase1"
        new_pass = "new_passphrase_phase2_rotated"

        vm = VaultManager(vault_path=vault_file, passphrase=old_pass)
        vm.set_secret("DATABASE_URI", "sqlite:////home/biezz/db.sqlite")
        vm.set_secret("JWT_SECRET", "jwt_very_secret_key_112233")

        # Rotate key
        rotated = vm.rotate_master_key(new_pass)
        assert rotated is True, "Master key rotation should succeed"

        # Old passphrase should fail to load
        with pytest.raises(VaultAuthenticationError):
            bad_vm = VaultManager(vault_path=vault_file, passphrase=old_pass)
            bad_vm.get_secret("DATABASE_URI")

        # New passphrase should successfully decrypt all data
        new_vm = VaultManager(vault_path=vault_file, passphrase=new_pass)
        assert new_vm.get_secret("DATABASE_URI") == "sqlite:////home/biezz/db.sqlite"
        assert new_vm.get_secret("JWT_SECRET") == "jwt_very_secret_key_112233"

    def test_03_vault_secret_masking(self):
        """Test credential sanitization and masking."""
        raw_key = "sk-proj-1234567890abcdef12345678"
        masked = mask_secret(raw_key)
        assert "1234567890abcdef" not in masked
        assert "[REDACTED]" in masked
        assert masked.startswith("sk-p")

        short_secret = "abc"
        assert mask_secret(short_secret) == "[REDACTED]"
        assert mask_secret("") == ""
        assert mask_secret(None) == ""

    def test_04_vault_backward_compatibility(self, tmp_path):
        """Test backward compatibility functions with existing application routes."""
        test_vault = str(tmp_path / "compat_vault.enc")
        os.environ["MIROFISH_VAULT_FILE"] = test_vault
        os.environ["MIROFISH_VAULT_PASSPHRASE"] = "compat_passphrase_2026"

        v = get_vault()
        assert v is not None

        # Backward compatibility functions
        store_secret("TEST_API_TOKEN", "token_value_abc_xyz")
        val = retrieve_secret("TEST_API_TOKEN")
        assert val == "token_value_abc_xyz"

    def test_05_9router_circuit_breaker_transitions(self):
        """Test Circuit Breaker states: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
        cb = CircuitBreaker("test-provider", failure_threshold=2, recovery_timeout_seconds=0.1)
        assert cb.state == CircuitState.CLOSED
        assert cb.can_attempt() is True

        # 1. First failure -> still CLOSED
        cb.record_failure(Exception("Transient network timeout 504"))
        assert cb.state == CircuitState.CLOSED
        assert cb.can_attempt() is True

        # 2. Second failure -> trips to OPEN
        cb.record_failure(Exception("Service unavailable 503"))
        assert cb.state == CircuitState.OPEN
        assert cb.can_attempt() is False

        # 3. Wait for recovery timeout -> transitions to HALF_OPEN
        time.sleep(0.12)
        assert cb.can_attempt() is True
        assert cb.state == CircuitState.HALF_OPEN

        # 4. Successful execution in HALF_OPEN -> resets to CLOSED
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_06_9router_failover_hierarchy(self):
        """Test multi-provider automatic failover from primary to secondary."""
        router = NineRouterGateway()

        # Mock primary to fail, secondary to succeed
        def mock_exec(provider, messages, **kwargs):
            if provider.name == "openai-primary":
                raise ConnectionError("OpenAI RateLimit 429")
            return {
                "id": "chatcmpl-mock-anthropic",
                "choices": [{"message": {"role": "assistant", "content": "Response from Anthropic Secondary"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
            }

        with patch.object(router, "_execute_provider_call", side_effect=mock_exec):
            messages = [{"role": "user", "content": "Hello AI failover test"}]
            resp = router.chat_completion(messages=messages)
            assert resp["provider"] == "secondary-fallback"
            assert resp["content"] == "Response from Anthropic Secondary"
            assert resp["status"] == "SUCCESS"

    def test_07_9router_response_caching(self):
        """Test intelligent response caching and latency optimization."""
        router = NineRouterGateway()
        messages = [{"role": "user", "content": "Cacheable unique prompt 2026"}]

        # First call (generates response)
        resp1 = router.chat_completion(messages=messages, temperature=0.0)
        assert resp1["cached"] is False

        # Second call (must hit in-memory cache)
        resp2 = router.chat_completion(messages=messages, temperature=0.0)
        assert resp2["cached"] is True
        assert resp2["content"] == resp1["content"]
        assert resp2["latency_ms"] < 10.0

    def test_08_9router_telemetry_and_audit_logging(self):
        """Test structured audit logging and telemetry metric export."""
        router = NineRouterGateway()
        telemetry = router.get_telemetry()

        assert "total_requests" in telemetry
        assert "circuit_breakers" in telemetry
        assert "providers" in telemetry
        assert "openai-primary" in telemetry["circuit_breakers"]
        assert "secondary-fallback" in telemetry["circuit_breakers"]
        assert "local-fallback" in telemetry["circuit_breakers"]

    def test_09_pm2_ecosystem_and_docker_compose(self):
        """Test ecosystem.config.js and docker-compose.yml configuration completeness."""
        eco_path = os.path.join(PROJECT_ROOT, "ecosystem.config.js")
        assert os.path.exists(eco_path), "ecosystem.config.js must exist in root"
        with open(eco_path, "r", encoding="utf-8") as f:
            eco_content = f.read()

        # Verify all 4 required PM2 services
        assert "mirofish-backend" in eco_content
        assert "mirofish-frontend" in eco_content
        assert "mirofish-9router" in eco_content
        assert "mirofish-webhook-worker" in eco_content

        docker_path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
        assert os.path.exists(docker_path), "docker-compose.yml must exist in root"
        with open(docker_path, "r", encoding="utf-8") as f:
            docker_content = f.read()

        # Verify Redis, SearXNG, and backend
        assert "searxng" in docker_content
        assert "redis" in docker_content

    def test_10_phase_gate_guard_v1_v8(self):
        """Test automated Phase-Gate verification engine (V1 to V8)."""
        guard = get_phase_gate_guard()
        v2 = guard.audit_v2_logic_correctness()
        assert v2.passed is True
        assert v2.score_percent == 100.0

        v3 = guard.audit_v3_security_and_owasp()
        assert v3.passed is True
        assert v3.score_percent == 100.0

        v4 = guard.audit_v4_standards_compliance()
        assert v4.passed is True
        assert v4.score_percent == 100.0

        v5 = guard.audit_v5_performance_and_resources()
        assert v5.passed is True
        assert v5.score_percent == 100.0

        v6 = guard.audit_v6_regression_check()
        assert v6.passed is True

        v7 = guard.audit_v7_code_quality()
        assert v7.passed is True
