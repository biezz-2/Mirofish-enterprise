"""
任务状态管理
用于跟踪长时间运行的任务（如图谱构建）
"""

import uuid
import threading
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from ..utils.locale import t
from .db_session import get_db_session
from .entities import TaskModel


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 等待中
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    progress: int = 0              # 总进度百分比 0-100
    message: str = ""              # 状态消息
    result: Optional[Dict] = None  # 任务结果
    error: Optional[str] = None    # 错误信息
    metadata: Dict = field(default_factory=dict)  # 额外元数据
    progress_detail: Dict = field(default_factory=dict)  # 详细进度信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "progress": self.progress,
            "message": self.message,
            "progress_detail": self.progress_detail,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


class TaskManager:
    """
    任务管理器
    线程安全的任务状态管理
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, Task] = {}
                    cls._instance._task_lock = threading.Lock()
        return cls._instance

    def _sync_to_db(self, task: Task) -> None:
        try:
            with get_db_session() as session:
                db_task = session.query(TaskModel).filter_by(id=task.task_id).first()
                if db_task:
                    db_task.status = task.status.value
                    db_task.progress = task.progress
                    db_task.message = task.message
                    db_task.result = task.result
                    db_task.error = task.error
                    db_task.metadata_json = task.metadata
                    db_task.progress_detail = task.progress_detail
                    db_task.updated_at = datetime.now()
                else:
                    db_task = TaskModel(
                        id=task.task_id,
                        project_id=task.metadata.get("project_id", "default_proj_id_for_standalone_task"), # required FK
                        task_type=task.task_type,
                        status=task.status.value,
                        progress=task.progress,
                        message=task.message,
                        result=task.result,
                        error=task.error,
                        metadata_json=task.metadata,
                        progress_detail=task.progress_detail,
                        created_at=task.created_at,
                        updated_at=datetime.now()
                    )
                    session.add(db_task)
        except Exception:
            pass

    def _sync_from_db(self, task_id: str) -> Optional[Task]:
        try:
            with get_db_session() as session:
                db_task = session.query(TaskModel).filter_by(id=task_id).first()
                if db_task:
                    status = TaskStatus.FAILED
                    try:
                        status = TaskStatus(db_task.status)
                    except ValueError:
                        pass

                    task = Task(
                        task_id=db_task.id,
                        task_type=db_task.task_type,
                        status=status,
                        created_at=db_task.created_at,
                        updated_at=db_task.updated_at,
                        progress=db_task.progress or 0,
                        message=db_task.message or "",
                        result=db_task.result,
                        error=db_task.error,
                        metadata=db_task.metadata_json or {},
                        progress_detail=db_task.progress_detail or {}
                    )
                    with self._task_lock:
                        self._tasks[task_id] = task
                    return task
        except Exception:
            pass
        return None
    
    def create_task(self, task_type: str, metadata: Optional[Dict] = None) -> str:
        """
        创建新任务
        
        Args:
            task_type: 任务类型
            metadata: 额外元数据
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        now = datetime.now()
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
        
        with self._task_lock:
            self._tasks[task_id] = task

        self._sync_to_db(task)
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                task = self._sync_from_db(task_id)
            return task
    
    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
        progress_detail: Optional[Dict] = None
    ):
        """
        更新任务状态
        """
        with self._task_lock:
            task = self.get_task(task_id) # uses lock internally, but we are already in lock, so get from dict to avoid deadlock

            task = self._tasks.get(task_id)
            if not task:
                 task = self._sync_from_db(task_id)

            if task:
                task.updated_at = datetime.now()
                if status is not None:
                    task.status = status
                if progress is not None:
                    task.progress = progress
                if message is not None:
                    task.message = message
                if result is not None:
                    task.result = result
                if error is not None:
                    task.error = error
                if progress_detail is not None:
                    task.progress_detail = progress_detail

                self._sync_to_db(task)
    
    def complete_task(self, task_id: str, result: Dict):
        """标记任务完成"""
        self.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            message=t('progress.taskComplete'),
            result=result
        )
    
    def fail_task(self, task_id: str, error: str):
        """标记任务失败"""
        self.update_task(
            task_id,
            status=TaskStatus.FAILED,
            message=t('progress.taskFailed'),
            error=error
        )
    
    def list_tasks(self, task_type: Optional[str] = None) -> list:
        """列出任务"""
        with self._task_lock:
            tasks = list(self._tasks.values())
            if task_type:
                tasks = [t for t in tasks if t.task_type == task_type]
            return [t.to_dict() for t in sorted(tasks, key=lambda x: x.created_at, reverse=True)]
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        with self._task_lock:
            old_ids = [
                tid for tid, task in self._tasks.items()
                if task.created_at < cutoff and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            ]
            for tid in old_ids:
                del self._tasks[tid]
