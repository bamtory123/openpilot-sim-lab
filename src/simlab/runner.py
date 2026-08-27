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

from .config import Scenario, ScenarioError, load_scenario, scenario_with_delay
from .manifest import build_manifest, git_metadata, write_json
from .metrics import calculate_metrics
from .report import generate_report

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUTS = ROOT / "outputs"


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
    writer.writerows(rows)


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


def preflight(scenario: Scenario, openpilot_root: Path, allow_dirty: bool) -> None:
  if not allow_dirty and (git_metadata(ROOT)["dirty"] or git_metadata(openpilot_root)["dirty"]):
    raise RuntimeError("refusing dirty working tree; commit first or pass --allow-dirty")
  if scenario.data["environment"]["map_id"] != "openpilot_default_loop_v1":
    raise ScenarioError("unsupported map")
  try:
    import metadrive  # noqa: F401
  except ImportError as error:
    raise RuntimeError("MetaDrive is not importable in this Python environment") from error


def _classify(data: RunData, scenario: Scenario, stop_reason: str | None) -> tuple[str, str, list[str]]:
  invalid: list[str] = []
  if not data.measured:
    invalid.append("measurement_not_started")
  expected = scenario.data["run"]["measurement_camera_frames"] * scenario.data["logging"]["telemetry_hz"] / scenario.data["logging"]["camera_hz_nominal"]
  measured = [row for row in data.telemetry if row.get("measurement")]
  if len(measured) / expected < scenario.data["validity"]["min_telemetry_coverage_ratio"]:
    invalid.append("telemetry_coverage")
  if not scenario.data["validity"]["allow_frame_drop"] and any(row.get("dropped") for row in data.camera):
    invalid.append("camera_frame_drop")
  if stop_reason == "watchdog":
    invalid.append("wall_watchdog")
  if invalid:
    return "invalid", "not_evaluated", invalid
  failures = []
  if any(row.get("lane_departure") for row in measured) or (data.termination or {}).get("out_of_lane"):
    failures.append("lane_departure")
  if any(row.get("collision") for row in measured):
    failures.append("collision")
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
  deadline = time.monotonic() + scenario.data["run"]["wall_watchdog_s"]
  try:
    control_queue, status_queue = Queue(), Queue()
    bridge = MetaDriveBridge(False, False, test_duration=float("inf"), test_run=True, simlab_config=scenario.data)
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
  finally:
    if bridge is not None:
      bridge.shutdown()
    if process is not None:
      process.join(timeout=10)
      if process.is_alive():
        process.terminate()
    _stop_process_group(manager)
    manager_log.close()

  _write_csv(run_dir / "telemetry.csv", data.telemetry)
  _write_csv(run_dir / "camera.csv", data.camera)
  with (run_dir / "events.jsonl").open("w", encoding="utf-8") as handle:
    for event in data.events:
      handle.write(json.dumps(event, sort_keys=True) + "\n")
  validity, outcome, reasons = _classify(data, scenario, stop_reason)
  metrics = calculate_metrics([row for row in data.telemetry if row.get("measurement")], [row for row in data.camera if row.get("measurement")])
  write_json(run_dir / "summary.json", {"schema_version": 1, "run_id": run_id, "scenario_id": scenario.scenario_id,
    "target_delay_ms": scenario.data["fault"]["target_delay_ms"], "validity": validity, "outcome": outcome,
    "reasons": reasons, "termination_reason": stop_reason, "metrics": metrics})
  return run_dir


def run_batch(scenario: Scenario, *, output_root: Path, allow_dirty: bool) -> list[Path]:
  blocks = ((0, 100, 50, 150), (150, 50, 100, 0), (50, 0, 150, 100))
  run_once(scenario_with_delay(scenario, 0), output_root=output_root / "warmup", allow_dirty=allow_dirty)
  return [run_once(scenario_with_delay(scenario, delay), output_root=output_root, allow_dirty=allow_dirty)
          for block in blocks for delay in block]


def main() -> None:
  parser = argparse.ArgumentParser(description="MetaDrive SIL repeatability runner")
  parser.add_argument("command", choices=("preflight", "run", "batch", "report"))
  parser.add_argument("--scenario", type=Path, default=ROOT / "configs/scenarios/md_default_loop_lane0_v1.yaml")
  parser.add_argument("--outputs", type=Path, default=DEFAULT_OUTPUTS)
  parser.add_argument("--allow-dirty", action="store_true")
  args = parser.parse_args()
  if args.command == "report":
    print(generate_report(args.outputs, args.outputs / "report.md"))
    return
  scenario = load_scenario(args.scenario)
  if args.command == "preflight":
    preflight(scenario, _openpilot_root(), args.allow_dirty)
    print("preflight: PASS")
  elif args.command == "run":
    print(run_once(scenario, output_root=args.outputs, allow_dirty=args.allow_dirty))
  else:
    for path in run_batch(scenario, output_root=args.outputs, allow_dirty=args.allow_dirty):
      print(path)


if __name__ == "__main__":
  main()
