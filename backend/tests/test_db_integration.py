import os
import unittest
from datetime import datetime

# Setup test environment
os.environ["DATABASE_URI"] = "sqlite:///:memory:"

from backend.app.models.db_session import init_db, get_db_session
from backend.app.models.project import ProjectManager, ProjectStatus
from backend.app.models.task import TaskManager, TaskStatus
from backend.app.models.entities import ProjectModel, TaskModel

class TestDBIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_project_manager_crud(self):
        # Create
        proj = ProjectManager.create_project("Test Project")
        self.assertEqual(proj.name, "Test Project")
        self.assertEqual(proj.status, ProjectStatus.CREATED)

        # Verify in DB
        with get_db_session() as session:
            db_proj = session.query(ProjectModel).filter_by(id=proj.project_id).first()
            self.assertIsNotNone(db_proj)
            self.assertEqual(db_proj.name, "Test Project")

        # Update
        proj.name = "Updated Project"
        proj.status = ProjectStatus.GRAPH_COMPLETED
        ProjectManager.save_project(proj)

        # Get
        retrieved_proj = ProjectManager.get_project(proj.project_id)
        self.assertIsNotNone(retrieved_proj)
        self.assertEqual(retrieved_proj.name, "Updated Project")
        self.assertEqual(retrieved_proj.status, ProjectStatus.GRAPH_COMPLETED)

        # Verify in DB
        with get_db_session() as session:
            db_proj = session.query(ProjectModel).filter_by(id=proj.project_id).first()
            self.assertEqual(db_proj.name, "Updated Project")
            self.assertEqual(db_proj.status, "graph_completed")

        # List
        projects = ProjectManager.list_projects()
        self.assertTrue(any(p.project_id == proj.project_id for p in projects))

    def test_task_manager_crud(self):
        task_manager = TaskManager()

        # Need a project first due to foreign key
        proj = ProjectManager.create_project("Task Project")

        # Create
        task_id = task_manager.create_task("test_type", {"project_id": proj.project_id})
        task = task_manager.get_task(task_id)

        self.assertEqual(task.task_type, "test_type")
        self.assertEqual(task.status, TaskStatus.PENDING)

        # Verify in DB
        with get_db_session() as session:
            db_task = session.query(TaskModel).filter_by(id=task.task_id).first()
            self.assertIsNotNone(db_task)
            self.assertEqual(db_task.task_type, "test_type")

        # Update
        task_manager.update_task(task.task_id, status=TaskStatus.PROCESSING, progress=50, message="Halfway")

        # Get (simulating new instance fetching from DB)
        task_manager._tasks = {} # Clear memory cache
        retrieved_task = task_manager.get_task(task.task_id)

        self.assertIsNotNone(retrieved_task)
        self.assertEqual(retrieved_task.status, TaskStatus.PROCESSING)
        self.assertEqual(retrieved_task.progress, 50)
        self.assertEqual(retrieved_task.message, "Halfway")

        # Complete
        task_manager.complete_task(task.task_id, result={"done": True})
        task_manager._tasks = {}
        completed_task = task_manager.get_task(task.task_id)
        self.assertEqual(completed_task.status, TaskStatus.COMPLETED)
        self.assertEqual(completed_task.progress, 100)
        self.assertTrue(completed_task.result.get("done"))

if __name__ == '__main__':
    unittest.main()
