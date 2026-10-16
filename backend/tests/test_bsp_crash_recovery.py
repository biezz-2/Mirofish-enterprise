"""
Test Suite untuk Agent 14: BSP Swarm Runner & SQLite WAL Crash Recovery
(Slice 14 / Master Plan v3.2 Divisi D)

Menguji:
1. Determinisme Kriptografi SHA-256 pada State Agen & Canonical JSON.
2. SQLite WAL Checkpointing: PRAGMA WAL, atomisitas simpan/pulih, deteksi korupsi.
3. Bulk Synchronous Parallel (BSP) Supersteps: Local Computation -> Communication -> Barrier Synchronization.
4. Zero-Loss Crash Recovery: Simulasi crash pada ronde K dan auto-resume hingga target ronde tanpa kehilangan data.
5. Skalabilitas Predictive Sandbox: 50 agen x 15 ronde x 8 platform (6.000 aksi evaluasi) tanpa deadlock.
6. Handoff Parameter Terkalibrasi untuk Agent 15 (ReACT ReportAgent).
7. Enterprise API Endpoints (/api/enterprise/bsp/*).
"""

import os
import json
import time
import uuid
import tempfile
import pytest
from flask import Flask

from app.services.bsp_swarm_runner import (
    BSPAgentState,
    BSPMessage,
    BSPBarrierMetrics,
    BSPCheckpointRecord,
    BSPSimulationMetrics,
    BSPSimulationResult,
    SQLiteWALCheckpointer,
    BSPSwarmRunner,
    RECOMMENDED_STATE_HASH_FIELDS,
    DEFAULT_PLATFORM_SYNC_INTERVALS_MS
)
from app.services.cascade_dynamics import EXTENDED_PLATFORMS, CANONICAL_7_PLATFORMS
from app.api.enterprise import enterprise_bp


# =============================================================================
# 1. Unit Tests: SHA-256 Determinism & Schema Verification
# =============================================================================

def test_bsp_agent_state_canonical_hash():
    """Memastikan representasi canonical hash agen deterministik dan sensitif terhadap perubahan."""
    agent1 = BSPAgentState(
        agent_id="x_agent_001",
        platform="x",
        v_dopamine=0.5500,
        is_active=True,
        consecutive_frustrations=0,
        posts_created=2,
        last_prediction_error=0.0500
    )
    agent2 = BSPAgentState(
        agent_id="x_agent_001",
        platform="x",
        v_dopamine=0.5500,
        is_active=True,
        consecutive_frustrations=0,
        posts_created=2,
        last_prediction_error=0.0500
    )

    d1 = agent1.to_canonical_hash_dict()
    d2 = agent2.to_canonical_hash_dict()
    assert d1 == d2

    str1 = SQLiteWALCheckpointer.serialize_state_canonically(d1)
    str2 = SQLiteWALCheckpointer.serialize_state_canonically(d2)
    hash1 = SQLiteWALCheckpointer.compute_sha256(str1)
    hash2 = SQLiteWALCheckpointer.compute_sha256(str2)
    assert hash1 == hash2, "Hash untuk state identik harus sama persis"

    # Mutasi salah satu field kunci
    agent2.v_dopamine = 0.5501
    d2_mutated = agent2.to_canonical_hash_dict()
    hash2_mutated = SQLiteWALCheckpointer.compute_sha256(SQLiteWALCheckpointer.serialize_state_canonically(d2_mutated))
    assert hash1 != hash2_mutated, "Hash harus berubah saat dopamin dimutasi"


# =============================================================================
# 2. SQLite WAL Checkpointer: WAL Mode, Atomisitas & Deteksi Korupsi
# =============================================================================

def test_sqlite_wal_mode_and_checkpoint():
    """Memverifikasi inisialisasi WAL mode, penulisan checkpoint, dan eksekusi WAL pragma."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_wal.db")
        snap_dir = os.path.join(tmpdir, "snaps")
        checkpointer = SQLiteWALCheckpointer(db_path=db_path, snapshot_dir=snap_dir)

        # Periksa mode WAL pada koneksi disk
        conn = checkpointer._get_connection()
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        conn.close()
        assert journal_mode.lower() == "wal", f"Journal mode harus WAL, didapat: {journal_mode}"

        # Simpan checkpoint ronde 1 sampai 5
        job_id = "test_job_wal"
        for r in range(1, 6):
            state = {
                "round_num": r,
                "agents": [{"agent_id": f"ag_{i}", "v_dopamine": 0.5} for i in range(10)],
                "platforms": {"x": 10}
            }
            rec = checkpointer.save_checkpoint(
                job_id=job_id,
                round_num=r,
                superstep_id=f"BSP_BARRIER_{r}",
                state_dict=state,
                active_agents_count=10,
                events_generated=15,
                wal_checkpoint_frequency=5
            )
            assert len(rec.sha256_hash) == 64, "Hash SHA-256 harus 64 karakter heksadesimal"
            assert rec.status == "COMMITTED"
            if r == 5:
                assert rec.wal_checkpoint_executed is True, "Ronde ke-5 harus mengeksekusi WAL checkpoint"

        # Verifikasi pemulihan (restore) ronde 3
        restored_3 = checkpointer.restore_checkpoint(job_id, 3)
        assert restored_3["round_num"] == 3
        assert len(restored_3["agents"]) == 10

        # Verifikasi deteksi korupsi integritas
        checkpointer.corrupt_checkpoint_for_testing(job_id, 3)
        with pytest.raises(ValueError, match="Integritas snapshot rusak"):
            checkpointer.restore_checkpoint(job_id, 3)


# =============================================================================
# 3. Bulk Synchronous Parallel (BSP) Swarm Execution & Barrier Sync
# =============================================================================

def test_bsp_barrier_sync_and_supersteps():
    """Menguji eksekusi superstep BSP dengan sinkronisasi penghalang (Barrier) multi-platform."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_bsp.db")
        checkpointer = SQLiteWALCheckpointer(db_path=db_path, snapshot_dir=tmpdir)
        runner = BSPSwarmRunner(
            bsp_superstep_barrier_interval=1,
            batch_size_agents=10,
            max_barrier_timeout_ms=5000.0,
            sqlite_wal_checkpoint_frequency_rounds=2,
            checkpointer=checkpointer
        )

        # Uji dengan 4 platform kanonikal x 10 agen x 3 ronde = 120 aksi
        test_platforms = ["x", "reddit", "tiktok", "instagram"]
        res = runner.run_swarm_simulation(
            agents_per_platform=10,
            rounds=3,
            platforms=test_platforms,
            job_id="test_bsp_sync_job"
        )

        assert res.success is True
        assert res.status == "COMPLETED"
        assert res.metrics.deadlock_detected is False
        assert res.metrics.barrier_sync_success_rate == 1.0
        assert res.metrics.total_rounds == 3
        assert res.metrics.total_actions_evaluated == 10 * 3 * 4  # 120 aksi
        assert len(res.metrics.checkpoint_chain) == 3

        # Pastikan seluruh checkpoint berstatus COMMITTED
        for cp in res.metrics.checkpoint_chain:
            assert cp["status"] == "COMMITTED"
            assert len(cp["sha256"]) == 64


# =============================================================================
# 4. Zero-Loss Crash Recovery & Auto-Resume
# =============================================================================

def test_zero_loss_crash_simulation_and_recovery():
    """
    Mensimulasikan crash server di tengah jalan (ronde 4 dari 8),
    lalu memanggil auto-resume dan memverifikasi rantai hash SHA-256 utuh.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "crash_test.db")
        checkpointer = SQLiteWALCheckpointer(db_path=db_path, snapshot_dir=tmpdir)
        runner = BSPSwarmRunner(
            bsp_superstep_barrier_interval=1,
            batch_size_agents=10,
            max_barrier_timeout_ms=5000.0,
            sqlite_wal_checkpoint_frequency_rounds=2,
            checkpointer=checkpointer
        )

        job_id = "test_crash_recovery_job"
        test_platforms = ["x", "tiktok", "youtube"]

        crash_report = runner.run_with_simulated_crash(
            job_id=job_id,
            total_rounds=8,
            crash_at_round=4,
            agents_per_platform=10,
            platforms=test_platforms
        )

        assert crash_report["recovery_successful"] is True
        assert crash_report["total_rounds_completed"] == 8
        assert crash_report["chain_length"] == 8
        assert crash_report["deadlock_detected"] is False

        # Verifikasi bahwa checkpoint ronde 4 dan ronde 8 valid dan tidak korup
        cp_4 = checkpointer.restore_checkpoint(job_id, 4)
        assert cp_4["round_num"] == 4
        cp_8 = checkpointer.restore_checkpoint(job_id, 8)
        assert cp_8["round_num"] == 8


# =============================================================================
# 5. Skalabilitas Sandbox Prediktif (50 Agen x 15 Ronde x 8 Platform = 6.000 Aksi)
# =============================================================================

def test_predictive_sandbox_6000_actions():
    """
    Verifikasi benchmark: 50 agen x 15 ronde x 8 platform = 6.000 aksi evaluasi.
    Memverifikasi tidak adanya deadlock, barrier rate 100%, dan pembuatan WAL checkpoints.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "sandbox_6000.db")
        checkpointer = SQLiteWALCheckpointer(db_path=db_path, snapshot_dir=tmpdir)
        runner = BSPSwarmRunner(
            bsp_superstep_barrier_interval=1,
            batch_size_agents=50,
            max_barrier_timeout_ms=5000.0,
            sqlite_wal_checkpoint_frequency_rounds=5,
            checkpointer=checkpointer
        )

        res = runner.run_swarm_simulation(
            agents_per_platform=50,
            rounds=15,
            platforms=EXTENDED_PLATFORMS,  # 8 platform
            job_id="sandbox_eval_6000"
        )

        assert res.success is True
        assert res.status == "COMPLETED"
        assert res.metrics.total_actions_evaluated == 6000
        assert res.metrics.deadlock_detected is False
        assert res.metrics.barrier_sync_success_rate == 1.0
        assert res.metrics.wal_checkpoints_executed == 3  # ronde 5, 10, 15
        assert len(res.metrics.checkpoint_chain) == 15

        # Downstream recommendations check
        recs = res.downstream_recommendations
        assert recs["integrity_attestation"] == "SHA-256_CHAIN_VERIFIED"
        assert recs["zero_loss_crash_recovery_certified"] is True
        assert recs["target_subagent"] == "Agent 15: ReACT ReportAgent Multi-Turn Deduction Analyst"
        assert len(recs["recommended_citation_nodes"]) >= 2


# =============================================================================
# 6. Enterprise API Flask Endpoint Tests
# =============================================================================

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(enterprise_bp, url_prefix='/api/enterprise')
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_api_bsp_simulate(client):
    """Uji API /api/enterprise/bsp/simulate."""
    payload = {
        "agents_per_platform": 5,
        "rounds": 2,
        "platforms": ["x", "reddit"]
    }
    resp = client.post('/api/enterprise/bsp/simulate', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["metrics"]["total_actions_evaluated"] == 5 * 2 * 2  # 20 aksi
    assert data["metrics"]["deadlock_detected"] is False


def test_api_bsp_checkpoint_and_status(client):
    """Uji API /api/enterprise/bsp/checkpoint dan /api/enterprise/bsp/status/<job_id>."""
    job_id = f"test_api_job_{int(time.time())}"
    state_payload = {
        "job_id": job_id,
        "round_num": 1,
        "superstep_id": "BSP_BARRIER_1",
        "state_dict": {"data": "test_state_123"},
        "active_agents": 25,
        "events_generated": 10
    }
    # Simpan checkpoint
    cp_resp = client.post('/api/enterprise/bsp/checkpoint', json=state_payload)
    assert cp_resp.status_code == 200
    cp_data = cp_resp.get_json()
    assert cp_data["success"] is True
    assert len(cp_data["checkpoint"]["sha256_hash"]) == 64

    # Cek status
    status_resp = client.get(f'/api/enterprise/bsp/status/{job_id}')
    assert status_resp.status_code == 200
    st_data = status_resp.get_json()
    assert st_data["success"] is True
    assert st_data["has_checkpoints"] is True
    assert st_data["checkpoints_count"] == 1


def test_api_bsp_downstream_recommendations(client):
    """Uji API /api/enterprise/bsp/downstream-recommendations."""
    resp = client.get('/api/enterprise/bsp/downstream-recommendations?job_id=test_job_rec')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    recs = data["recommendations"]
    assert recs["target_subagent"] == "Agent 15: ReACT ReportAgent Multi-Turn Deduction Analyst"
    assert "safe_abstention_rules" in recs
