1.  **Implement consistent Authentication & Authorization in backend routes:**
    *   Create a robust authentication and authorization utility `backend/app/utils/auth.py`. Since there is no actual user model available in the system yet (except maybe through some unhandled header or token), I'll implement a token-based placeholder for authentication (`require_auth`) and resource ownership (`require_resource_ownership`). The `require_auth` will check for the `Authorization` header and reject requests without it.
    *   I will apply the `@require_auth` decorator to all critical endpoints in:
        *   `backend/app/api/project.py` (if it exists, though it might be named differently or merged. I'll check `backend/app/api/graph.py` and `backend/app/api/simulation.py`). Wait, `project_id` operations are mainly in `backend/app/api/graph.py`.
        *   `backend/app/api/task.py` (check if exists, operations are likely in graph.py).
        *   `backend/app/api/graph.py`
        *   `backend/app/api/simulation.py`
        *   `backend/app/api/report.py`
    *   For endpoints that manipulate or retrieve data by ID (like `project_id`, `task_id`, `simulation_id`), I'll apply the `@require_resource_ownership` decorator to check IDOR.
2.  **Ensure Uniform HTTP 401/403 Responses:**
    *   The decorators will return a uniform JSON response (e.g., `{"success": False, "error": {"code": "UNAUTHORIZED", "message": "Missing or invalid credentials"}}`) without exposing stack traces.
3.  **Write and Run Unit Tests:**
    *   Enhance `backend/tests/test_auth.py` to test the auth decorators on mock routes.
    *   Ensure all tests pass.
4.  **Complete pre-commit steps:** Ensure tests pass and the code matches the project standards.
5.  **Submit the changes.**
