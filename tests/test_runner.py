import csv
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
from pathlib import Path

from simlab.config import Scenario, load_scenario
from simlab.manifest import build_manifest
from simlab.runner import RunData, _classify, _stop_process_group, _write_camera_alignment, _write_csv, _write_dataset_manifest, _write_specialist_manifest, preflight


def test_stops_the_manager_process_group():
  process = Mock()
  process.pid = 4242
  process.poll.return_value = None
  with patch("simlab.runner.os.killpg") as killpg:
    _stop_process_group(process)
  killpg.assert_called_once_with(4242, __import__("signal").SIGTERM)
  process.wait.assert_called_once_with(timeout=10)


def test_lane_departure_is_a_valid_failure_before_full_coverage():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(
    measured=True,
    telemetry=[{"measurement": True, "lane_departure": True}],
    termination={"out_of_lane": True},
  )

  validity, outcome, reasons = _classify(data, scenario, "simulator_termination")

  assert (validity, outcome, reasons) == ("valid", "fail", ["lane_departure"])


def test_timestamp_error_is_invalid_without_a_measured_failure():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(measured=True, camera=[{"camera": "road", "source_frame_id": 0, "capture_mono_ns": 2,
                                           "scheduled_publish_mono_ns": 1, "actual_publish_mono_ns": 2}])

  validity, outcome, reasons = _classify(data, scenario, None)

  assert (validity, outcome, reasons) == ("invalid", "not_evaluated", ["telemetry_coverage", "camera_timestamp"])


def test_lateral_kpi_threshold_is_a_valid_failure():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(measured=True, telemetry=[{"measurement": True, "lateral_error_m": 1.26}])

  validity, outcome, reasons = _classify(data, scenario, None)

  assert (validity, outcome, reasons) == ("valid", "fail", ["lateral_error_threshold"])


def test_disengagement_after_measurement_starts_is_a_valid_failure():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(measured=True, events=[{"type": "run_state", "state": "MEASURE"},
                                        {"type": "openpilot_state", "engaged": False}])

  validity, outcome, reasons = _classify(data, scenario, None)

  assert (validity, outcome, reasons) == ("valid", "fail", ["disengagement"])


def test_required_traffic_actor_absence_is_invalid():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  scenario.data["validity"]["min_traffic_vehicle_count"] = 1
  data = RunData(measured=True, telemetry=[{"measurement": True, "traffic_vehicle_count": 0}])

  validity, outcome, reasons = _classify(data, scenario, None)

  assert (validity, outcome) == ("invalid", "not_evaluated") and "traffic_actor_coverage" in reasons


def test_required_traffic_proximity_absence_is_invalid():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  scenario.data["validity"]["max_traffic_ego_nearest_distance_m"] = 30
  data = RunData(measured=True, telemetry=[{"measurement": True, "traffic_nearest_distance_m": 31}])

  validity, outcome, reasons = _classify(data, scenario, None)

  assert (validity, outcome) == ("invalid", "not_evaluated") and "traffic_proximity_coverage" in reasons


def test_visible_lead_preflight_requires_vehicle_assets(monkeypatch, tmp_path):
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  scenario.data["diagnostics"] = {"camera_capture_frames": [100], "require_visible_lead": True}
  monkeypatch.setattr("simlab.runner.git_metadata", lambda _: {"dirty": False})
  monkeypatch.setattr("simlab.runner.metadrive_source_metadata", lambda: {"dirty": False})
  monkeypatch.setattr("simlab.runner._has_renderable_vehicle_assets", lambda: False)
  monkeypatch.setitem(sys.modules, "metadrive", SimpleNamespace(__file__="/tmp/metadrive/__init__.py"))

  with __import__("pytest").raises(RuntimeError, match="renderable MetaDrive vehicle assets"):
    preflight(scenario, tmp_path, allow_dirty=False)


def test_csv_writes_none_as_an_empty_field(tmp_path):
  path = tmp_path / "telemetry.csv"
  _write_csv(path, [{"path_y_20m": None, "speed_mps": 4.0}])

  assert list(csv.DictReader(path.open())) == [{"path_y_20m": "", "speed_mps": "4.0"}]


def test_camera_alignment_joins_capture_to_nearest_telemetry(tmp_path):
  debug = tmp_path / "debug"
  debug.mkdir()
  (debug / "road-frame-000100.png.json").write_text('{"simulation_frame": 100}')

  _write_camera_alignment(tmp_path, [{"simulation_frame": 99, "lateral_error_m": 1.0},
                                      {"simulation_frame": 101, "lateral_error_m": 2.0}])

  capture = __import__("json").loads((tmp_path / "camera_alignment.json").read_text())["captures"][0]
  assert capture["image"] == "road-frame-000100.png" and capture["telemetry"]["simulation_frame"] == 99


def test_camera_alignment_includes_traffic_interaction_labels(tmp_path):
  debug = tmp_path / "debug"
  debug.mkdir()
  (debug / "road-frame-000100.png.json").write_text('{"simulation_frame": 100}')

  _write_camera_alignment(tmp_path, [{"simulation_frame": 100, "traffic_nearest_distance_m": 12.0,
                                      "traffic_nearest_closing_speed_mps": 1.5, "traffic_nearest_ttc_s": 8.0,
                                      "collision": False}])

  capture = __import__("json").loads((tmp_path / "camera_alignment.json").read_text())["captures"][0]
  assert capture["telemetry"]["traffic_nearest_ttc_s"] == 8.0


def test_dataset_manifest_uses_run_relative_image_paths(tmp_path):
  (tmp_path / "camera_alignment.json").write_text('{"captures":[{"image":"road.png","metadata":{"simulation_frame":1},"telemetry":{"lateral_error_m":0.2}}]}')

  _write_dataset_manifest(tmp_path, Scenario({"environment": {"seed": 1}}, tmp_path))

  sample = __import__("json").loads((tmp_path / "dataset_manifest.jsonl").read_text())
  assert sample["image"] == "debug/road.png" and sample["split"] == "train" and sample["labels"]["lateral_error_m"] == 0.2


def test_specialist_manifest_joins_teacher_label_to_run_relative_image(tmp_path):
  debug = tmp_path / "debug"
  debug.mkdir()
  (debug / "road-frame-000010.png.json").write_text('{"simulation_frame": 10}')
  scenario = Scenario({"environment": {"seed": 1}, "dataset": {"validation_seeds": [1]}}, tmp_path)

  _write_specialist_manifest(tmp_path, scenario, [{"simulation_frame": 10, "specialist_teacher_normalized_steer": 0.05}])

  sample = __import__("json").loads((tmp_path / "specialist_manifest.jsonl").read_text())
  assert sample == {"image": "debug/road-frame-000010.png", "split": "validation", "simulation_frame": 10, "target_normalized_steer": 0.05}


def test_manifest_records_metadrive_source_state(monkeypatch, tmp_path):
  package = tmp_path / "metadrive" / "metadrive"
  package.mkdir(parents=True)
  monkeypatch.setitem(sys.modules, "metadrive", SimpleNamespace(__file__=str(package / "__init__.py")))
  monkeypatch.setattr("simlab.manifest.git_metadata", lambda root: {"commit": "abc", "dirty": True, "submodules": ""})

  manifest = build_manifest("run", Scenario({}, tmp_path), tmp_path, tmp_path, ["simlab"])

  assert manifest["metadrive_source"] == {"path": str(package.parent), "commit": "abc", "dirty": True, "submodules": ""}
