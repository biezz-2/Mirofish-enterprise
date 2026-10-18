import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_visibility_panel_is_wired_and_read_only():
    view = (ROOT / "frontend/src/views/DashboardView.vue").read_text(encoding="utf-8")
    panel = (ROOT / "frontend/src/components/dashboard/Panel8SimulationVisibility.vue").read_text(encoding="utf-8")
    api = (ROOT / "frontend/src/api/simulation.js").read_text(encoding="utf-8")

    assert "Panel8SimulationVisibility" in view
    assert "id=\"panel-8\"" in view
    for method in ("getSimulation", "getRunStatus", "getSimulationTimeline", "getSimulationActions", "getSimulationPosts", "getSimulationHistory", "getEnvStatus"):
        assert method in panel
    assert "setInterval(this.refresh, 10000)" in panel
    assert "startSimulation" not in panel
    assert "stopSimulation" not in panel
    assert "getSimulationHistory" in api


def test_missing_task_is_truthfully_labeled_by_fixture_state():
    state = json.loads((ROOT / "backend/uploads/simulations/sim_b839625f8ac2/state.json").read_text(encoding="utf-8"))
    assert state["simulation_id"] == "sim_b839625f8ac2"
    assert "task_id" not in state
    panel = (ROOT / "frontend/src/components/dashboard/Panel8SimulationVisibility.vue").read_text(encoding="utf-8")
    assert "Not present in API state" in panel
    assert "Unavailable" in panel
