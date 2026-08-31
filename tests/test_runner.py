import csv
import sys
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch
from pathlib import Path

from simlab.config import Scenario, load_scenario
from simlab.manifest import build_manifest, gpu_runtime_snapshot
from simlab.runner import RunData, _classify, _coverage_ratios, _stop_process_group, _write_camera_alignment, _write_csv, _write_dataset_manifest, _write_specialist_manifest, preflight, recover_incomplete_run


def test_stops_the_manager_process_group():
  process = Mock()
  process.pid = 4242
  process.poll.return_value = None
  with patch("simlab.runner.os.killpg") as killpg:
    _stop_process_group(process)
  killpg.assert_called_once_with(4242, __import__("signal").SIGTERM)
  process.wait.assert_called_once_with(timeout=10)


def _complete_measurement():
  return [{"measurement": True, "simulation_time_s": index / 100} for index in range(6000)]


def _complete_road_camera():
  return [{"measurement": True, "camera": "road", "source_frame_id": index, "capture_mono_ns": index + 1,
           "scheduled_publish_mono_ns": index + 2, "actual_publish_mono_ns": index + 3} for index in range(1200)]


def test_coverage_shortfall_is_invalid_even_after_lane_departure():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(
    measured=True,
    telemetry=[{"measurement": True, "lane_departure": True}],
    termination={"out_of_lane": True},
  )

  validity, outcome, reasons = _classify(data, scenario, "simulator_termination")

  assert (validity, outcome, reasons) == ("invalid", "not_evaluated", ["telemetry_coverage", "camera_coverage", "insufficient_active_time:0.00s<55.00s"])


def test_lane_departure_is_a_valid_failure_with_full_coverage():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  telemetry = _complete_measurement()
  telemetry[-1]["lane_departure"] = True
  data = RunData(measured=True, telemetry=telemetry, camera=_complete_road_camera(), termination={"out_of_lane": True})

  validity, outcome, reasons = _classify(data, scenario, "simulator_termination")

  assert (validity, outcome, reasons) == ("valid", "fail", ["lane_departure"])


def test_camera_coverage_is_required_even_with_full_telemetry():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(measured=True, telemetry=_complete_measurement())

  validity, outcome, reasons = _classify(data, scenario, None)

  assert (validity, outcome) == ("invalid", "not_evaluated")
  assert reasons == ["camera_coverage"]


def test_coverage_ratios_use_measured_road_camera_frames_only():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(telemetry=_complete_measurement(), camera=_complete_road_camera() + [{"measurement": False, "camera": "road"}])

  assert _coverage_ratios(data, scenario) == (1.0, 1.0)


def test_watchdog_is_invalid_even_after_a_collision():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(measured=True, telemetry=[{"measurement": True, "collision": True}], termination={"collision": True})

  validity, outcome, reasons = _classify(data, scenario, "watchdog")

  assert (validity, outcome) == ("invalid", "not_evaluated")
  assert "wall_watchdog" in reasons


def test_runner_exception_is_invalid_even_after_a_collision():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(measured=True, telemetry=[{"measurement": True, "collision": True}], termination={"collision": True})

  validity, outcome, reasons = _classify(data, scenario, "runner_exception")

  assert (validity, outcome) == ("invalid", "not_evaluated")
  assert "runner_exception" in reasons


def test_host_interrupted_run_is_recovered_without_overwriting_results(monkeypatch, tmp_path):
  (tmp_path / "manifest.json").write_text('{"run_id": "interrupted", "created_at_utc": "2026-08-31T09:00:00+00:00", "wsl_boot_id": "before"}')
  (tmp_path / "scenario.yaml").write_text("scenario_id: interrupted\nfault:\n  target_delay_ms: 50\n")
  monkeypatch.setattr("simlab.runner.wsl_boot_id", lambda: "after")

  summary = recover_incomplete_run(tmp_path)

  recovered = __import__("json").loads(summary.read_text())
  assert recovered["reasons"] == ["host_interrupted"] and recovered["host_recovery"]["wsl_boot_changed"] is True
  assert recovered["host_recovery"]["recorded_created_at_utc"] == "2026-08-31T09:00:00+00:00"
  with __import__("pytest").raises(RuntimeError, match="existing summary"):
    recover_incomplete_run(tmp_path)


def test_timestamp_error_is_invalid_without_a_measured_failure():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(measured=True, camera=[{"camera": "road", "source_frame_id": 0, "capture_mono_ns": 2,
                                           "scheduled_publish_mono_ns": 1, "actual_publish_mono_ns": 2}])

  validity, outcome, reasons = _classify(data, scenario, None)

  assert (validity, outcome, reasons) == ("invalid", "not_evaluated", ["telemetry_coverage", "camera_coverage", "insufficient_active_time:0.00s<55.00s", "camera_timestamp"])


def test_lateral_kpi_threshold_is_a_valid_failure():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  telemetry = _complete_measurement()
  telemetry[-1]["lateral_error_m"] = 1.26
  data = RunData(measured=True, telemetry=telemetry, camera=_complete_road_camera())

  validity, outcome, reasons = _classify(data, scenario, None)

  assert (validity, outcome, reasons) == ("valid", "fail", ["lateral_error_threshold"])


def test_disengagement_after_measurement_starts_is_a_valid_failure():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  telemetry = _complete_measurement()
  data = RunData(measured=True, events=[{"type": "run_state", "state": "MEASURE"},
                                        {"type": "openpilot_state", "engaged": False}], telemetry=telemetry, camera=_complete_road_camera())

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


def test_camera_alignment_preserves_static_obstacle_bbox_metadata(tmp_path):
  debug = tmp_path / "debug"
  debug.mkdir()
  (debug / "road-frame-000100.png.json").write_text('{"simulation_frame":100,"static_obstacle_bbox_xyxy_px":[1,2,3,4]}')

  _write_camera_alignment(tmp_path, [{"simulation_frame": 100}])

  capture = __import__("json").loads((tmp_path / "camera_alignment.json").read_text())["captures"][0]
  assert capture["metadata"]["static_obstacle_bbox_xyxy_px"] == [1, 2, 3, 4]


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
  assets = package / "assets"
  (assets / "models" / "ferra").mkdir(parents=True)
  (assets / "version.txt").write_text("0.4.2.3")
  (assets / "models" / "ferra" / "vehicle.gltf").write_bytes(b"vehicle")
  monkeypatch.setitem(sys.modules, "metadrive", SimpleNamespace(__file__=str(package / "__init__.py")))
  monkeypatch.setattr("simlab.manifest.git_metadata", lambda root: {"commit": "abc", "dirty": True, "submodules": ""})

  manifest = build_manifest("run", Scenario({}, tmp_path), tmp_path, tmp_path, ["simlab"])

  assert manifest["metadrive_source"] == {"path": str(package.parent), "commit": "abc", "dirty": True, "submodules": ""}
  assert manifest["metadrive_assets"]["version"] == "0.4.2.3"
  assert manifest["metadrive_assets"]["ferra_vehicle_available"] is True
  assert datetime.fromisoformat(manifest["created_at_utc"]).tzinfo is not None


def test_gpu_runtime_snapshot_parses_nvidia_smi_fields(monkeypatch):
  monkeypatch.setattr("simlab.manifest._command", lambda args, cwd=None: "52, 0, 1000, 16376, P0")

  snapshot = gpu_runtime_snapshot()

  assert snapshot == {"temperature_c": "52", "utilization_percent": "0", "memory_used_mib": "1000",
                      "memory_total_mib": "16376", "pstate": "P0"}
