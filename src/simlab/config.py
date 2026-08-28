from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


class ScenarioError(ValueError):
  pass


@dataclass(frozen=True)
class Scenario:
  data: dict[str, Any]
  source: Path

  @property
  def scenario_id(self) -> str:
    return self.data["scenario_id"]

  @property
  def hash(self) -> str:
    canonical = json.dumps(self.data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def _require(mapping: dict[str, Any], key: str, expected: type) -> None:
  if key not in mapping or not isinstance(mapping[key], expected):
    raise ScenarioError(f"missing or invalid {key}")


def validate_scenario(data: dict[str, Any]) -> None:
  if data.get("schema_version") != 1:
    raise ScenarioError("only schema_version 1 is supported")
  _require(data, "scenario_id", str)
  for section in ("environment", "run", "fault", "validity", "logging"):
    _require(data, section, dict)
  env, run, fault, validity, logging = (data[x] for x in ("environment", "run", "fault", "validity", "logging"))
  if env.get("map_id") != "openpilot_default_loop_v1":
    raise ScenarioError("v0.1 supports only openpilot_default_loop_v1")
  if not isinstance(env.get("seed"), int) or env.get("reference_lane_index") not in (0, 1):
    raise ScenarioError("seed and reference_lane_index must be concrete")
  if "camera_fov_deg" in env and env["camera_fov_deg"] not in (40, 60):
    raise ScenarioError("camera_fov_deg must be an approved diagnostic value")
  for key in ("camera_position_m", "camera_hpr_deg"):
    if key in env and (not isinstance(env[key], list) or len(env[key]) != 3 or not all(isinstance(value, (int, float)) for value in env[key])):
      raise ScenarioError(f"{key} must be a three-value numeric vector")
  if fault.get("type") != "camera_transport_delay" or fault.get("target_delay_ms") not in (0, 50, 100, 150):
    raise ScenarioError("v0.1 supports a 0/50/100/150 ms camera_transport_delay only")
  if fault.get("queue_capacity_frames", 0) < 1 or fault.get("overflow_policy") != "invalid_run":
    raise ScenarioError("queue must be bounded and overflow must invalidate the run")
  if run.get("measurement_camera_frames", 0) < 1 or run.get("wall_watchdog_s", 0) < 1:
    raise ScenarioError("measurement and watchdog must be positive")
  if logging.get("telemetry_hz") != 100 or logging.get("camera_hz_nominal") != 20:
    raise ScenarioError("v0.1 rate contract is 100 Hz telemetry / 20 Hz camera")
  if not isinstance(validity.get("allow_frame_drop"), bool):
    raise ScenarioError("allow_frame_drop must be boolean")
  diagnostics = data.get("diagnostics")
  if diagnostics is not None:
    frames = diagnostics.get("camera_capture_frames") if isinstance(diagnostics, dict) else None
    if not isinstance(frames, list) or not frames or not all(isinstance(frame, int) and frame > 0 for frame in frames):
      raise ScenarioError("diagnostics.camera_capture_frames must be a non-empty positive integer list")
    if frames != sorted(set(frames)):
      raise ScenarioError("diagnostics.camera_capture_frames must be unique and increasing")
  controller = data.get("simulator_control")
  if controller is not None:
    if not isinstance(controller, dict) or controller.get("mode") not in ("reference_lane_assist", "pure_pursuit", "reference_curvature_follow"):
      raise ScenarioError("unsupported simulator control mode")
    keys_by_mode = {
      "reference_lane_assist": ("target_speed_mps", "lateral_gain", "heading_gain", "lookahead_m"),
      "pure_pursuit": ("target_speed_mps", "lookahead_m", "curvature_to_steer_gain"),
      "reference_curvature_follow": ("target_speed_mps", "curvature_to_steer_gain", "lateral_gain", "heading_gain"),
    }
    keys = keys_by_mode[controller["mode"]]
    for key in keys:
      if not isinstance(controller.get(key), (int, float)) or controller[key] <= 0:
        raise ScenarioError(f"simulator_control.{key} must be positive")


def load_scenario(path: Path) -> Scenario:
  with path.open(encoding="utf-8") as handle:
    data = yaml.safe_load(handle)
  if not isinstance(data, dict):
    raise ScenarioError("scenario must be a mapping")
  validate_scenario(data)
  return Scenario(data=data, source=path.resolve())


def scenario_with_delay(scenario: Scenario, delay_ms: int) -> Scenario:
  data = json.loads(json.dumps(scenario.data))
  data["fault"]["target_delay_ms"] = delay_ms
  validate_scenario(data)
  return Scenario(data=data, source=scenario.source)
