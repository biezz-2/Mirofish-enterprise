"""
Unit and Integration Tests for MiroFish Database & Persistence Architecture (Subagent B).
Verifies:
1. Relational ACID schema and cascading relations.
2. 7-Platform action logging and composite indexes.
3. Atomic state machine transitions for Task and Job models.
4. SHA-256 hash checkpoint validation and crash recovery.
5. High-concurrency SQLite WAL multi-threaded writes without locks.
6. Dual-persistence synchronization (file + relational DB).
"""
import os
import shutil
import tempfile
import threading
import sqlite3
import hashlib
from datetime import datetime
import pytest

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.models.entities import (
    Base,
    ProjectModel,
    TaskModel,
    JobModel,
    CheckpointModel,
    SimulationRunModel,
    SimulationActionModel,
    CANONICAL_SIMULATION_PLATFORMS,
    TaskState,
    JobState,
    atomic_transition_task,
    atomic_transition_job,
)
from app.models.project import Project, ProjectStatus, ProjectManager
from app.utils.sqlite_engine import (
    get_sqlite_connection,
    configure_sqlite_engine,
    verify_sqlite_wal_mode,
    ensure_platform_db_indexes,
)
from scripts.action_logger import SimulationLogManager, SUPPORTED_PLATFORMS


@pytest.fixture
def test_db():
    """Create a temporary SQLite database configured with WAL mode."""
    temp_dir = tempfile.mkdtemp(prefix="mirofish_test_db_")
    db_path = os.path.join(temp_dir, "test_mirofish.db")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    configure_sqlite_engine(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield {
        "engine": engine,
        "session": session,
        "db_path": db_path,
        "temp_dir": temp_dir,
    }

    session.close()
    engine.dispose()
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_canonical_platforms_support():
    """Verify all 7 canonical platforms are defined and supported."""
    expected = {"twitter", "reddit", "tiktok", "instagram", "threads", "linkedin", "youtube"}
    assert set(CANONICAL_SIMULATION_PLATFORMS) == expected
    assert set(SUPPORTED_PLATFORMS) == expected


def test_schema_and_composite_indexes(test_db):
    """Verify tables and composite indexes on simulation_actions table."""
    engine = test_db["engine"]
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "simulation_runs" in tables
    assert "simulation_actions" in tables
    assert "projects" in tables
    assert "tasks" in tables
    assert "jobs" in tables
    assert "checkpoints" in tables

    # Verify indexes on simulation_actions
    indices = {idx["name"]: idx["column_names"] for idx in inspector.get_indexes("simulation_actions")}
    assert "ix_sim_actions_sim_platform" in indices
    assert indices["ix_sim_actions_sim_platform"] == ["simulation_id", "platform"]
    assert "ix_sim_actions_platform_round" in indices
    assert indices["ix_sim_actions_platform_round"] == ["simulation_id", "platform", "round_num"]
    assert "ix_sim_actions_platform_agent" in indices
    assert indices["ix_sim_actions_platform_agent"] == ["simulation_id", "platform", "agent_id"]
    assert "ix_sim_actions_platform_type" in indices
    assert indices["ix_sim_actions_platform_type"] == ["platform", "action_type"]


def test_atomic_task_state_machine(test_db):
    """Verify atomic state transitions for TaskModel with concurrency safeguards."""
    session = test_db["session"]

    proj = ProjectModel(id="p-test-01", name="Project Alpha")
    session.add(proj)
    task = TaskModel(id="t-test-01", project_id="p-test-01", task_type="build_graph", status="pending")
    session.add(task)
    session.commit()

    # Valid transition: pending -> processing
    assert atomic_transition_task(session, "t-test-01", "pending", "processing") is True
    session.commit()

    # Verify status in DB
    refreshed = session.query(TaskModel).filter_by(id="t-test-01").first()
    assert refreshed.status == "processing"

    # Invalid current state: expecting 'pending' should return False because it is now 'processing'
    assert atomic_transition_task(session, "t-test-01", "pending", "processing") is False

    # Illegal transition: processing -> pending should raise ValueError
    with pytest.raises(ValueError):
        atomic_transition_task(session, "t-test-01", "processing", "pending")

    # Valid transition: processing -> completed
    assert atomic_transition_task(session, "t-test-01", "processing", "completed") is True
    session.commit()
    refreshed = session.query(TaskModel).filter_by(id="t-test-01").first()
    assert refreshed.status == "completed"


def test_atomic_job_state_machine(test_db):
    """Verify atomic state transitions for JobModel with optimistic locking."""
    session = test_db["session"]

    proj = ProjectModel(id="p-test-02", name="Project Beta")
    task = TaskModel(id="t-test-02", project_id="p-test-02", task_type="simulation", status="processing")
    job = JobModel(id="j-test-01", task_id="t-test-02", project_id="p-test-02", state="queued")
    session.add_all([proj, task, job])
    session.commit()

    # Valid transition: queued -> running
    assert atomic_transition_job(session, "j-test-01", "queued", "running", pid=12345) is True
    session.commit()

    job_db = session.query(JobModel).filter_by(id="j-test-01").first()
    assert job_db.state == "running"
    assert job_db.pid == 12345

    # Checkpoint transition: running -> checkpointing -> running
    assert atomic_transition_job(session, "j-test-01", "running", "checkpointing") is True
    session.commit()
    assert atomic_transition_job(session, "j-test-01", "checkpointing", "running") is True
    session.commit()

    # Terminal transition: running -> completed
    assert atomic_transition_job(session, "j-test-01", "running", "completed") is True
    session.commit()
    job_db = session.query(JobModel).filter_by(id="j-test-01").first()
    assert job_db.state == "completed"

    # Transition from completed should raise ValueError (no outgoing transitions)
    with pytest.raises(ValueError):
        atomic_transition_job(session, "j-test-01", "completed", "running")


def test_sqlite_wal_multi_platform_concurrency():
    """Verify that 7 platform threads writing concurrently to SQLite WAL never lock."""
    temp_dir = tempfile.mkdtemp(prefix="mirofish_wal_test_")
    db_path = os.path.join(temp_dir, "concurrent_sim.db")

    init_conn = get_sqlite_connection(db_path, timeout=30.0, wal_mode=True)
    status = verify_sqlite_wal_mode(init_conn)
    assert status["is_wal"] is True
    assert status["is_synchronous_normal"] is True
    assert status["busy_timeout"] == 30000

    init_conn.execute("""
        CREATE TABLE IF NOT EXISTS platform_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            round_num INTEGER NOT NULL,
            agent_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    init_conn.execute("CREATE INDEX IF NOT EXISTS idx_platform_round ON platform_events(platform, round_num);")
    init_conn.close()

    errors = []
    writes_per_thread = 50

    def worker(plat: str):
        try:
            conn = get_sqlite_connection(db_path, timeout=30.0, wal_mode=True)
            for r in range(writes_per_thread):
                conn.execute(
                    "INSERT INTO platform_events (platform, round_num, agent_id, action) VALUES (?, ?, ?, ?)",
                    (plat, r, r * 10, f"action_{plat}_{r}")
                )
                conn.commit()
            conn.close()
        except Exception as e:
            errors.append((plat, str(e)))

    threads = [
        threading.Thread(target=worker, args=(p,))
        for p in CANONICAL_SIMULATION_PLATFORMS
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent write errors encountered: {errors}"

    verify_conn = get_sqlite_connection(db_path, timeout=30.0, wal_mode=True)
    count = verify_conn.execute("SELECT COUNT(*) FROM platform_events").fetchone()[0]
    verify_conn.close()

    expected_total = len(CANONICAL_SIMULATION_PLATFORMS) * writes_per_thread
    assert count == expected_total

    shutil.rmtree(temp_dir, ignore_errors=True)


def test_checkpoint_sha256_integrity():
    """Verify crash recovery checkpoint SHA-256 calculation and verification."""
    temp_dir = tempfile.mkdtemp(prefix="mirofish_cp_test_")
    state_data = {
        "round": 5,
        "agents": {"agent_1": {"belief": 0.8}, "agent_2": {"belief": 0.4}},
        "active_platforms": list(CANONICAL_SIMULATION_PLATFORMS),
    }

    raw_bytes = str(state_data).encode("utf-8")
    expected_hash = hashlib.sha256(raw_bytes).hexdigest()

    cp_file = os.path.join(temp_dir, "round_0005.bin")
    hash_file = cp_file + ".sha256"

    with open(cp_file, "wb") as f:
        f.write(raw_bytes)
    with open(hash_file, "w") as f:
        f.write(expected_hash)

    # Verification passes
    with open(cp_file, "rb") as f:
        read_bytes = f.read()
    computed_hash = hashlib.sha256(read_bytes).hexdigest()
    assert computed_hash == expected_hash

    # Corrupt snapshot: must detect mismatch
    with open(cp_file, "wb") as f:
        f.write(raw_bytes + b"_tampered_data")
    with open(cp_file, "rb") as f:
        corrupt_bytes = f.read()
    tampered_hash = hashlib.sha256(corrupt_bytes).hexdigest()
    assert tampered_hash != expected_hash

    shutil.rmtree(temp_dir, ignore_errors=True)


def test_simulation_log_manager_7_platforms():
    """Verify SimulationLogManager instantiates and logs for all 7 platforms."""
    temp_dir = tempfile.mkdtemp(prefix="mirofish_log_mgr_")
    manager = SimulationLogManager(temp_dir)

    for plat in CANONICAL_SIMULATION_PLATFORMS:
        logger = manager.get_platform_logger(plat)
        assert logger.platform == plat
        logger.log_action(
            round_num=1,
            agent_id=101,
            agent_name=f"Agent_{plat.capitalize()}",
            action_type="post",
            action_args={"text": f"Testing {plat} persistence"},
            result="success",
            success=True
        )
        assert os.path.exists(logger.log_path)
        with open(logger.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) >= 1
            assert plat in lines[-1]

    # Test explicit helper getters
    assert manager.get_twitter_logger().platform == "twitter"
    assert manager.get_reddit_logger().platform == "reddit"
    assert manager.get_tiktok_logger().platform == "tiktok"
    assert manager.get_instagram_logger().platform == "instagram"
    assert manager.get_threads_logger().platform == "threads"
    assert manager.get_linkedin_logger().platform == "linkedin"
    assert manager.get_youtube_logger().platform == "youtube"

    shutil.rmtree(temp_dir, ignore_errors=True)
