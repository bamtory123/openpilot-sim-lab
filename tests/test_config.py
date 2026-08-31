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


def test_low_traffic_density_is_supported_but_high_density_is_rejected(tmp_path):
  path = tmp_path / "traffic.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("reference_lane_index: 0", "reference_lane_index: 0\n  traffic_density: 0.03"))
  assert load_scenario(path).data["environment"]["traffic_density"] == 0.03
  path.write_text(path.read_text().replace("traffic_density: 0.03", "traffic_density: 0.2"))
  with pytest.raises(ScenarioError): load_scenario(path)


def test_traffic_actor_requirement_must_be_a_nonnegative_integer(tmp_path):
  path = tmp_path / "traffic.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("allow_frame_drop: false", "allow_frame_drop: false\n  min_traffic_vehicle_count: 1"))
  assert load_scenario(path).data["validity"]["min_traffic_vehicle_count"] == 1
  path.write_text(path.read_text().replace("min_traffic_vehicle_count: 1", "min_traffic_vehicle_count: -1"))
  with pytest.raises(ScenarioError): load_scenario(path)


def test_traffic_mode_is_limited_to_trigger_or_respawn(tmp_path):
  path = tmp_path / "traffic.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("reference_lane_index: 0", "reference_lane_index: 0\n  traffic_mode: respawn"))
  assert load_scenario(path).data["environment"]["traffic_mode"] == "respawn"
  path.write_text(path.read_text().replace("traffic_mode: respawn", "traffic_mode: hybrid"))
  with pytest.raises(ScenarioError): load_scenario(path)


def test_traffic_proximity_requirement_must_be_positive(tmp_path):
  path = tmp_path / "traffic.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("allow_frame_drop: false", "allow_frame_drop: false\n  max_traffic_ego_nearest_distance_m: 30"))
  assert load_scenario(path).data["validity"]["max_traffic_ego_nearest_distance_m"] == 30
  path.write_text(path.read_text().replace("max_traffic_ego_nearest_distance_m: 30", "max_traffic_ego_nearest_distance_m: 0"))
  with pytest.raises(ScenarioError): load_scenario(path)


def test_lead_vehicle_gap_is_bounded(tmp_path):
  path = tmp_path / "lead.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("reference_lane_index: 0", "reference_lane_index: 0\n  lead_vehicle:\n    gap_m: 20"))
  assert load_scenario(path).data["environment"]["lead_vehicle"]["gap_m"] == 20
  path.write_text(path.read_text().replace("gap_m: 20", "gap_m: 2"))
  with pytest.raises(ScenarioError): load_scenario(path)


def test_lead_vehicle_box_proxy_is_supported(tmp_path):
  path = tmp_path / "lead.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text().replace("reference_lane_index: 0", "reference_lane_index: 0\n  lead_vehicle:\n    gap_m: 20\n    visual_proxy: box"))
  assert load_scenario(path).data["environment"]["lead_vehicle"]["visual_proxy"] == "box"


def test_static_lead_dataset_scenario_is_a_valid_diagnostic_contract():
  scenario = load_scenario(ROOT / "configs/scenarios/md_serpentine_lane0_temporal_v06_gamma_tight_dagger_speed2_static_lead20_dataset_v1.yaml")
  assert scenario.data["diagnostics"]["dataset_collection"] is True
  assert scenario.data["environment"]["lead_vehicle"] == {"gap_m": 20}


def test_static_lead_dataset_matrix_has_a_held_out_seed():
  scenario = load_scenario(ROOT / "configs/scenarios/md_serpentine_lane0_temporal_v06_gamma_tight_dagger_speed2_static_lead20_dataset_matrix_v1.yaml")
  assert scenario.data["dataset"]["validation_seeds"] == [20260902]


def test_static_obstacle_proxy_smoke_scenario_is_valid():
  scenario = load_scenario(ROOT / "configs/scenarios/md_serpentine_lane0_temporal_v06_gamma_tight_dagger_speed2_static_obstacle_box20_smoke_v1.yaml")
  assert scenario.data["environment"]["lead_vehicle"]["visual_proxy"] == "box"


def test_static_obstacle_proxy_matrix_has_a_held_out_seed():
  scenario = load_scenario(ROOT / "configs/scenarios/md_serpentine_lane0_temporal_v06_gamma_tight_dagger_speed2_static_obstacle_box20_matrix_v1.yaml")
  assert scenario.data["dataset"]["validation_seeds"] == [20260902]


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


def test_visible_lead_requirement_must_be_boolean(tmp_path):
  path = tmp_path / "invalid.yaml"
  path.write_text((ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml").read_text() + "\ndiagnostics:\n  camera_capture_frames: [100]\n  require_visible_lead: 1\n")
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
