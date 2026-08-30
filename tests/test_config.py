from pathlib import Path
import pytest
from simlab.config import ScenarioError, load_scenario, scenario_with_delay, scenario_with_seed

ROOT = Path(__file__).resolve().parents[1]

def test_default_scenario_is_supported_and_hash_is_stable():
  scenario = load_scenario(ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml")
  assert scenario.scenario_id == "md_default_loop_lane0_v1" and len(scenario.hash) == 64
  assert scenario_with_delay(scenario, 150).data["fault"]["target_delay_ms"] == 150
  assert scenario_with_seed(scenario, 123).data["environment"]["seed"] == 123

def test_unsupported_delay_is_rejected(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("target_delay_ms: 0", "target_delay_ms: 75"))
  with pytest.raises(ScenarioError): load_scenario(path)


def test_serpentine_map_is_supported_but_unknown_map_is_rejected(tmp_path):
  path = tmp_path / "serpentine.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("openpilot_default_loop_v1", "openpilot_serpentine_v1"))
  assert load_scenario(path).data["environment"]["map_id"] == "openpilot_serpentine_v1"
  path.write_text(path.read_text().replace("openpilot_serpentine_v1", "unknown_map"))
  with pytest.raises(ScenarioError): load_scenario(path)


def test_unsupported_camera_fov_is_rejected(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("reference_lane_index: 0", "reference_lane_index: 0\n  camera_fov_deg: 55"))
  with pytest.raises(ScenarioError): load_scenario(path)


def test_invalid_camera_pose_is_rejected(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("reference_lane_index: 0", "reference_lane_index: 0\n  camera_hpr_deg: [0, 1]"))
  with pytest.raises(ScenarioError): load_scenario(path)


def test_unsorted_camera_capture_frames_are_rejected(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text() + "\ndiagnostics:\n  camera_capture_frames: [2600, 2400]\n")
  with pytest.raises(ScenarioError): load_scenario(path)


def test_duplicate_dataset_seeds_are_rejected(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text() + "\ndataset:\n  seeds: [1, 1]\n")
  with pytest.raises(ScenarioError): load_scenario(path)


def test_reference_lane_assist_requires_complete_positive_configuration(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text() + "\nsimulator_control:\n  mode: reference_lane_assist\n")
  with pytest.raises(ScenarioError): load_scenario(path)


def test_reference_curvature_follow_requires_complete_positive_configuration(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text() + "\nsimulator_control:\n  mode: reference_curvature_follow\n")
  with pytest.raises(ScenarioError): load_scenario(path)


def test_specialist_dataset_requires_complete_positive_teacher_configuration(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text() + "\nspecialist_dataset:\n  teacher:\n    lookahead_m: 12\n")
  with pytest.raises(ScenarioError): load_scenario(path)


def test_specialist_replay_requires_artifact_and_target_speed(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text() + "\nspecialist_replay:\n  artifact_path: models/test.npz\n")
  with pytest.raises(ScenarioError): load_scenario(path)
