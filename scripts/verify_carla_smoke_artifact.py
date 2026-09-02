from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_LOGS = {"server_stdout", "server_stderr", "connect", "client"}


def fail(message: str) -> None:
  raise SystemExit(message)


def main() -> None:
  parser = argparse.ArgumentParser(description="Verify one retained CARLA client-smoke artifact")
  parser.add_argument("result", type=Path, help="result.json written by run_carla_camera_smoke.ps1")
  args = parser.parse_args()
  result_path = args.result.resolve()
  try:
    result = json.loads(result_path.read_text(encoding="utf-8-sig"))
  except (OSError, json.JSONDecodeError) as error:
    fail(f"cannot read CARLA smoke result: {error}")

  if result.get("schema_version") not in {1, 2}:
    fail("unsupported CARLA smoke schema")
  if result.get("scope") != "carla_client_or_connectivity_smoke_only":
    fail("unexpected CARLA smoke scope")
  if result.get("status") not in {"pass", "fail"}:
    fail("CARLA smoke status must be pass or fail")
  logs = result.get("logs")
  if not isinstance(logs, dict) or set(logs) != REQUIRED_LOGS:
    fail("CARLA smoke must name exactly the four required logs")
  for name, filename in logs.items():
    path = result_path.parent / str(filename)
    if Path(str(filename)).name != filename or not path.is_file():
      fail(f"missing or unsafe {name} log")
  if result["status"] == "pass":
    if result.get("connect_exit_code") != 0 or result.get("client_exit_code") != 0:
      fail("passing CARLA smoke has a nonzero client exit code")
    if result.get("server_stopped") is not True or result.get("failure") is not None:
      fail("passing CARLA smoke did not cleanly stop its server")
    if result["schema_version"] == 2:
      observation = result.get("client_observation")
      if not isinstance(observation, dict) or not observation.get("client_version") or not observation.get("server_version"):
        fail("schema 2 CARLA smoke lacks client/server observation")
      camera = observation.get("camera")
      control = observation.get("vehicle_control")
      if not isinstance(camera, dict) or camera.get("width", 0) <= 0 or camera.get("height", 0) <= 0:
        fail("schema 2 CARLA smoke lacks a valid camera observation")
      if not isinstance(control, dict) or observation.get("actors_destroyed") is not True:
        fail("schema 2 CARLA smoke lacks control or cleanup observation")

  print(json.dumps({"schema_version": 1, "artifact_schema_version": result["schema_version"],
                    "scope": result["scope"], "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
  main()
