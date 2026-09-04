"""Summaries for bounded real-camera OpenPilot model replay."""

from __future__ import annotations

import math

import numpy as np


def _stats(values: list[float]) -> dict[str, float | None]:
  finite = np.asarray([value for value in values if math.isfinite(value)], dtype=np.float64)
  if not len(finite):
    return {"mean": None, "p95": None, "max": None}
  return {
    "mean": float(np.mean(finite)),
    "p95": float(np.quantile(finite, 0.95)),
    "max": float(np.max(finite)),
  }


def summarize_replay(model_records: list[dict], driver_records: list[dict], expected_frames: int = 60) -> dict:
  """Classify replay function separately from host timing qualification."""
  frame_ids = [int(record["frame_id"]) for record in model_records]
  core_values = [
    float(record[key])
    for record in model_records
    for key in ("model_execution_time_s", "frame_drop_pct", "path_horizon_m", "desired_curvature_1pm")
  ]
  counts_ok = len(model_records) == expected_frames and len(driver_records) == expected_frames
  frames_ordered = len(frame_ids) == len(set(frame_ids)) and all(a < b for a, b in zip(frame_ids, frame_ids[1:]))
  finite_core = bool(core_values) and all(math.isfinite(value) for value in core_values)
  functional_status = "pass" if counts_ok and frames_ordered and finite_core else "fail"

  # Match upstream model_replay.py: the first inference may include one-time initialization.
  model_timing = _stats([float(record["model_execution_time_s"]) for record in model_records[1:]])
  driver_timing = _stats([float(record["model_execution_time_s"]) for record in driver_records[1:]])
  timing_pass = (
    model_timing["max"] is not None and model_timing["max"] <= 0.050 and model_timing["mean"] <= 0.028
    and driver_timing["max"] is not None and driver_timing["max"] <= 0.050 and driver_timing["mean"] <= 0.018
  )
  timing_status = "pass" if timing_pass else "not_qualified"
  classification = f"functional_{functional_status}_timing_{timing_status}"

  return {
    "schema_version": 1,
    "scope": "pretrained_real_camera_model_replay_reference_not_closed_loop_or_road_performance",
    "classification": classification,
    "functional_status": functional_status,
    "timing_status": timing_status,
    "timing_warmup_frames_excluded": 1,
    "expected_frames": expected_frames,
    "model_v2_count": len(model_records),
    "driver_state_v2_count": len(driver_records),
    "model_frame_coverage": len(model_records) / expected_frames,
    "frame_ids_strictly_increasing": frames_ordered,
    "model": {
      "execution_time_s": model_timing,
      "frame_age": _stats([float(record["frame_age"]) for record in model_records]),
      "frame_drop_pct": _stats([float(record["frame_drop_pct"]) for record in model_records]),
      "path_horizon_m": _stats([float(record["path_horizon_m"]) for record in model_records]),
      "left_lane_probability": _stats([float(record["left_lane_probability"]) for record in model_records]),
      "right_lane_probability": _stats([float(record["right_lane_probability"]) for record in model_records]),
      "absolute_desired_curvature_1pm": _stats([abs(float(record["desired_curvature_1pm"])) for record in model_records]),
    },
    "driver_model": {"execution_time_s": driver_timing},
    "timing_contract_s": {
      "model_v2": {"max": 0.050, "mean": 0.028},
      "driver_state_v2": {"max": 0.050, "mean": 0.018},
    },
    "limitations": [
      "prerecorded_frames_do_not_respond_to_model_or_control_output",
      "functional_replay_does_not_measure_closed_loop_driving",
      "lane_probability_is_model_output_not_ground_truth_accuracy",
      "host_timing_is_not_device_timing",
    ],
  }
