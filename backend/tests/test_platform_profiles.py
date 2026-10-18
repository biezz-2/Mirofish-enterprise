import csv
import json

import pytest

from app.services.simulation_manager import (
    CANONICAL_PLATFORMS,
    SimulationManager,
    SimulationState,
    migrate_prepared_simulation,
)


def _manager(tmp_path, *, twitter, reddit):
    manager = SimulationManager()
    manager.SIMULATION_DATA_DIR = str(tmp_path)
    state = SimulationState(
        simulation_id="sim_test",
        project_id="proj_test",
        graph_id="graph_test",
        enable_twitter=twitter,
        enable_reddit=reddit,
    )
    manager._save_simulation_state(state)
    return manager, tmp_path / "sim_test"


def test_twitter_default_reads_generated_csv(tmp_path):
    manager, sim_dir = _manager(tmp_path, twitter=True, reddit=False)
    with (sim_dir / "twitter_profiles.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["agent_id", "name"])
        writer.writeheader()
        writer.writerow({"agent_id": "0", "name": "Alice"})

    assert manager.get_profiles("sim_test") == [{"agent_id": "0", "name": "Alice"}]


def test_reddit_default_preserves_json_behavior(tmp_path):
    manager, sim_dir = _manager(tmp_path, twitter=False, reddit=True)
    profiles = [{"user_id": 0, "username": "alice"}]
    (sim_dir / "reddit_profiles.json").write_text(json.dumps(profiles), encoding="utf-8")

    assert manager.get_profiles("sim_test") == profiles


def test_explicit_platform_overrides_dual_platform_default(tmp_path):
    manager, sim_dir = _manager(tmp_path, twitter=True, reddit=True)
    with (sim_dir / "twitter_profiles.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["agent_id", "name"])
        writer.writeheader()
        writer.writerow({"agent_id": "1", "name": "Bob"})

    assert manager.get_profiles("sim_test", platform="twitter")[0]["name"] == "Bob"


def test_invalid_platform_is_rejected(tmp_path):
    manager, _ = _manager(tmp_path, twitter=True, reddit=True)

    with pytest.raises(ValueError, match="不支持的平台"):
        manager.get_profiles("sim_test", platform="../state")


def test_migrate_prepared_simulation_clones_existing_profiles_without_resetting_state(tmp_path):
    sim_dir = tmp_path / "sim_ready"
    sim_dir.mkdir()
    original_profiles = [{"user_id": 7, "username": "alice"}]
    (sim_dir / "reddit_profiles.json").write_text(json.dumps(original_profiles), encoding="utf-8")
    with (sim_dir / "twitter_profiles.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["agent_id", "name"])
        writer.writeheader()
        writer.writerow({"agent_id": "7", "name": "Alice"})
    config = {"simulation_id": "sim_ready", "twitter_config": {"platform": "twitter"}, "reddit_config": {"platform": "reddit"}}
    (sim_dir / "simulation_config.json").write_text(json.dumps(config), encoding="utf-8")
    state = {
        "simulation_id": "sim_ready",
        "project_id": "proj_ready",
        "graph_id": "graph_ready",
        "status": "ready",
        "profiles_count": 1,
        "profiles_generated": True,
        "config_generated": True,
        "current_round": 0,
        "twitter_status": "not_started",
        "reddit_status": "not_started",
    }
    (sim_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    migrated = migrate_prepared_simulation(sim_dir)

    assert migrated["platforms"] == list(CANONICAL_PLATFORMS)
    assert migrated["status"] == "ready"
    assert migrated["current_round"] == 0
    assert migrated["profiles_count"] == 1
    assert migrated["profiles_generated"] is True
    assert migrated["config_generated"] is True
    assert migrated["platform_statuses"] == {platform: "not_started" for platform in CANONICAL_PLATFORMS}
    assert migrated["platform_states"] == {
        platform: {"profiles_count": 1, "prepared": True, "config_generated": True}
        for platform in CANONICAL_PLATFORMS
    }
    for platform in ("instagram", "linkedin", "threads", "tiktok", "youtube"):
        assert json.loads((sim_dir / f"{platform}_profiles.json").read_text(encoding="utf-8")) == original_profiles
    config = json.loads((sim_dir / "simulation_config.json").read_text(encoding="utf-8"))
    assert config["platforms"] == list(CANONICAL_PLATFORMS)
    assert set(config["platform_configs"]) == set(CANONICAL_PLATFORMS)


def test_migrate_prepared_simulation_rejects_non_ready_state(tmp_path):
    sim_dir = tmp_path / "sim_running"
    sim_dir.mkdir()
    (sim_dir / "state.json").write_text(json.dumps({"status": "running"}), encoding="utf-8")

    with pytest.raises(ValueError, match="ready"):
        migrate_prepared_simulation(sim_dir)
