"""
Unit Test: Redis Requirepass Client Enforcement & Database WAL Integrity
Memverifikasi:
1. URL parsing Redis dengan password terisi dan kosong.
2. Penolakan koneksi tanpa kredensial jika REDIS_PASSWORD diwajibkan (anonymous login prohibited).
3. Penerimaan koneksi saat kredensial valid dan pencocokan password.
4. Integrasi Config.get_redis_url() dan build_redis_url().
5. Konsistensi SQLite WAL mode dan synchronous=NORMAL pada inisialisasi koneksi.
"""

import os
import tempfile
import pytest
from sqlalchemy import create_engine, text

from app.config import Config
from app.utils.redis_client import (
    parse_redis_url,
    build_redis_url,
    enforce_redis_credentials,
    get_hardened_redis_url,
    HardenedRedisClient,
)
from app.utils.sqlite_engine import (
    get_sqlite_connection,
    configure_sqlite_engine,
    verify_sqlite_wal_mode,
    execute_wal_checkpoint,
)
from app.services.local_graph_service import LocalGraphService


# =============================================================================
# 1. Redis URL Parsing: Dengan Password & Tanpa Password
# =============================================================================

def test_parse_redis_url_without_password():
    """Menguji parsing URL Redis standar tanpa autentikasi password."""
    url = "redis://127.0.0.1:6379/0"
    parsed = parse_redis_url(url)

    assert parsed["scheme"] == "redis"
    assert parsed["host"] == "127.0.0.1"
    assert parsed["port"] == 6379
    assert parsed["db"] == 0
    assert parsed["password"] == ""
    assert parsed["has_password"] is False


def test_parse_redis_url_with_password():
    """Menguji parsing URL Redis dengan kredensial requirepass."""
    url = "redis://:super_secure_vault_pass_123@10.0.0.5:6380/2"
    parsed = parse_redis_url(url)

    assert parsed["scheme"] == "redis"
    assert parsed["host"] == "10.0.0.5"
    assert parsed["port"] == 6380
    assert parsed["db"] == 2
    assert parsed["password"] == "super_secure_vault_pass_123"
    assert parsed["has_password"] is True


def test_parse_redis_url_with_username_and_ssl():
    """Menguji parsing URL Redis dengan username dan skema SSL (rediss://)."""
    url = "rediss://app_client:my_auth_token@redis-cluster.internal:6379/5"
    parsed = parse_redis_url(url)

    assert parsed["scheme"] == "rediss"
    assert parsed["host"] == "redis-cluster.internal"
    assert parsed["port"] == 6379
    assert parsed["db"] == 5
    assert parsed["username"] == "app_client"
    assert parsed["password"] == "my_auth_token"
    assert parsed["has_password"] is True


def test_parse_redis_url_invalid_scheme():
    """Menguji penolakan skema URL selain redis:// atau rediss://."""
    with pytest.raises(ValueError, match="Skema URL tidak didukung"):
        parse_redis_url("http://127.0.0.1:6379")


# =============================================================================
# 2. Redis URL Builder
# =============================================================================

def test_build_redis_url():
    """Menguji pembuatan format URL Redis dengan dan tanpa password."""
    # Tanpa password
    url_anon = build_redis_url(host="localhost", port=6379, password="", db=0)
    assert url_anon == "redis://localhost:6379/0"

    # Dengan password
    url_auth = build_redis_url(host="localhost", port=6379, password="secret_key_abc", db=1)
    assert url_auth == "redis://:secret_key_abc@localhost:6379/1"


# =============================================================================
# 3. Penegakan Requirepass & Penolakan Koneksi Anonymous
# =============================================================================

def test_enforce_redis_credentials_rejection():
    """Memastikan penolakan keras (PermissionError) saat mencoba akses anonymous tanpa password."""
    required_pwd = "production_requirepass_999"
    anon_url = "redis://127.0.0.1:6379/0"

    # Penolakan koneksi tanpa kredensial jika REDIS_PASSWORD diwajibkan
    with pytest.raises(PermissionError, match="anonymous login dilarang"):
        enforce_redis_credentials(anon_url, required_password=required_pwd)


def test_enforce_redis_credentials_mismatch():
    """Memastikan penolakan saat password yang diberikan salah."""
    required_pwd = "correct_password"
    wrong_url = "redis://:wrong_password@127.0.0.1:6379/0"

    with pytest.raises(PermissionError, match="tidak cocok"):
        enforce_redis_credentials(wrong_url, required_password=required_pwd)


def test_enforce_redis_credentials_acceptance():
    """Memastikan koneksi diterima saat password valid disertakan."""
    required_pwd = "correct_password"
    valid_url = "redis://:correct_password@127.0.0.1:6379/0"

    res = enforce_redis_credentials(valid_url, required_password=required_pwd)
    assert res == valid_url


def test_hardened_redis_client_enforcement():
    """Menguji HardenedRedisClient menolak anonymous login dan mengesahkan autentikasi."""
    required_pwd = "cluster_requirepass_key"

    # 1. Menolak anonymous login via string host tanpa password
    with pytest.raises(PermissionError, match="anonymous login ditolak"):
        HardenedRedisClient(
            url_or_host="127.0.0.1",
            port=6379,
            password="",
            required_password=required_pwd
        )

    # 2. Menolak anonymous login via URL tanpa password
    with pytest.raises(PermissionError, match="anonymous login dilarang"):
        HardenedRedisClient(
            url_or_host="redis://127.0.0.1:6379/0",
            required_password=required_pwd
        )

    # 3. Menolak password yang salah
    with pytest.raises(PermissionError, match="password tidak cocok"):
        HardenedRedisClient(
            url_or_host="127.0.0.1",
            port=6379,
            password="incorrect_password",
            required_password=required_pwd
        )

    # 4. Berhasil inisialisasi dengan password yang cocok
    client = HardenedRedisClient(
        url_or_host="127.0.0.1",
        port=6379,
        password=required_pwd,
        required_password=required_pwd
    )
    assert client.password == required_pwd
    assert client.ping(mock=True) is True


def test_get_hardened_redis_url_injection():
    """Menguji injeksi otomatis password wajib ke URL anonymous jika diminta."""
    required_pwd = "injected_pass"
    raw_anon_url = "redis://192.168.1.100:6379/3"

    hardened_url = get_hardened_redis_url(raw_url=raw_anon_url, required_password=required_pwd)
    assert hardened_url == "redis://:injected_pass@192.168.1.100:6379/3"


# =============================================================================
# 4. Konfigurasi App Config: REDIS_URL & FalkorDB URI
# =============================================================================

def test_config_redis_url_behavior(monkeypatch):
    """Menguji Config.build_redis_url dan Config.get_redis_url sesuai environment."""
    monkeypatch.setattr(Config, "REDIS_HOST", "127.0.0.1")
    monkeypatch.setattr(Config, "REDIS_PORT", 6379)
    monkeypatch.setattr(Config, "REDIS_DB", 0)
    monkeypatch.setattr(Config, "REDIS_PASSWORD", "vault_secret_token")

    built_url = Config.build_redis_url()
    assert built_url == "redis://:vault_secret_token@127.0.0.1:6379/0"

    # get_redis_url dengan penegakan kredensial
    monkeypatch.setattr(Config, "REDIS_URL", built_url)
    assert Config.get_redis_url(enforce_auth=True) == built_url

    # Memastikan jika REDIS_URL di-set anonymous saat REDIS_PASSWORD ada, get_redis_url menolaknya
    monkeypatch.setattr(Config, "REDIS_URL", "redis://127.0.0.1:6379/0")
    with pytest.raises(PermissionError, match="anonymous login dilarang"):
        Config.get_redis_url(enforce_auth=True)


# =============================================================================
# 5. SQLite WAL Mode Retention & Synchronous NORMAL Integrity
# =============================================================================

def test_sqlite_engine_wal_and_synchronous():
    """Memverifikasi inisialisasi koneksi SQLite langsung mengeksekusi PRAGMA WAL dan synchronous NORMAL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_integrity.sqlite3")
        conn = get_sqlite_connection(db_path)

        try:
            status = verify_sqlite_wal_mode(conn)
            assert status["is_wal"] is True, f"Journal mode harus 'wal', didapat: {status['journal_mode']}"
            assert status["is_synchronous_normal"] is True, f"Synchronous harus NORMAL (1), didapat: {status['synchronous']}"
            assert status["busy_timeout"] >= 5000, f"Busy timeout harus >= 5000ms, didapat: {status['busy_timeout']}"

            # Jalankan checkpoint WAL
            cp_result = execute_wal_checkpoint(conn, mode="PASSIVE")
            assert cp_result["success"] is True
            assert cp_result["mode"] == "PASSIVE"
        finally:
            conn.close()


def test_sqlalchemy_sqlite_engine_wal_listener():
    """Memverifikasi hook configure_sqlite_engine mengonfigurasi koneksi SQLAlchemy ke SQLite."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_sa.sqlite3")
        engine = create_engine(f"sqlite:///{db_path}")
        configure_sqlite_engine(engine)

        with engine.connect() as connection:
            # Query PRAGMA langsung lewat SQLAlchemy
            res_wal = connection.execute(text("PRAGMA journal_mode;")).scalar()
            res_sync = connection.execute(text("PRAGMA synchronous;")).scalar()

            assert str(res_wal).lower() == "wal"
            assert int(res_sync) == 1  # 1 = NORMAL


def test_local_graph_service_sqlite_connection():
    """Memverifikasi LocalGraphService.get_sqlite_connection() menerapkan PRAGMA WAL & synchronous NORMAL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "graph_db.sqlite3")
        conn = LocalGraphService.get_sqlite_connection(db_path)
        try:
            status = verify_sqlite_wal_mode(conn)
            assert status["is_wal"] is True
            assert status["is_synchronous_normal"] is True
        finally:
            conn.close()
