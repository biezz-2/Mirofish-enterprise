"""
Modul Utilitas SQLite Engine untuk MiroFish Enterprise
Menyediakan standardisasi koneksi SQLite dengan Write-Ahead Logging (WAL) mode,
pengaturan synchronous=NORMAL untuk efisiensi ACID multi-thread,
dan hook listener untuk SQLAlchemy Engine.
"""
from __future__ import annotations

import sqlite3
import os
from typing import Optional, Dict, Any, Union
from sqlalchemy import event
from sqlalchemy.engine import Engine


def get_sqlite_connection(
    db_path: str,
    timeout: float = 30.0,
    wal_mode: bool = True,
    check_same_thread: bool = False,
) -> sqlite3.Connection:
    """
    Membuka koneksi sqlite3 baru dan mengonfigurasi PRAGMA WAL & synchronous NORMAL,
    timeout 30 detik, serta tuning performa memori (cache_size, mmap_size).
    """
    if db_path != ":memory:":
        parent = os.path.dirname(os.path.abspath(db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=timeout, check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row

    if wal_mode and db_path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA cache_size = -64000;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA mmap_size = 268435456;")
    return conn


def configure_sqlite_engine(engine: Engine) -> None:
    """
    Mengaitkan event listener SQLAlchemy pada engine SQLite agar setiap koneksi
    dari connection pool selalu mengeksekusi PRAGMA journal_mode=WAL, synchronous=NORMAL,
    dan busy_timeout=30000.
    """
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode = WAL;")
                cursor.execute("PRAGMA synchronous = NORMAL;")
                cursor.execute("PRAGMA busy_timeout = 30000;")
                cursor.execute("PRAGMA cache_size = -64000;")
                cursor.execute("PRAGMA temp_store = MEMORY;")
                cursor.execute("PRAGMA mmap_size = 268435456;")
            finally:
                cursor.close()


def ensure_platform_db_indexes(conn: sqlite3.Connection) -> None:
    """
    Memastikan indeks relasional optimal telah dibuat pada tabel-tabel simulasi
    (trace, post, comment, likes) untuk mempercepat pembacaan simultan multi-platform.
    """
    cursor = conn.cursor()
    try:
        tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
        if "trace" in tables:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_action_user ON trace (action, user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_created_at ON trace (created_at);")
        if "post" in tables:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_created_at ON post (created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_user_id ON post (user_id);")
        if "comment" in tables:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comment_post_id ON comment (post_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comment_created_at ON comment (created_at);")
        if "likes" in tables:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_likes_post_id ON likes (post_id);")
        conn.commit()
    finally:
        cursor.close()


def enable_wal_on_db_file(db_path: str) -> bool:
    """
    Mengaktifkan WAL mode dan indeks performa pada file database SQLite yang sudah ada secara online.
    Aman dijalankan tanpa merusak data atau mematikan proses yang sedang berjalan.
    """
    if not os.path.exists(db_path):
        return False
    try:
        conn = get_sqlite_connection(db_path, timeout=30.0, wal_mode=True)
        ensure_platform_db_indexes(conn)
        conn.close()
        return True
    except Exception:
        return False


def verify_sqlite_wal_mode(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Memverifikasi apakah koneksi SQLite aktif dalam WAL mode dan synchronous NORMAL.
    """
    cursor = conn.cursor()
    try:
        journal_mode = cursor.execute("PRAGMA journal_mode;").fetchone()[0]
        sync_mode = cursor.execute("PRAGMA synchronous;").fetchone()[0]
        busy_timeout = cursor.execute("PRAGMA busy_timeout;").fetchone()[0]
        return {
            "journal_mode": str(journal_mode).lower(),
            "synchronous": int(sync_mode),
            "busy_timeout": int(busy_timeout),
            "is_wal": str(journal_mode).lower() == "wal",
            "is_synchronous_normal": int(sync_mode) == 1,
        }
    finally:
        cursor.close()


def execute_wal_checkpoint(
    conn_or_path: Union[sqlite3.Connection, str],
    mode: str = "PASSIVE"
) -> Dict[str, Any]:
    """
    Mengeksekusi checkpointing WAL secara terkontrol (PASSIVE, FULL, RESTART, TRUNCATE).
    """
    valid_modes = {"PASSIVE", "FULL", "RESTART", "TRUNCATE"}
    norm_mode = mode.upper()
    if norm_mode not in valid_modes:
        raise ValueError(f"Checkpoint mode tidak valid: {mode}. Harus salah satu dari {valid_modes}")

    close_conn = False
    if isinstance(conn_or_path, str):
        conn = get_sqlite_connection(conn_or_path)
        close_conn = True
    else:
        conn = conn_or_path

    try:
        cursor = conn.execute(f"PRAGMA wal_checkpoint({norm_mode});")
        row = cursor.fetchone()
        # format: (busy, log_frames, checkpointed_frames)
        return {
            "mode": norm_mode,
            "busy": int(row[0]),
            "log_frames": int(row[1]),
            "checkpointed_frames": int(row[2]),
            "success": int(row[0]) == 0,
        }
    finally:
        if close_conn:
            conn.close()
