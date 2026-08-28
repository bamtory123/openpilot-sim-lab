from pathlib import Path
import pytest
from simlab.config import ScenarioError, load_scenario, scenario_with_delay

ROOT = Path(__file__).resolve().parents[1]

def test_default_scenario_is_supported_and_hash_is_stable():
  scenario = load_scenario(ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml")
  assert scenario.scenario_id == "md_default_loop_lane0_v1" and len(scenario.hash) == 64
  assert scenario_with_delay(scenario, 150).data["fault"]["target_delay_ms"] == 150

def test_unsupported_delay_is_rejected(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("target_delay_ms: 0", "target_delay_ms: 75"))
  with pytest.raises(ScenarioError): load_scenario(path)


def test_unsupported_camera_fov_is_rejected(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("reference_lane_index: 0", "reference_lane_index: 0\n  camera_fov_deg: 55"))
  with pytest.raises(ScenarioError): load_scenario(path)


def test_reference_lane_assist_requires_complete_positive_configuration(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text() + "\nsimulator_control:\n  mode: reference_lane_assist\n")
  with pytest.raises(ScenarioError): load_scenario(path)


def test_reference_curvature_follow_requires_complete_positive_configuration(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text() + "\nsimulator_control:\n  mode: reference_curvature_follow\n")
  with pytest.raises(ScenarioError): load_scenario(path)
