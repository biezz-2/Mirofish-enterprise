"""
Modul Checkpoint dan Pemulihan Pasca-Crash (Crash Recovery)
Menyimpan snapshot serialisasi per ronde dan memverifikasi integritas SHA-256
"""
import os
import pickle
import hashlib
import uuid
from ..models.db_session import get_db_session
from ..models.entities import JobModel, CheckpointModel

def create_round_checkpoint(job_id: str, round_num: int, state_data: dict, snapshot_root: str = "./snapshots") -> str:
    """Menulis snapshot ronde ke disk dan mencatat hash SHA-256 ke database."""
    job_dir = os.path.join(snapshot_root, job_id)
    os.makedirs(job_dir, exist_ok=True)
    file_path = os.path.join(job_dir, f"round_{round_num:04d}.pkl")
    blob = pickle.dumps(state_data)
    with open(file_path, "wb") as f:
        f.write(blob)
    sha256 = hashlib.sha256(blob).hexdigest()
    with open(file_path + ".sha256", "w") as f:
        f.write(sha256)
        
    with get_db_session() as session:
        cp = CheckpointModel(
            id=f"cp-{uuid.uuid4().hex[:10]}",
            job_id=job_id,
            round_number=round_num,
            snapshot_path=file_path,
            sha256_hash=sha256
        )
        session.add(cp)
        job = session.query(JobModel).filter_by(id=job_id).first()
        if job:
            job.current_round = round_num
            job.progress_pct = round(round_num / max(job.total_rounds, 1) * 100, 2)
    return file_path

def restore_checkpoint(job_id: str, round_num: int, snapshot_root: str = "./snapshots") -> dict:
    """Memverifikasi hash dan memuat data snapshot ronde."""
    file_path = os.path.join(snapshot_root, job_id, f"round_{round_num:04d}.pkl")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Snapshot checkpoint tidak ada: {file_path}")
    expected_hash = open(file_path + ".sha256").read().strip()
    with open(file_path, "rb") as f:
        blob = f.read()
    actual_hash = hashlib.sha256(blob).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError("Integritas snapshot rusak: hash SHA-256 tidak cocok")
    return pickle.loads(blob)

def startup_recovery_scan(snapshot_root: str = "./snapshots") -> list:
    """Pemindaian otomatis saat backend start untuk memulihkan job terputus."""
    recovered = []
    with get_db_session() as session:
        interrupted_jobs = session.query(JobModel).filter(JobModel.state.in_(["running", "checkpointing", "paused"])).all()
        for j in interrupted_jobs:
            latest_cp = session.query(CheckpointModel).filter_by(job_id=j.id).order_by(CheckpointModel.round_number.desc()).first()
            if latest_cp:
                try:
                    restore_checkpoint(j.id, latest_cp.round_number, snapshot_root=snapshot_root)
                    j.state = "paused"
                    j.error_message = f"Otomatis dipulihkan pasca-crash dari ronde {latest_cp.round_number}"
                    recovered.append({"job_id": j.id, "action": "recovered", "last_valid_round": latest_cp.round_number})
                except Exception as e:
                    j.state = "failed"
                    j.error_message = f"Gagal memulihkan snapshot: {str(e)}"
                    recovered.append({"job_id": j.id, "action": "failed", "error": str(e)})
            else:
                j.state = "failed"
                j.error_message = "Proses terputus tanpa ada checkpoint tersimpan"
                recovered.append({"job_id": j.id, "action": "failed", "error": "No checkpoint"})
    return recovered
