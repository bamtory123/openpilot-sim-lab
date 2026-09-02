"""Evidence contract for the bounded CARLA adapter pilot.

This is deliberately separate from v0.1 MetaDrive qualification.  It records
whether the adapter integrated, not whether openpilot is road-qualified.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PilotVerdict:
  status: str
  reasons: tuple[str, ...]


def classify_pilot(*, lifecycle: list[str], telemetry: list[dict[str, Any]], camera: list[dict[str, Any]],
                   termination: dict[str, Any] | None, expected_camera_frames: int) -> PilotVerdict:
  invalid: list[str] = []
  if "WAIT_SIM_READY" not in lifecycle or "WAIT_OPENPILOT_READY" not in lifecycle or "MEASURE" not in lifecycle:
    invalid.append("startup_or_measurement_incomplete")
  if not telemetry:
    invalid.append("telemetry_coverage")
  if invalid:
    return PilotVerdict("invalid", tuple(invalid))
  unstable: list[str] = []
  if termination:
    if termination.get("collision"):
      unstable.append("collision")
    if termination.get("lane_departure"):
      unstable.append("lane_departure")
  if any(row.get("measurement") and not row.get("engaged", True) for row in telemetry):
    unstable.append("disengagement")
  if unstable:
    return PilotVerdict("integrated-but-not-stable", tuple(unstable))
  if expected_camera_frames <= 0 or sum(not row.get("dropped", False) for row in camera) < expected_camera_frames * 0.95:
    return PilotVerdict("invalid", ("camera_coverage",))
  return PilotVerdict("bounded-pass", ())
