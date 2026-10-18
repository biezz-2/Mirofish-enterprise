import csv
import json
import pytest

from app.services.platform_behaviors import (
    CANONICAL_PLATFORMS,
    PLATFORM_CHARACTERISTICS,
    get_platform_behavior,
)
from app.services.simulation_manager import (
    SimulationManager,
    SimulationState,
    SimulationStatus,
    normalize_platforms,
)
from app.services.simulation_config_generator import (
    SimulationParameters,
    PlatformConfig,
)
from app.services.report_agent import Report, ReportStatus, ReportManager
from mcp_server.server import MCPServer
from mcp_server.tools import handle_create_simulation_project, handle_get_simulation_report

def test_canonical_platforms_characteristics():
    expected = ("instagram", "linkedin", "reddit", "threads", "tiktok", "twitter", "youtube")
    assert CANONICAL_PLATFORMS == expected
    for p in expected:
        assert p in PLATFORM_CHARACTERISTICS
        behavior = get_platform_behavior(p)
        assert behavior.platform == p
        assert behavior.peak_hours is not None
        assert behavior.agent_type_distribution is not None


def test_normalize_platforms():
    # Backward compatibility defaults
    assert normalize_platforms(None, enable_twitter=True, enable_reddit=True) == ["twitter", "reddit"]
    assert normalize_platforms(None, enable_twitter=True, enable_reddit=False) == ["twitter"]
    assert normalize_platforms(None, enable_twitter=False, enable_reddit=True) == ["reddit"]
    assert normalize_platforms(None, enable_twitter=False, enable_reddit=False) == []

    # Explicit list with aliases
    explicit = ["x", "ig", "yt", "li", "th", "tiktok", "reddit"]
    resolved = normalize_platforms(explicit)
    assert resolved == ["twitter", "instagram", "youtube", "linkedin", "threads", "tiktok", "reddit"]

    # Deduplication
    assert normalize_platforms(["twitter", "x", "twitter"]) == ["twitter"]

    # Rejection of invalid platforms
    with pytest.raises(ValueError, match="不支持的平台"):
        normalize_platforms(["unknown_network"])


def test_simulation_state_lifecycle(tmp_path):
    manager = SimulationManager()
    manager.SIMULATION_DATA_DIR = str(tmp_path)

    # 1. Create with custom 3 platforms
    state = manager.create_simulation(
        project_id="proj_123",
        graph_id="graph_456",
        platforms=["youtube", "linkedin", "tiktok"],
    )
    assert state.platforms == ["youtube", "linkedin", "tiktok"]
    assert not state.enable_twitter
    assert not state.enable_reddit
    assert state.platform_statuses == {
        "youtube": "not_started",
        "linkedin": "not_started",
        "tiktok": "not_started",
    }
    assert state.get_default_platform() == "youtube"

    # Save and reload
    state.platform_statuses["youtube"] = "ready"
    state.platform_states["youtube"] = {"profiles_count": 5}
    manager._save_simulation_state(state)

    reloaded = manager.get_simulation(state.simulation_id)
    assert reloaded is not None
    assert reloaded.platforms == ["youtube", "linkedin", "tiktok"]
    assert reloaded.platform_statuses["youtube"] == "ready"
    assert reloaded.platform_states["youtube"] == {"profiles_count": 5}


def test_get_profiles_multi_platform(tmp_path):
    manager = SimulationManager()
    manager.SIMULATION_DATA_DIR = str(tmp_path)

    state = manager.create_simulation(
        project_id="proj_profiles",
        graph_id="graph_profiles",
        platforms=["youtube", "twitter", "threads"],
    )
    sim_dir = tmp_path / state.simulation_id

    # Write Twitter CSV
    with (sim_dir / "twitter_profiles.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["agent_id", "name"])
        writer.writeheader()
        writer.writerow({"agent_id": "0", "name": "TwAgent"})

    # Write YouTube JSON
    yt_data = [{"user_id": 1, "username": "YtCreator"}]
    (sim_dir / "youtube_profiles.json").write_text(json.dumps(yt_data), encoding="utf-8")

    # Write Threads JSON
    th_data = [{"user_id": 2, "username": "ThUser"}]
    (sim_dir / "threads_profiles.json").write_text(json.dumps(th_data), encoding="utf-8")

    # Test reading each
    assert manager.get_profiles(state.simulation_id, platform="twitter") == [{"agent_id": "0", "name": "TwAgent"}]
    assert manager.get_profiles(state.simulation_id, platform="x") == [{"agent_id": "0", "name": "TwAgent"}]
    assert manager.get_profiles(state.simulation_id, platform="youtube") == yt_data
    assert manager.get_profiles(state.simulation_id, platform="yt") == yt_data
    assert manager.get_profiles(state.simulation_id, platform="threads") == th_data

    # Missing platform data must not inherit Reddit profiles.
    assert manager.get_profiles(state.simulation_id, platform="instagram") == []

    # Test unsupported platform
    with pytest.raises(ValueError, match="不支持的平台"):
        manager.get_profiles(state.simulation_id, platform="myspace")


def test_simulation_parameters_multi_platform():
    platforms = ["instagram", "youtube"]
    platform_configs = {
        p: PlatformConfig(
            platform=p,
            recency_weight=PLATFORM_CHARACTERISTICS[p]["recency_weight"],
            popularity_weight=PLATFORM_CHARACTERISTICS[p]["popularity_weight"],
            relevance_weight=PLATFORM_CHARACTERISTICS[p]["relevance_weight"],
            viral_threshold=int(PLATFORM_CHARACTERISTICS[p]["viral_threshold"]),
            echo_chamber_strength=float(PLATFORM_CHARACTERISTICS[p]["echo_chamber_strength"]),
        )
        for p in platforms
    }

    params = SimulationParameters(
        simulation_id="sim_params",
        project_id="proj_params",
        graph_id="graph_params",
        simulation_requirement="Uji multi platform",
        platforms=platforms,
        platform_configs=platform_configs,
    )

    data = params.to_dict()
    assert data["platforms"] == ["instagram", "youtube"]
    assert "instagram" in data["platform_configs"]
    assert "youtube" in data["platform_configs"]
    assert data["platform_configs"]["youtube"]["platform"] == "youtube"
    assert data["platform_configs"]["youtube"]["viral_threshold"] == 25000

    # Ensure json dump & load preserves platforms
    json_str = params.to_json()
    loaded = json.loads(json_str)
    assert loaded["platforms"] == ["instagram", "youtube"]


def test_report_agent_persistence(tmp_path):
    report_folder = tmp_path / "reports" / "report_test"
    report_folder.mkdir(parents=True, exist_ok=True)

    report = Report(
        report_id="report_test",
        simulation_id="sim_report",
        graph_id="graph_report",
        simulation_requirement="Testing report platforms",
        status=ReportStatus.COMPLETED,
        platforms=["linkedin", "youtube"],
        platform_statuses={"linkedin": "completed", "youtube": "completed"},
        platform_states={"linkedin": {"reach": 100}},
    )

    meta_file = report_folder / "meta.json"
    meta_file.write_text(json.dumps(report.to_dict()), encoding="utf-8")

    ReportManager.REPORTS_DIR = str(tmp_path / "reports")
    loaded_report = ReportManager.get_report("report_test")
    assert loaded_report is not None
    assert loaded_report.platforms == ["linkedin", "youtube"]
    assert loaded_report.platform_statuses == {"linkedin": "completed", "youtube": "completed"}
    assert loaded_report.platform_states == {"linkedin": {"reach": 100}}


def test_mcp_report_unavailable_fallback():
    # If simulation does not exist or report cannot be retrieved
    res = handle_get_simulation_report(project_id="nonexistent_proj", simulation_id="nonexistent_sim")
    assert res["status"] == "unavailable"
    assert res["error"] == "backend_error"
    assert res["source"] == "unavailable"
    assert "sentiment_score" not in res
    assert "consensus_score" not in res

    # FastMCP server MCPServer fallback test
    server = MCPServer()
    resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {
            "name": "get_simulation_report",
            "arguments": {"simulation_id": "missing_sim"}
        }
    })
    server_res = json.loads(resp["result"]["content"][0]["text"])
    assert server_res["status"] == "unavailable"
    assert server_res["error"] == "backend_error"
    assert server_res["source"] == "unavailable"
    assert "consensus_score" not in server_res

def test_check_simulation_prepared_dynamic(tmp_path, monkeypatch):
    from app.api.simulation import _check_simulation_prepared
    from app.config import Config

    sim_id = "sim_prepared_test"
    sim_dir = tmp_path / sim_id
    sim_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Config, "OASIS_SIMULATION_DATA_DIR", str(tmp_path))

    # Create state.json with youtube and linkedin
    state_data = {
        "simulation_id": sim_id,
        "project_id": "proj_1",
        "graph_id": "graph_1",
        "status": "ready",
        "platforms": ["youtube", "linkedin"],
        "config_generated": True,
    }
    (sim_dir / "state.json").write_text(json.dumps(state_data), encoding="utf-8")

    # Missing config and profiles
    is_prep, info = _check_simulation_prepared(sim_id)
    assert not is_prep
    assert "simulation_config.json" in info.get("missing_files", [])
    assert "youtube_profiles.json" in info.get("missing_files", [])
    assert "linkedin_profiles.json" in info.get("missing_files", [])
    # Ensure twitter and reddit are NOT required when not in platforms
    assert "twitter_profiles.csv" not in info.get("missing_files", [])
    assert "reddit_profiles.json" not in info.get("missing_files", [])

    # Now create the required files
    (sim_dir / "simulation_config.json").write_text("{}", encoding="utf-8")
    (sim_dir / "youtube_profiles.json").write_text("[{}]", encoding="utf-8")
    (sim_dir / "linkedin_profiles.json").write_text("[{}]", encoding="utf-8")

    is_prep, info = _check_simulation_prepared(sim_id)
    assert is_prep
    assert info["status"] == "ready"
