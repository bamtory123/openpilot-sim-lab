#!/usr/bin/env python3
"""Build a source-hashed verdict for exactly three fixed-contract SIL repeats."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import fmean, pstdev


def digest(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--summary", type=Path, required=True, nargs=3)
  parser.add_argument("--attempt", type=Path, required=True, nargs=3)
  parser.add_argument("--output", type=Path, required=True)
  args = parser.parse_args()

  records = []
  for summary_path, attempt_path in zip(args.summary, args.attempt, strict=True):
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    attempt = json.loads(attempt_path.read_text(encoding="utf-8"))
    metrics = summary.get("metrics", {})
    eligible = (summary.get("validity") == "valid" and summary.get("outcome") == "pass"
                and summary.get("target_delay_ms") == 0 and metrics.get("camera_frames_published") == 1200
                and metrics.get("camera_frames_dropped") == 0 and not metrics.get("lane_departure_occurred")
                and not metrics.get("collision_occurred") and attempt.get("runner_exit_code") == 0
                and attempt.get("wsl_boot_changed") is False)
    records.append({
      "run_id": summary.get("run_id"),
      "summary_sha256": digest(summary_path),
      "attempt_sha256": digest(attempt_path),
      "scenario_hash": attempt.get("scenario_hash"),
      "validity": summary.get("validity"),
      "outcome": summary.get("outcome"),
      "eligible": eligible,
      "lateral_rmse_m": metrics.get("lateral_rmse_m"),
      "heading_rmse_rad": metrics.get("heading_rmse_rad"),
      "camera_frames_published": metrics.get("camera_frames_published"),
      "camera_frames_dropped": metrics.get("camera_frames_dropped"),
      "lane_departure_occurred": metrics.get("lane_departure_occurred"),
      "collision_occurred": metrics.get("collision_occurred"),
      "wsl_boot_changed": attempt.get("wsl_boot_changed"),
    })

  hashes = {record["scenario_hash"] for record in records}
  eligible = all(record["eligible"] for record in records) and len(hashes) == 1 and None not in hashes
  lateral = [float(record["lateral_rmse_m"]) for record in records if record["lateral_rmse_m"] is not None]
  result = {
    "schema_version": 1,
    "scope": "fixed_contract_three_repeat_gate_not_generalization_or_road_performance",
    "status": "pass" if eligible else "fail",
    "scenario_hash": next(iter(hashes)) if len(hashes) == 1 else None,
    "runs": records,
    "aggregate": {
      "run_count": len(records),
      "performance_eligible": eligible,
      "observed_mean_lateral_rmse_m": fmean(lateral) if len(lateral) == 3 else None,
      "observed_population_std_lateral_rmse_m": pstdev(lateral) if len(lateral) == 3 else None,
    },
  }
  args.output.parent.mkdir(parents=True, exist_ok=True)
  args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()
