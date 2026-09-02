from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def render_summary(evidence: dict) -> str:
  observation = evidence["observation"]
  camera = observation["camera"]
  control = observation["vehicle_control"]
  return f"""# CARLA client-smoke public sample

This is a public-safe extract from one retained CARLA client-smoke artifact. It is outside the v0.1 MetaDrive release gate and does not demonstrate an OpenPilot bridge, closed loop, route coverage, response quality, or driving capability.

## Retained observation

| Field | Value |
|---|---|
| Artifact schema | {evidence["artifact_schema_version"]} |
| CARLA client / server | {observation["client_version"]} / {observation["server_version"]} |
| RGB camera | {camera["width"]}×{camera["height"]} |
| Applied command | throttle={control["throttle"]}, steer={control["steer"]}, brake={control["brake"]} |
| Reported speed (m/s) | {observation["vehicle_speed_mps"]} |
| Actor cleanup / world restore / server stop | {observation["actors_destroyed"]} / {observation["world_settings_restored"]} / {evidence["server_stopped"]} |

The source artifact SHA-256 is `{evidence["source_sha256"]}`. It excludes local paths, server/client logs, and raw camera data. Verify the retained local artifact with `scripts/verify_carla_smoke_artifact.py` before regenerating this sample.
"""


def main() -> None:
  parser = argparse.ArgumentParser(description="Build a public-safe CARLA client-smoke sample")
  parser.add_argument("result", type=Path)
  parser.add_argument("--output-dir", type=Path, required=True)
  args = parser.parse_args()
  verifier = Path(__file__).with_name("verify_carla_smoke_artifact.py")
  subprocess.run([sys.executable, str(verifier), str(args.result)], check=True)
  source = args.result.read_bytes()
  result = json.loads(source.decode("utf-8-sig"))
  observation = result["client_observation"]
  evidence = {
    "schema_version": 1,
    "scope": "carla_client_smoke_public_sample_only",
    "artifact_schema_version": result["schema_version"],
    "source_sha256": hashlib.sha256(source).hexdigest(),
    "server_stopped": result["server_stopped"],
    "observation": {
      "client_version": observation["client_version"],
      "server_version": observation["server_version"],
      "camera": observation["camera"],
      "vehicle_control": observation["vehicle_control"],
      "vehicle_speed_mps": observation["vehicle_speed_mps"],
      "actors_destroyed": observation["actors_destroyed"],
      "world_settings_restored": observation["world_settings_restored"],
    },
  }
  args.output_dir.mkdir(parents=True, exist_ok=True)
  (args.output_dir / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  (args.output_dir / "README.md").write_text(render_summary(evidence), encoding="utf-8")


if __name__ == "__main__":
  main()
