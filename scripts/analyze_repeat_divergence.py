#!/usr/bin/env python3
"""Locate control and trajectory divergence across repeated MetaDrive runs."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def digest(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def truth(value: str) -> bool:
  return value.strip().lower() in {"1", "true", "yes"}


def rows_by_frame(path: Path) -> dict[int, dict]:
  with path.open(newline="", encoding="utf-8") as stream:
    return {int(row["simulation_frame"]): row for row in csv.DictReader(stream) if truth(row["measurement"])}


def first_scalar_divergence(runs: list[dict[int, dict]], frames: list[int], field: str, threshold: float) -> dict | None:
  for frame in frames:
    values = [float(run[frame][field]) for run in runs]
    if max(values) - min(values) > threshold:
      return {"simulation_frame": frame, "values": values, "spread": max(values) - min(values), "threshold": threshold}
  return None


def first_position_divergence(runs: list[dict[int, dict]], frames: list[int], threshold: float) -> dict | None:
  for frame in frames:
    positions = [(float(run[frame]["position_x_m"]), float(run[frame]["position_y_m"])) for run in runs]
    spread = max(math.dist(left, right) for left in positions for right in positions)
    if spread > threshold:
      return {"simulation_frame": frame, "positions_m": positions, "spread_m": spread, "threshold_m": threshold}
  return None


def summarize(paths: list[Path]) -> dict:
  runs = [rows_by_frame(path) for path in paths]
  frames = sorted(set.intersection(*(set(run) for run in runs)))
  if not frames:
    raise ValueError("telemetry runs have no common measurement frames")
  steer = first_scalar_divergence(runs, frames, "specialist_replay_normalized_steer", 0.005)
  lateral = first_scalar_divergence(runs, frames, "lateral_error_m", 0.05)
  position = first_position_divergence(runs, frames, 0.05)
  aligned_model_frames = sum(len({run[frame]["model_frame_id"] for run in runs}) == 1 for frame in frames)
  departures = []
  for run in runs:
    row = next((run[frame] for frame in frames if truth(run[frame]["lane_departure"])), None)
    departures.append(None if row is None else {"simulation_frame": int(row["simulation_frame"]),
      "route_progress_m": float(row["route_progress_m"]), "lateral_error_m": float(row["lateral_error_m"])})
  mixed_outcome = 0 < sum(point is not None for point in departures) < len(departures)
  control_precedes_trajectory = bool(steer and lateral and steer["simulation_frame"] < lateral["simulation_frame"])
  model_frames_aligned = aligned_model_frames == len(frames)
  bifurcation = mixed_outcome and control_precedes_trajectory and model_frames_aligned
  return {
    "schema_version": 1,
    "scope": "repeat_divergence_diagnostic_not_causal_or_driving_performance_evidence",
    "classification": "closed_loop_bifurcation_observed" if bifurcation else "no_bounded_bifurcation_conclusion",
    "run_count": len(runs), "common_measurement_frame_count": len(frames),
    "common_frame_range": [frames[0], frames[-1]],
    "model_frame_id_alignment_ratio": aligned_model_frames / len(frames),
    "first_steer_divergence": steer, "first_lateral_divergence": lateral,
    "first_position_divergence": position, "lane_departures": departures,
    "telemetry_sha256": [digest(path) for path in paths],
    "limitations": ["thresholds_are_project_diagnostic_not_oem_limits",
                    "aligned_model_frame_ids_do_not_prove_identical_pixels",
                    "temporal_order_supports_localization_not_causality"],
  }


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--telemetry", type=Path, nargs="+", required=True)
  parser.add_argument("--output", type=Path, required=True)
  args = parser.parse_args()
  result = summarize(args.telemetry)
  args.output.parent.mkdir(parents=True, exist_ok=True)
  args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  print(json.dumps(result, indent=2, sort_keys=True))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
