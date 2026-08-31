from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from uuid import uuid4
from multiprocessing import Queue

import yaml

from .config import Scenario, ScenarioError, load_scenario, scenario_with_delay, scenario_with_seed, scenario_with_map_curve_direction
from .dataset import audit_dataset
from .manifest import build_manifest, git_metadata, metadrive_source_metadata, write_json, wsl_boot_id
from .metrics import calculate_metrics, camera_timestamps_valid
from .report import generate_report
from .specialist import train_specialist, train_temporal_specialist

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUTS = ROOT / "outputs"
THRESHOLDS_PATH = ROOT / "configs/thresholds.yaml"


@dataclass
class RunData:
  telemetry: list[dict] = field(default_factory=list)
  camera: list[dict] = field(default_factory=list)
  events: list[dict] = field(default_factory=list)
  termination: dict | None = None
  measured: bool = False


def _write_csv(path: Path, rows: list[dict]) -> None:
  keys = sorted({key for row in rows for key in row})
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=keys)
    writer.writeheader()
    writer.writerows([{key: "" if value is None else value for key, value in row.items()} for row in rows])


def _write_camera_alignment(run_dir: Path, telemetry: list[dict]) -> None:
  captures = []
  for metadata_path in sorted((run_dir / "debug").glob("road-frame-*.png.json")):
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    frame = metadata["simulation_frame"]
    nearest = min(telemetry, key=lambda row: abs(int(row.get("simulation_frame", -1)) - frame))
    captures.append({"image": metadata_path.with_suffix("").name, "metadata": metadata,
                     "telemetry": {key: nearest.get(key) for key in ("simulation_frame", "lateral_error_m",
                     "heading_error_rad", "reference_curvature_1pm", "model_target_curvature_1pm",
                     "control_target_curvature_1pm", "model_path_end_x_m", "model_path_end_y_m",
                     "model_path_end_speed_mps", "model_valid", "model_frame_id", "model_frame_age",
                     "model_frame_drop_perc", "model_execution_time_s", "model_device_type",
                     "model_camera_sensor", "model_camera_width_px", "model_camera_height_px",
                     "model_camera_focal_length_px", "calibration_status", "calibration_roll_rad",
                     "calibration_pitch_rad", "calibration_yaw_rad", "model_left_lane_prob",
                     "model_right_lane_prob", "model_left_lane_y0_m", "model_right_lane_y0_m",
                     "specialist_teacher_curvature_1pm", "specialist_teacher_normalized_steer",
                     "traffic_vehicle_count", "traffic_active_vehicle_count", "traffic_nearest_distance_m",
                     "traffic_nearest_closing_speed_mps", "traffic_nearest_ttc_s", "collision")}})
  if captures:
    write_json(run_dir / "camera_alignment.json", {"schema_version": 1, "captures": captures})


def _write_dataset_manifest(run_dir: Path, scenario: Scenario) -> None:
  alignment_path = run_dir / "camera_alignment.json"
  if not alignment_path.exists():
    return
  captures = json.loads(alignment_path.read_text(encoding="utf-8"))["captures"]
  split = "validation" if scenario.data["environment"]["seed"] in scenario.data.get("dataset", {}).get("validation_seeds", []) else "train"
  with (run_dir / "dataset_manifest.jsonl").open("w", encoding="utf-8") as handle:
    for capture in captures:
      handle.write(json.dumps({"image": f"debug/{capture['image']}", "split": split, "metadata": capture["metadata"],
                               "labels": capture["telemetry"]}, sort_keys=True) + "\n")


def _write_specialist_manifest(run_dir: Path, scenario: Scenario, telemetry: list[dict]) -> None:
  samples = []
  split = "validation" if scenario.data["environment"]["seed"] in scenario.data["dataset"]["validation_seeds"] else "train"
  for metadata_path in sorted((run_dir / "debug").glob("road-frame-*.png.json")):
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    frame = metadata["simulation_frame"]
    nearest = min(telemetry, key=lambda row: abs(int(row.get("simulation_frame", -1)) - frame))
    target = nearest.get("specialist_teacher_normalized_steer")
    if target not in (None, ""):
      samples.append({"image": f"debug/{metadata_path.with_suffix('').name}", "split": split,
                      "simulation_frame": frame, "target_normalized_steer": float(target)})
  with (run_dir / "specialist_manifest.jsonl").open("w", encoding="utf-8") as handle:
    for sample in samples:
      handle.write(json.dumps(sample, sort_keys=True) + "\n")


def rebuild_specialist_manifests(root: Path) -> int:
  rebuilt = 0
  for run_dir in sorted(path for path in root.iterdir() if path.is_dir()):
    scenario_path, telemetry_path = run_dir / "scenario.yaml", run_dir / "telemetry.csv"
    if not scenario_path.exists() or not telemetry_path.exists():
      continue
    scenario = load_scenario(scenario_path)
    if "specialist_dataset" not in scenario.data:
      continue
    with telemetry_path.open(newline="", encoding="utf-8") as handle:
      _write_specialist_manifest(run_dir, scenario, list(csv.DictReader(handle)))
    rebuilt += 1
  return rebuilt


def _stop_process_group(process: subprocess.Popen) -> None:
  """Terminate the manager and every daemon it starts for one experiment."""
  if process.poll() is not None:
    return
  os.killpg(process.pid, signal.SIGTERM)
  try:
    process.wait(timeout=10)
  except subprocess.TimeoutExpired:
    os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=10)


def _openpilot_root() -> Path:
  value = os.environ.get("OPENPILOT_ROOT")
  if not value:
    raise RuntimeError("OPENPILOT_ROOT must point at the instrumented openpilot fork")
  root = Path(value).expanduser().resolve()
  if not (root / "openpilot/tools/sim/run_bridge.py").is_file():
    raise RuntimeError(f"OPENPILOT_ROOT is not an openpilot checkout: {root}")
  return root


def _has_renderable_vehicle_assets() -> bool:
  import metadrive
  return (Path(metadrive.__file__).resolve().parent / "assets/models/ferra/right_tire_front.gltf").is_file()


def preflight(scenario: Scenario, openpilot_root: Path, allow_dirty: bool) -> None:
  if not allow_dirty and (git_metadata(ROOT)["dirty"] or git_metadata(openpilot_root)["dirty"] or metadrive_source_metadata()["dirty"]):
    raise RuntimeError("refusing dirty working tree; commit first or pass --allow-dirty")
  if scenario.data["environment"]["map_id"] not in ("openpilot_default_loop_v1", "openpilot_serpentine_v1"):
    raise ScenarioError("unsupported map")
  specialist_replay = scenario.data.get("specialist_replay")
  if specialist_replay is not None and not (ROOT / specialist_replay["artifact_path"]).is_file():
    raise RuntimeError("specialist replay artifact is missing")
  try:
    import metadrive  # noqa: F401
  except ImportError as error:
    raise RuntimeError("MetaDrive is not importable in this Python environment") from error
  if scenario.data.get("diagnostics", {}).get("require_visible_lead") and not _has_renderable_vehicle_assets():
    raise RuntimeError("renderable MetaDrive vehicle assets are required for a visible-lead scenario")


def _outcome_thresholds() -> dict:
  data = yaml.safe_load(THRESHOLDS_PATH.read_text(encoding="utf-8"))
  outcome = data.get("outcome") if isinstance(data, dict) else None
  if not isinstance(outcome, dict) or not isinstance(outcome.get("max_abs_lateral_error_m"), (int, float)):
    raise RuntimeError("invalid outcome thresholds")
  return outcome


def _disengaged_during_measurement(events: list[dict]) -> bool:
  measuring = False
  for event in events:
    if event.get("type") == "run_state" and event.get("state") == "MEASURE":
      measuring = True
    elif measuring and event.get("type") == "openpilot_state" and not event.get("engaged"):
      return True
  return False


def _classify(data: RunData, scenario: Scenario, stop_reason: str | None) -> tuple[str, str, list[str]]:
  measured = [row for row in data.telemetry if row.get("measurement")]
  thresholds = _outcome_thresholds()
  required_traffic = scenario.data["validity"].get("min_traffic_vehicle_count")
  traffic_requirement_not_met = required_traffic is not None and (not measured or max((int(row.get("traffic_vehicle_count", 0)) for row in measured), default=0) < required_traffic)
  max_traffic_distance = scenario.data["validity"].get("max_traffic_ego_nearest_distance_m")
  observed_traffic_distance = min((float(row["traffic_nearest_distance_m"]) for row in measured if row.get("traffic_nearest_distance_m") is not None), default=None)
  traffic_proximity_not_met = max_traffic_distance is not None and (observed_traffic_distance is None or observed_traffic_distance > max_traffic_distance)
  failures = []
  if not thresholds["allow_lane_departure"] and (any(row.get("lane_departure") for row in measured) or (data.termination or {}).get("out_of_lane")):
    failures.append("lane_departure")
  if not thresholds["allow_collision"] and (any(row.get("collision") for row in measured) or (data.termination or {}).get("collision")):
    failures.append("collision")
  lateral = [abs(float(row["lateral_error_m"])) for row in measured if row.get("lateral_error_m") is not None]
  if lateral and max(lateral) > float(thresholds["max_abs_lateral_error_m"]):
    failures.append("lateral_error_threshold")
  if not thresholds["allow_disengagement_during_measurement"] and _disengaged_during_measurement(data.events):
    failures.append("disengagement")
  if data.measured and failures and not traffic_requirement_not_met and not traffic_proximity_not_met and stop_reason not in ("watchdog", "bridge_exit", "runner_exception"):
    return "valid", "fail", failures

  invalid: list[str] = []
  if not data.measured:
    invalid.append("measurement_not_started")
  if traffic_requirement_not_met:
    invalid.append("traffic_actor_coverage")
  if traffic_proximity_not_met:
    invalid.append("traffic_proximity_coverage")
  expected = scenario.data["run"]["measurement_camera_frames"] * scenario.data["logging"]["telemetry_hz"] / scenario.data["logging"]["camera_hz_nominal"]
  if len(measured) / expected < scenario.data["validity"]["min_telemetry_coverage_ratio"]:
    invalid.append("telemetry_coverage")
  if not scenario.data["validity"]["allow_frame_drop"] and any(row.get("dropped") for row in data.camera):
    invalid.append("camera_frame_drop")
  if not camera_timestamps_valid(data.camera):
    invalid.append("camera_timestamp")
  if stop_reason == "watchdog":
    invalid.append("wall_watchdog")
  elif stop_reason == "bridge_exit":
    invalid.append("bridge_exit")
  elif stop_reason == "runner_exception":
    invalid.append("runner_exception")
  if invalid:
    return "invalid", "not_evaluated", invalid
  return "valid", "fail" if failures else "pass", failures


def run_once(scenario: Scenario, *, output_root: Path = DEFAULT_OUTPUTS, allow_dirty: bool = False) -> Path:
  openpilot_root = _openpilot_root()
  preflight(scenario, openpilot_root, allow_dirty)
  run_id = f"{scenario.scenario_id}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid4().hex[:8]}"
  run_dir = output_root / run_id
  if run_dir.exists():
    raise RuntimeError(f"refusing duplicate output directory: {run_dir}")
  run_dir.mkdir(parents=True)
  (run_dir / "scenario.yaml").write_text(yaml.safe_dump(scenario.data, sort_keys=False), encoding="utf-8")
  write_json(run_dir / "manifest.json", build_manifest(run_id, scenario, ROOT, openpilot_root, ["simlab", "run", str(scenario.source)]))

  runtime_scenario = json.loads(json.dumps(scenario.data))
  if runtime_scenario.get("specialist_replay"):
    runtime_scenario["specialist_replay"]["artifact_path"] = str((ROOT / runtime_scenario["specialist_replay"]["artifact_path"]).resolve())
  sys.path.insert(0, str(openpilot_root))
  from openpilot.tools.sim.bridge.common import QueueMessageType
  from openpilot.tools.sim.bridge.metadrive.metadrive_bridge import MetaDriveBridge

  manager_log = (run_dir / "manager.log").open("w")
  pythonpath = os.pathsep.join(filter(None, (str(openpilot_root), os.environ.get("PYTHONPATH"))))
  runtime_bin = openpilot_root / ".venv/bin"
  path = os.pathsep.join((str(runtime_bin), os.environ.get("PATH", "")))
  blocked = ",".join(filter(None, (os.environ.get("BLOCK"), "soundd", "locationd")))
  manager = subprocess.Popen(["./launch_openpilot.sh"], cwd=openpilot_root / "openpilot/tools/sim",
                             env={**os.environ, "SIMULATION": "1", "SIM_TINYGRAD_DEVICE": "CUDA",
                                  "PYTHONPATH": pythonpath, "PATH": path, "BLOCK": blocked},
                             stdout=manager_log, stderr=subprocess.STDOUT, start_new_session=True)
  control_queue = status_queue = process = bridge = None
  data, stop_reason = RunData(), None
  diagnostic_frames = scenario.data.get("diagnostics", {}).get("camera_capture_frames", [])
  debug_environment = {key: os.environ.get(key) for key in ("SIMLAB_CAMERA_DEBUG_CAPTURE_FRAMES", "SIMLAB_CAMERA_DEBUG_CAPTURE_DIR")}
  if diagnostic_frames:
    os.environ["SIMLAB_CAMERA_DEBUG_CAPTURE_FRAMES"] = ",".join(map(str, diagnostic_frames))
    os.environ["SIMLAB_CAMERA_DEBUG_CAPTURE_DIR"] = str(run_dir / "debug")
  deadline = time.monotonic() + scenario.data["run"]["wall_watchdog_s"]
  try:
    control_queue, status_queue = Queue(), Queue()
    bridge = MetaDriveBridge(False, False, test_duration=float("inf"), test_run=True, simlab_config=runtime_scenario)
    process = bridge.run(control_queue, status_queue=status_queue)
    while time.monotonic() < deadline:
      if process.exitcode is not None:
        stop_reason = "bridge_exit"
        break
      while not status_queue.empty():
        message = status_queue.get()
        if message.type == QueueMessageType.TELEMETRY:
          payload = dict(message.info)
          if payload.get("type") == "run_state":
            data.events.append(payload)
            data.measured = data.measured or payload.get("state") == "MEASURE"
          elif payload.get("type") == "openpilot_state":
            data.events.append(payload)
          elif payload.get("type") == "camera_frame":
            payload["measurement"] = data.measured
            data.camera.append(payload)
          elif payload.get("type") == "vehicle_telemetry":
            payload["measurement"] = data.measured
            payload.setdefault("mono_ns", time.monotonic_ns())
            data.telemetry.append(payload)
        elif message.type == QueueMessageType.TERMINATION_INFO:
          data.termination, stop_reason = message.info, "simulator_termination"
      frames = sum(1 for row in data.camera if row.get("measurement") and row.get("camera") == "road" and not row.get("dropped"))
      if frames >= scenario.data["run"]["measurement_camera_frames"] or stop_reason:
        break
      time.sleep(0.01)
    else:
      stop_reason = "watchdog"
  except Exception as error:
    data.termination = {"runner_error": f"{type(error).__name__}: {error}"}
    stop_reason = "runner_exception"
  finally:
    if bridge is not None:
      bridge.shutdown()
    if process is not None:
      process.join(timeout=10)
      if process.is_alive():
        process.terminate()
    _stop_process_group(manager)
    manager_log.close()
    for key, value in debug_environment.items():
      if value is None:
        os.environ.pop(key, None)
      else:
        os.environ[key] = value

  _write_csv(run_dir / "telemetry.csv", data.telemetry)
  _write_csv(run_dir / "camera.csv", data.camera)
  _write_camera_alignment(run_dir, data.telemetry)
  if scenario.data.get("diagnostics", {}).get("dataset_collection"):
    _write_dataset_manifest(run_dir, scenario)
  if scenario.data.get("specialist_dataset"):
    _write_specialist_manifest(run_dir, scenario, data.telemetry)
  with (run_dir / "events.jsonl").open("w", encoding="utf-8") as handle:
    for event in data.events:
      handle.write(json.dumps(event, sort_keys=True) + "\n")
  validity, outcome, reasons = _classify(data, scenario, stop_reason)
  metrics = calculate_metrics([row for row in data.telemetry if row.get("measurement")], [row for row in data.camera if row.get("measurement")])
  write_json(run_dir / "summary.json", {"schema_version": 1, "run_id": run_id, "scenario_id": scenario.scenario_id,
    "target_delay_ms": scenario.data["fault"]["target_delay_ms"], "validity": validity, "outcome": outcome,
    "reasons": reasons, "termination_reason": stop_reason, "metrics": metrics})
  return run_dir


def recover_incomplete_run(run_dir: Path) -> Path:
  """Write an explicit invalid result after a host restart interrupted a run."""
  summary = run_dir / "summary.json"
  if summary.exists():
    raise RuntimeError("refusing to overwrite an existing summary")
  manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
  scenario = yaml.safe_load((run_dir / "scenario.yaml").read_text(encoding="utf-8"))
  recorded_boot_id, observed_boot_id = manifest.get("wsl_boot_id"), wsl_boot_id()
  write_json(summary, {"schema_version": 1, "run_id": manifest["run_id"], "scenario_id": scenario["scenario_id"],
                       "target_delay_ms": scenario["fault"]["target_delay_ms"], "validity": "invalid",
                       "outcome": "not_evaluated", "reasons": ["host_interrupted"],
                       "termination_reason": "host_interrupted", "metrics": {}, "host_recovery": {
                         "recorded_wsl_boot_id": recorded_boot_id, "observed_wsl_boot_id": observed_boot_id,
                         "wsl_boot_changed": bool(recorded_boot_id and observed_boot_id and recorded_boot_id != observed_boot_id)}})
  return summary


def run_batch(scenario: Scenario, *, output_root: Path, allow_dirty: bool) -> list[Path]:
  blocks = ((0, 100, 50, 150), (150, 50, 100, 0), (50, 0, 150, 100))
  run_once(scenario_with_delay(scenario, 0), output_root=output_root / "warmup", allow_dirty=allow_dirty)
  return [run_once(scenario_with_delay(scenario, delay), output_root=output_root, allow_dirty=allow_dirty)
          for block in blocks for delay in block]


def collect_dataset(scenario: Scenario, *, output_root: Path, allow_dirty: bool) -> list[Path]:
  dataset = scenario.data.get("dataset", {})
  seeds = dataset.get("seeds", [scenario.data["environment"]["seed"]])
  directions = dataset.get("map_curve_directions", [scenario.data["environment"].get("map_curve_direction", 0)])
  return [run_once(scenario_with_map_curve_direction(scenario_with_seed(scenario, seed), direction), output_root=output_root, allow_dirty=allow_dirty)
          for direction in directions for seed in seeds]


def main() -> None:
  parser = argparse.ArgumentParser(description="MetaDrive SIL repeatability runner")
  parser.add_argument("command", choices=("preflight", "run", "batch", "collect", "recover", "audit", "report", "train-specialist", "train-temporal-specialist", "rebuild-specialist-manifests"))
  parser.add_argument("--scenario", type=Path, default=ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml")
  parser.add_argument("--outputs", type=Path, default=DEFAULT_OUTPUTS)
  parser.add_argument("--allow-dirty", action="store_true")
  parser.add_argument("--dataset-root", type=Path)
  parser.add_argument("--artifact", type=Path)
  parser.add_argument("--run-dir", type=Path)
  parser.add_argument("--gamma-augment", action="store_true")
  args = parser.parse_args()
  if args.command == "report":
    print(generate_report(args.outputs, args.outputs / "report.md"))
    return
  if args.command == "audit":
    print(json.dumps(audit_dataset(args.outputs), indent=2, sort_keys=True))
    return
  if args.command == "train-specialist":
    if args.dataset_root is None or args.artifact is None:
      parser.error("train-specialist requires --dataset-root and --artifact")
    print(json.dumps(train_specialist(args.dataset_root, args.artifact), indent=2, sort_keys=True))
    return
  if args.command == "train-temporal-specialist":
    if args.dataset_root is None or args.artifact is None:
      parser.error("train-temporal-specialist requires --dataset-root and --artifact")
    print(json.dumps(train_temporal_specialist(args.dataset_root, args.artifact, gamma_augment=args.gamma_augment), indent=2, sort_keys=True))
    return
  if args.command == "rebuild-specialist-manifests":
    print(rebuild_specialist_manifests(args.outputs))
    return
  if args.command == "recover":
    if args.run_dir is None:
      parser.error("recover requires --run-dir")
    print(recover_incomplete_run(args.run_dir))
    return
  scenario = load_scenario(args.scenario)
  if args.command == "preflight":
    preflight(scenario, _openpilot_root(), args.allow_dirty)
    print("preflight: PASS")
  elif args.command == "run":
    print(run_once(scenario, output_root=args.outputs, allow_dirty=args.allow_dirty))
  elif args.command == "collect":
    for path in collect_dataset(scenario, output_root=args.outputs, allow_dirty=args.allow_dirty):
      print(path)
  else:
    for path in run_batch(scenario, output_root=args.outputs, allow_dirty=args.allow_dirty):
      print(path)


if __name__ == "__main__":
  main()
