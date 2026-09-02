from __future__ import annotations

import argparse
import json
from pathlib import Path


VALID_STATUSES = {"invalid", "integrated-but-not-stable", "bounded-pass"}


def main() -> None:
  parser = argparse.ArgumentParser(description="Verify one CARLA adapter pilot artifact")
  parser.add_argument("run_dir", type=Path)
  args = parser.parse_args()
  summary_path = args.run_dir / "summary.json"
  manifest_path = args.run_dir / "manifest.json"
  if not summary_path.is_file() or not manifest_path.is_file():
    raise SystemExit("pilot artifact requires manifest.json and summary.json")
  summary = json.loads(summary_path.read_text(encoding="utf-8"))
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  if summary.get("schema_version") != 1 or summary.get("pilot_status") not in VALID_STATUSES:
    raise SystemExit("invalid CARLA adapter pilot summary")
  if manifest.get("scope") != "carla_v02_adapter_pilot_not_road_qualification":
    raise SystemExit("pilot manifest has an invalid scope")
  required = ("events.jsonl", "telemetry.csv", "camera.csv", "run.log")
  missing = [name for name in required if not (args.run_dir / name).is_file()]
  if missing:
    raise SystemExit(f"pilot artifact is missing: {', '.join(missing)}")
  print(json.dumps({"status": "pass", "pilot_status": summary["pilot_status"], "run_dir": str(args.run_dir)}, sort_keys=True))


if __name__ == "__main__":
  main()
