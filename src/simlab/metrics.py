from __future__ import annotations

import math
from statistics import fmean, pstdev
from typing import Iterable


def _quantile(values: list[float], probability: float) -> float | None:
  if not values:
    return None
  ordered = sorted(values)
  index = (len(ordered) - 1) * probability
  low, high = math.floor(index), math.ceil(index)
  return ordered[low] if low == high else ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def _rms(values: list[float]) -> float | None:
  return math.sqrt(fmean([value * value for value in values])) if values else None


def camera_timestamps_valid(camera: Iterable[dict]) -> bool:
  """Validate per-camera source ordering and capture-to-publish causality."""
  last_source_id: dict[str, int] = {}
  last_capture_ns: dict[str, int] = {}
  for row in camera:
    if row.get("dropped"):
      continue
    required = ("camera", "source_frame_id", "capture_mono_ns", "scheduled_publish_mono_ns", "actual_publish_mono_ns")
    if any(row.get(key) is None for key in required):
      return False
    try:
      camera_name = str(row["camera"])
      source_id = int(row["source_frame_id"])
      capture_ns = int(row["capture_mono_ns"])
      scheduled_ns = int(row["scheduled_publish_mono_ns"])
      actual_ns = int(row["actual_publish_mono_ns"])
    except (TypeError, ValueError):
      return False
    if source_id <= last_source_id.get(camera_name, -1) or capture_ns < last_capture_ns.get(camera_name, -1):
      return False
    if scheduled_ns < capture_ns or actual_ns < capture_ns:
      return False
    last_source_id[camera_name] = source_id
    last_capture_ns[camera_name] = capture_ns
  return True


def calculate_metrics(telemetry: Iterable[dict], camera: Iterable[dict]) -> dict:
  rows = list(telemetry)
  camera_rows = list(camera)
  lateral = [float(row["lateral_error_m"]) for row in rows if row.get("lateral_error_m") is not None]
  heading = [float(row["heading_error_rad"]) for row in rows if row.get("heading_error_rad") is not None]
  speed = [float(row["speed_mps"]) for row in rows if row.get("speed_mps") is not None]
  applied = [(int(row["mono_ns"]), float(row["applied_steering_angle_deg"])) for row in rows
             if row.get("mono_ns") is not None and row.get("applied_steering_angle_deg") is not None]
  steering_rates = [(value - previous_value) / ((stamp - previous_stamp) / 1e9)
                    for (previous_stamp, previous_value), (stamp, value) in zip(applied, applied[1:]) if stamp > previous_stamp]
  published = [row for row in camera_rows if not row.get("dropped")]
  actual_delay = [float(row["actual_delay_ms"]) for row in published if row.get("actual_delay_ms") is not None]
  return {
    "lateral_rmse_m": _rms(lateral), "lateral_abs_p95_m": _quantile([abs(value) for value in lateral], 0.95),
    "lateral_abs_max_m": max(map(abs, lateral), default=None), "heading_rmse_rad": _rms(heading),
    "applied_steering_rate_rms_deg_s": _rms(steering_rates), "speed_mean_mps": fmean(speed) if speed else None,
    "speed_std_mps": pstdev(speed) if len(speed) > 1 else 0.0 if speed else None,
    "actual_delay_median_ms": _quantile(actual_delay, 0.5), "actual_delay_p95_ms": _quantile(actual_delay, 0.95),
    "actual_delay_max_ms": max(actual_delay, default=None), "camera_frames_published": len(published),
    "camera_frames_dropped": sum(bool(row.get("dropped")) for row in camera_rows),
    "camera_timestamps_valid": camera_timestamps_valid(camera_rows),
    "telemetry_samples": len(rows), "lane_departure_occurred": any(bool(row.get("lane_departure")) for row in rows),
    "collision_occurred": any(bool(row.get("collision")) for row in rows),
  }
