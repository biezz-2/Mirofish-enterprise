"""
Job Engine & Mesin Status Transaksional MiroFish
Mengatur status job berbasis WAL dan transisi aman
"""
import uuid
import os
from datetime import datetime
from ..models.db_session import get_db_session
from ..models.entities import JobModel

VALID_TRANSITIONS = {
    "queued": ["running", "failed"],
    "running": ["checkpointing", "paused", "failed", "completed"],
    "checkpointing": ["running", "failed", "completed"],
    "paused": ["running", "failed"],
    "failed": ["recovering"],
    "recovering": ["running", "failed"],
    "completed": []
}

class JobEngine:
    """Manajer siklus hidup pekerjaan simulasi dan tugas asinkron."""

    def create_job(self, task_id: str, project_id: str, total_rounds: int = 10) -> JobModel:
        with get_db_session() as session:
            job = JobModel(
                id=f"job-{uuid.uuid4().hex[:12]}",
                task_id=task_id,
                project_id=project_id,
                state="queued",
                pid=os.getpid(),
                current_round=0,
                total_rounds=total_rounds,
                progress_pct=0.0
            )
            session.add(job)
            return job

    def transition(self, job_id: str, target_state: str, pid: int = None, error: str = None):
        with get_db_session() as session:
            job = session.query(JobModel).filter_by(id=job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} tidak ditemukan")
            allowed = VALID_TRANSITIONS.get(job.state, [])
            if target_state not in allowed:
                raise ValueError(f"Transisi terlarang: {job.state} -> {target_state}")
            job.state = target_state
            if pid is not None:
                job.pid = pid
            if error is not None:
                job.error_message = error
            job.updated_at = datetime.utcnow()

    def get_job(self, job_id: str):
        with get_db_session() as session:
            job = session.query(JobModel).filter_by(id=job_id).first()
            if not job:
                return None
            return {
                "id": job.id,
                "task_id": job.task_id,
                "project_id": job.project_id,
                "state": job.state,
                "current_round": job.current_round,
                "total_rounds": job.total_rounds,
                "progress_pct": job.progress_pct,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            }

    def list_jobs(self, project_id: str = None):
        with get_db_session() as session:
            q = session.query(JobModel)
            if project_id:
                q = q.filter_by(project_id=project_id)
            jobs = q.order_by(JobModel.created_at.desc()).all()
            return [
                {
                    "id": j.id,
                    "task_id": j.task_id,
                    "project_id": j.project_id,
                    "state": j.state,
                    "current_round": j.current_round,
                    "total_rounds": j.total_rounds,
                    "progress_pct": j.progress_pct,
                    "error_message": j.error_message,
                }
                for j in jobs
            ]
