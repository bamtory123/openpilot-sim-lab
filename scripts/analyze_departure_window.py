#!/usr/bin/env python3
"""Locate a repeatable lane-departure window across MetaDrive telemetry runs."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def _sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as stream:
    for block in iter(lambda: stream.read(1024 * 1024), b""):
      digest.update(block)
  return digest.hexdigest()


def _truth(value: str) -> bool:
  return value.strip().lower() in {"1", "true", "yes"}


def analyze_run(path: Path) -> dict:
  with path.open(newline="", encoding="utf-8") as stream:
    rows = [row for row in csv.DictReader(stream) if _truth(row["measurement"])]
  if not rows:
    raise ValueError(f"no measurement rows: {path}")

  departures = [row for row in rows if _truth(row["lane_departure"])]
  first_departure = departures[0] if departures else None
  first_lateral_1m = next((row for row in rows if abs(float(row["lateral_error_m"])) >= 1.0), None)

  def point(row: dict | None) -> dict | None:
    if row is None:
      return None
    return {
      "simulation_frame": int(row["simulation_frame"]),
      "simulation_time_s": float(row["simulation_time_s"]),
      "route_progress_m": float(row["route_progress_m"]),
      "lateral_error_m": float(row["lateral_error_m"]),
      "heading_error_rad": float(row["heading_error_rad"]),
      "reference_curvature_1pm": float(row["reference_curvature_1pm"]),
    }

  return {
    "path": str(path),
    "sha256": _sha256(path),
    "measurement_rows": len(rows),
    "first_abs_lateral_1m": point(first_lateral_1m),
    "first_lane_departure": point(first_departure),
  }


def summarize(paths: list[Path]) -> dict:
  runs = [analyze_run(path) for path in paths]
  departures = [run["first_lane_departure"] for run in runs]
  all_departed = all(point is not None for point in departures)
  curvatures = [point["reference_curvature_1pm"] for point in departures if point]
  frames = [point["simulation_frame"] for point in departures if point]
  progress = [point["route_progress_m"] for point in departures if point]
  same_curve = bool(curvatures) and all(
    math.isclose(value, curvatures[0], rel_tol=0.0, abs_tol=1e-9) for value in curvatures
  ) and not math.isclose(curvatures[0], 0.0, abs_tol=1e-9)
  bounded_frame_spread = bool(frames) and max(frames) - min(frames) <= 200
  repeatable = len(runs) >= 2 and all_departed and same_curve and bounded_frame_spread

  lateral_crossings = [run["first_abs_lateral_1m"]["simulation_frame"] for run in runs
                       if run["first_abs_lateral_1m"]]
  recommendation = None
  if repeatable and len(lateral_crossings) == len(runs):
    recommendation = {
      "purpose": "targeted_dagger_capture_before_common_departure",
      "start_frame": max(0, (min(lateral_crossings) - 600) // 20 * 20),
      "end_frame": min(frames) // 20 * 20 - 40,
      "step_frames": 20,
    }

  return {
    "schema_version": 1,
    "scope": "diagnostic_failure_localization_not_driving_performance_evidence",
    "classification": "repeatable_common_curve_departure" if repeatable else "no_repeatable_common_departure",
    "run_count": len(runs),
    "all_runs_departed": all_departed,
    "common_reference_curvature_1pm": curvatures[0] if repeatable else None,
    "departure_frame_range": [min(frames), max(frames)] if frames else None,
    "departure_progress_m_range": [min(progress), max(progress)] if progress else None,
    "recommended_capture_window": recommendation,
    "runs": runs,
  }


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--telemetry", nargs="+", required=True, type=Path)
  parser.add_argument("--output", type=Path)
  args = parser.parse_args()

  result = summarize(args.telemetry)
  payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
  if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
  print(payload, end="")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
