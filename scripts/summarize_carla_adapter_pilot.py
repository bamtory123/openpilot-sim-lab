from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


def main() -> None:
  parser = argparse.ArgumentParser(description="Summarize retained CARLA adapter-pilot run artifacts")
  parser.add_argument("root", type=Path)
  parser.add_argument("--output", type=Path)
  parser.add_argument("--after", help="include run IDs lexically after this UTC timestamp fragment")
  args = parser.parse_args()
  summaries = []
  for path in sorted(args.root.glob("carla-city-mixed-pilot-*/summary.json")):
    timestamp = path.parent.name.split("-")[4]
    if args.after and timestamp <= args.after:
      continue
    summary = json.loads(path.read_text(encoding="utf-8"))
    if summary.get("schema_version") != 1 or "pilot_status" not in summary:
      continue
    summaries.append({"run_id": path.parent.name, "pilot_status": summary["pilot_status"], "reasons": summary.get("reasons", []),
                      "termination": summary.get("termination"), "camera_rows": summary.get("measurement_camera_rows", 0),
                      "telemetry_rows": summary.get("measurement_telemetry_rows", 0),
                      "dataset": summary.get("dataset_summary")})
  result = {"schema_version": 1, "scope": "carla_v02_adapter_pilot_not_road_qualification", "run_count": len(summaries),
            "status_counts": dict(Counter(row["pilot_status"] for row in summaries)),
            "reason_counts": dict(Counter(reason for row in summaries for reason in row["reasons"])),
            "dataset_valid_count": sum(bool(row["dataset"] and row["dataset"].get("valid")) for row in summaries),
            "dataset_joined_samples": sum(int((row["dataset"] or {}).get("joined_samples", 0)) for row in summaries), "runs": summaries}
  text = json.dumps(result, indent=2, sort_keys=True) + "\n"
  if args.output:
    args.output.write_text(text, encoding="utf-8")
  print(text, end="")


if __name__ == "__main__":
  main()
