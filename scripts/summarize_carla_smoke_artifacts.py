from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
  parser = argparse.ArgumentParser(description="Summarize retained CARLA client-smoke artifacts")
  parser.add_argument("root", type=Path, help="CARLA smoke output root")
  args = parser.parse_args()
  verifier = Path(__file__).with_name("verify_carla_smoke_artifact.py")
  runs = []
  for result_path in sorted(args.root.glob("*/result.json")):
    checked = subprocess.run([sys.executable, str(verifier), str(result_path)], capture_output=True, text=True)
    result = json.loads(result_path.read_text(encoding="utf-8-sig"))
    runs.append({
      "run_id": result_path.parent.name,
      "verification": "pass" if checked.returncode == 0 else "fail",
      "status": result.get("status"),
      "artifact_schema_version": result.get("schema_version"),
      "host": result.get("host"),
      "port": result.get("port"),
      "client_version": result.get("client_observation", {}).get("client_version"),
      "server_version": result.get("client_observation", {}).get("server_version"),
      "server_stopped": result.get("server_stopped"),
      "verification_error": checked.stderr.strip() or None,
    })
  verified = [run for run in runs if run["verification"] == "pass"]
  print(json.dumps({
    "schema_version": 1,
    "scope": "carla_client_smoke_artifact_summary_only",
    "artifact_count": len(runs),
    "verified_count": len(verified),
    "latest": runs[-1] if runs else None,
    "runs": runs,
  }, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()
