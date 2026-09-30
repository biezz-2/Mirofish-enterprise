"""
Model Relasional Database MiroFish (SQLAlchemy)
Mendukung SQLite (default) dan migrasi ke PostgreSQL
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class ProjectModel(Base):
    __tablename__ = "projects"
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    tasks = relationship("TaskModel", back_populates="project", cascade="all, delete-orphan")

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
