"""
Model Relasional Database MiroFish (SQLAlchemy)
Mendukung SQLite (default) dan migrasi ke PostgreSQL
"""
from datetime import datetime
from typing import Set, Dict, Any, Optional
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

CANONICAL_SIMULATION_PLATFORMS = (
    "twitter",
    "reddit",
    "tiktok",
    "instagram",
    "threads",
    "linkedin",
    "youtube",
)

class ProjectModel(Base):
    __tablename__ = "projects"
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), default="created", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    tasks = relationship("TaskModel", back_populates="project", cascade="all, delete-orphan")
    simulation_runs = relationship("SimulationRunModel", back_populates="project", cascade="all, delete-orphan")

class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    task_type = Column(String(32), nullable=False)
    status = Column(String(32), default="pending")
    params_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("ProjectModel", back_populates="tasks")
    jobs = relationship("JobModel", back_populates="task", cascade="all, delete-orphan")

class JobModel(Base):
    __tablename__ = "jobs"
    id = Column(String(64), primary_key=True)
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=False)
    project_id = Column(String(64), nullable=False)
    state = Column(String(32), default="queued")
    pid = Column(Integer, nullable=True)
    current_round = Column(Integer, default=0)
    total_rounds = Column(Integer, default=10)
    progress_pct = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    task = relationship("TaskModel", back_populates="jobs")
    checkpoints = relationship("CheckpointModel", back_populates="job", cascade="all, delete-orphan")

class CheckpointModel(Base):
    __tablename__ = "checkpoints"
    id = Column(String(64), primary_key=True)
    job_id = Column(String(64), ForeignKey("jobs.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    snapshot_path = Column(String(512), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    job = relationship("JobModel", back_populates="checkpoints")

class PlatformConfigModel(Base):
    __tablename__ = "platforms_config"
    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    platform = Column(String(32), nullable=False)
    params_json = Column(Text, nullable=False)

class ResearchReportModel(Base):
    __tablename__ = "research_reports"
    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=True)
    query = Column(String(512), nullable=False)
    research_type = Column(String(32), default="general")
    facts_json = Column(Text, nullable=True)
    entities_json = Column(Text, nullable=True)
    trends_json = Column(Text, nullable=True)
    credibility_score = Column(Float, default=0.0)
    raw_results_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SettingsModel(Base):
    __tablename__ = "settings"
    key = Column(String(128), primary_key=True)
    value_encrypted = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLogModel(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SimulationRunModel(Base):
    __tablename__ = "simulation_runs"
    id = Column(String(64), primary_key=True)  # simulation_id (e.g. sim_xxx)
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=True)
    status = Column(String(32), default="idle", index=True)
    platforms_json = Column(Text, nullable=True)  # JSON array of platforms
    current_round = Column(Integer, default=0)
    total_rounds = Column(Integer, default=0)
    simulated_hours = Column(Integer, default=0)
    total_simulation_hours = Column(Integer, default=0)
    config_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("ProjectModel", back_populates="simulation_runs")
    actions = relationship("SimulationActionModel", back_populates="simulation", cascade="all, delete-orphan")

class SimulationActionModel(Base):
    __tablename__ = "simulation_actions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_id = Column(String(64), ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(32), nullable=False, index=True)  # twitter, reddit, tiktok, instagram, threads, linkedin, youtube
    round_num = Column(Integer, nullable=False, default=0, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    agent_id = Column(Integer, nullable=False, default=0, index=True)
    agent_name = Column(String(255), nullable=True)
    action_type = Column(String(64), nullable=False, index=True)
    action_args_json = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    success = Column(Boolean, default=True)

    simulation = relationship("SimulationRunModel", back_populates="actions")

    __table_args__ = (
        Index("ix_sim_actions_sim_platform", "simulation_id", "platform"),
        Index("ix_sim_actions_platform_round", "simulation_id", "platform", "round_num"),
        Index("ix_sim_actions_platform_agent", "simulation_id", "platform", "agent_id"),
        Index("ix_sim_actions_platform_type", "platform", "action_type"),
        Index("ix_sim_actions_sim_platform_time", "simulation_id", "platform", "timestamp"),
    )


# ==========================================
# State Machine & Concurrency Primitives
# ==========================================

class TaskState:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ALLOWED_TRANSITIONS = {
        PENDING: {PROCESSING, FAILED},
        PROCESSING: {COMPLETED, FAILED},
        COMPLETED: set(),
        FAILED: set(),
    }


class JobState:
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    CHECKPOINTING = "checkpointing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ALLOWED_TRANSITIONS = {
        QUEUED: {RUNNING, FAILED, CANCELLED},
        RUNNING: {CHECKPOINTING, PAUSED, COMPLETED, FAILED, CANCELLED},
        CHECKPOINTING: {RUNNING, FAILED},
        PAUSED: {RUNNING, CANCELLED, FAILED},
        COMPLETED: set(),
        FAILED: set(),
        CANCELLED: set(),
    }


def atomic_transition_task(
    session,
    task_id: str,
    expected_status: str,
    new_status: str,
    **kwargs
) -> bool:
    """
    Transisi status TaskModel secara atomik menggunakan optimistic concurrency control.
    Mengembalikan True jika update berhasil, False jika status di DB tidak cocok (race condition dicegah).
    """
    allowed = TaskState.ALLOWED_TRANSITIONS.get(expected_status, set())
    if new_status not in allowed:
        raise ValueError(f"Transisi status task tidak valid: {expected_status} -> {new_status}")

    values = {"status": new_status, **kwargs}
    rows = session.query(TaskModel).filter(
        TaskModel.id == task_id,
        TaskModel.status == expected_status
    ).update(values, synchronize_session="fetch")
    return rows > 0


def atomic_transition_job(
    session,
    job_id: str,
    expected_state: str,
    new_state: str,
    **kwargs
) -> bool:
    """
    Transisi status JobModel secara atomik menggunakan optimistic concurrency control.
    Mengembalikan True jika update berhasil, False jika state di DB tidak cocok (race condition dicegah).
    """
    allowed = JobState.ALLOWED_TRANSITIONS.get(expected_state, set())
    if new_state not in allowed:
        raise ValueError(f"Transisi status job tidak valid: {expected_state} -> {new_state}")

    values = {"state": new_state, "updated_at": datetime.utcnow(), **kwargs}
    rows = session.query(JobModel).filter(
        JobModel.id == job_id,
        JobModel.state == expected_state
    ).update(values, synchronize_session="fetch")
    return rows > 0

