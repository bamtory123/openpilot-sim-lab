"""Run one bounded CARLA/OpenPilot adapter-pilot attempt against a ready server."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from multiprocessing import Queue
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict) -> None:
  path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
  fields = sorted({key for row in rows for key in row})
  with path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)


def stop_group(process: subprocess.Popen) -> None:
  if process.poll() is None:
    os.killpg(process.pid, signal.SIGTERM)
    try:
      process.wait(timeout=10)
    except subprocess.TimeoutExpired:
      os.killpg(process.pid, signal.SIGKILL)
      process.wait()


def main() -> None:
  parser = argparse.ArgumentParser(description="Run one CARLA v0.2 adapter pilot against a ready CARLA server")
  parser.add_argument("--openpilot-root", type=Path, required=True)
  parser.add_argument("--route-asset", type=Path, required=True)
  parser.add_argument("--host", required=True)
  parser.add_argument("--port", type=int, default=2000)
  parser.add_argument("--town", default="Town04")
  parser.add_argument("--output-root", type=Path, default=ROOT / "outputs/carla-adapter-pilot")
  parser.add_argument("--measurement-s", type=float, default=60.0)
  parser.add_argument("--settle-s", type=float, default=5.0)
  parser.add_argument("--watchdog-s", type=float, default=180.0)
  args = parser.parse_args()
  if args.measurement_s <= 0 or args.settle_s < 0 or args.watchdog_s <= args.measurement_s:
    parser.error("invalid timing arguments")
  if not args.route_asset.is_file():
    parser.error(f"route asset is missing: {args.route_asset}")
  openpilot_root = args.openpilot_root.resolve()
  if not (openpilot_root / "openpilot/tools/sim/launch_openpilot.sh").is_file():
    parser.error("--openpilot-root is not a compatible checkout")
  sys.path.insert(0, str(ROOT / "src"))
  sys.path.insert(0, str(openpilot_root))
  from simlab.carla_pilot import classify_pilot
  from openpilot.tools.sim.bridge.carla.carla_bridge import CarlaBridge
  from openpilot.tools.sim.bridge.common import QueueMessageType

  run_id = f"carla-city-mixed-pilot-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid4().hex[:8]}"
  run_dir = args.output_root / run_id
  run_dir.mkdir(parents=True)
  route_sha256 = hashlib.sha256(args.route_asset.read_bytes()).hexdigest()
  write_json(run_dir / "manifest.json", {"schema_version": 1,
    "scope": "carla_v02_adapter_pilot_not_road_qualification", "run_id": run_id,
    "route_asset": str(args.route_asset.resolve()), "route_asset_sha256": route_sha256,
    "town": args.town, "host": args.host, "port": args.port,
    "measurement_s": args.measurement_s, "settle_s": args.settle_s, "watchdog_s": args.watchdog_s,
    "control_authority": "openpilot_only", "dynamic_traffic_count": 0})
  manager_log = (run_dir / "run.log").open("w", encoding="utf-8")
  runtime_bin = openpilot_root / ".venv/bin"
  env = {**os.environ, "SIMULATION": "1", "SIM_TINYGRAD_DEVICE": "CUDA",
         "PYTHONPATH": os.pathsep.join((str(openpilot_root), os.environ.get("PYTHONPATH", ""))),
         "PATH": os.pathsep.join((str(runtime_bin), os.environ.get("PATH", ""))),
         "BLOCK": ",".join(filter(None, (os.environ.get("BLOCK"), "soundd", "locationd")))}
  manager = subprocess.Popen(["./launch_openpilot.sh"], cwd=openpilot_root / "openpilot/tools/sim", env=env,
                             stdout=manager_log, stderr=subprocess.STDOUT, start_new_session=True)
  control_q, status_q = Queue(), Queue()
  bridge = CarlaBridge(False, False, host=args.host, port=args.port, town=args.town,
                       route_asset=str(args.route_asset), test_duration=args.measurement_s + args.settle_s + 5,
                       test_run=True, simlab_config={"fault": {"target_delay_ms": 0, "queue_capacity_frames": 8},
                                                     "run": {"fault_settle_s": args.settle_s}})
  process = bridge.run(control_q, status_queue=status_q)
  lifecycle, events, telemetry, camera = ["PROCESS_START"], [], [], []
  termination, stop_reason, measured_at = None, None, None
  deadline = time.monotonic() + args.watchdog_s
  try:
    while time.monotonic() < deadline:
      if process.exitcode is not None:
        stop_reason = "bridge_exit"
        break
      while not status_q.empty():
        message = status_q.get()
        if message.type == QueueMessageType.START_STATUS:
          lifecycle.append("WAIT_SIM_READY")
          events.append({"type": "run_state", "state": "WAIT_SIM_READY", "payload": message.info})
        elif message.type == QueueMessageType.TERMINATION_INFO:
          termination, stop_reason = dict(message.info), "simulator_termination"
        elif message.type == QueueMessageType.TELEMETRY:
          payload = dict(message.info)
          if payload.get("type") == "openpilot_state":
            if "WAIT_OPENPILOT_READY" not in lifecycle:
              lifecycle.extend(("WAIT_OPENPILOT_READY", "WAIT_ENGAGEMENT"))
              events.extend(({"type": "run_state", "state": "WAIT_OPENPILOT_READY"}, {"type": "run_state", "state": "WAIT_ENGAGEMENT"}))
            events.append(payload)
          elif payload.get("type") == "run_state":
            lifecycle.append(payload["state"])
            if payload["state"] == "MEASURE":
              measured_at = time.monotonic()
            events.append(payload)
          elif payload.get("type") == "camera_frame":
            payload["measurement"] = measured_at is not None
            camera.append(payload)
          elif payload.get("type") == "vehicle_telemetry":
            payload["measurement"] = measured_at is not None
            telemetry.append(payload)
      if measured_at is not None and time.monotonic() - measured_at >= args.measurement_s:
        stop_reason = "measurement_complete"
        break
      if stop_reason:
        break
      time.sleep(0.01)
    else:
      stop_reason = "watchdog"
  finally:
    bridge.shutdown()
    process.join(timeout=10)
    if process.is_alive():
      process.terminate()
    stop_group(manager)
    manager_log.close()
  expected_camera_frames = round(args.measurement_s * 20)
  measured_telemetry = [row for row in telemetry if row.get("measurement")]
  measured_camera = [row for row in camera if row.get("measurement")]
  verdict = classify_pilot(lifecycle=lifecycle, telemetry=measured_telemetry, camera=measured_camera,
                           termination=termination, expected_camera_frames=expected_camera_frames)
  write_csv(run_dir / "telemetry.csv", telemetry)
  write_csv(run_dir / "camera.csv", camera)
  with (run_dir / "events.jsonl").open("w", encoding="utf-8") as handle:
    for event in events:
      handle.write(json.dumps(event, sort_keys=True) + "\n")
  write_json(run_dir / "summary.json", {"schema_version": 1, "pilot_status": verdict.status,
    "reasons": list(verdict.reasons), "termination": termination, "stop_reason": stop_reason,
    "lifecycle": lifecycle, "measurement_telemetry_rows": len(measured_telemetry),
    "measurement_camera_rows": len(measured_camera), "expected_camera_frames": expected_camera_frames})
  print(run_dir)


if __name__ == "__main__":
  main()
