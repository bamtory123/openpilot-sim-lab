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
  if env.get("map_id") not in ("openpilot_default_loop_v1", "openpilot_serpentine_v1"):
    raise ScenarioError("unsupported map_id")
  if not isinstance(env.get("seed"), int) or env.get("reference_lane_index") not in (0, 1):
    raise ScenarioError("seed and reference_lane_index must be concrete")
  if env.get("map_curve_direction", 0) not in (0, 1):
    raise ScenarioError("map_curve_direction must be 0 or 1")
  if not isinstance(env.get("map_track_size_m", 60), int) or env.get("map_track_size_m", 60) < 30:
    raise ScenarioError("map_track_size_m must be an integer of at least 30")
  if "camera_fov_deg" in env and env["camera_fov_deg"] not in (40, 60):
    raise ScenarioError("camera_fov_deg must be an approved diagnostic value")
  if "camera_gamma" in env and (not isinstance(env["camera_gamma"], (int, float)) or not 0.8 <= float(env["camera_gamma"]) <= 1.2):
    raise ScenarioError("camera_gamma must be between 0.8 and 1.2")
  if "traffic_density" in env and (not isinstance(env["traffic_density"], (int, float)) or not 0.0 <= float(env["traffic_density"]) <= 0.05):
    raise ScenarioError("traffic_density must be between 0.0 and 0.05")
  if "traffic_mode" in env and env["traffic_mode"] not in ("trigger", "respawn"):
    raise ScenarioError("traffic_mode must be trigger or respawn")
  lead_vehicle = env.get("lead_vehicle")
  if lead_vehicle is not None:
    if not isinstance(lead_vehicle, dict) or set(lead_vehicle) - {"gap_m", "visual_proxy", "render_vehicle"} or not isinstance(lead_vehicle.get("gap_m"), (int, float)) or not 5.0 <= float(lead_vehicle["gap_m"]) <= 40.0:
      raise ScenarioError("lead_vehicle must contain gap_m between 5 and 40")
    if "visual_proxy" in lead_vehicle and lead_vehicle["visual_proxy"] != "box":
      raise ScenarioError("lead_vehicle.visual_proxy must be box")
    if "render_vehicle" in lead_vehicle and not isinstance(lead_vehicle["render_vehicle"], bool):
      raise ScenarioError("lead_vehicle.render_vehicle must be boolean")
  if "show_navi_mark" in env and not isinstance(env["show_navi_mark"], bool):
    raise ScenarioError("show_navi_mark must be boolean")
  for key in ("camera_position_m", "camera_hpr_deg"):
    if key in env and (not isinstance(env[key], list) or len(env[key]) != 3 or not all(isinstance(value, (int, float)) for value in env[key])):
      raise ScenarioError(f"{key} must be a three-value numeric vector")
  if fault.get("type") != "camera_transport_delay" or fault.get("target_delay_ms") not in (0, 50, 100, 150):
    raise ScenarioError("v0.1 supports a 0/50/100/150 ms camera_transport_delay only")
  if fault.get("queue_capacity_frames", 0) < 1 or fault.get("overflow_policy") != "invalid_run":
    raise ScenarioError("queue must be bounded and overflow must invalidate the run")
  if run.get("measurement_camera_frames", 0) < 1 or run.get("wall_watchdog_s", 0) < 1:
    raise ScenarioError("measurement and watchdog must be positive")
  if not isinstance(validity.get("min_telemetry_coverage_ratio"), (int, float)) or not 0 < float(validity["min_telemetry_coverage_ratio"]) <= 1:
    raise ScenarioError("min_telemetry_coverage_ratio must be in (0, 1]")
  if not isinstance(validity.get("min_active_time_s"), (int, float)) or validity["min_active_time_s"] <= 0:
    raise ScenarioError("min_active_time_s must be positive")
  if logging.get("telemetry_hz") != 100 or logging.get("camera_hz_nominal") != 20:
    raise ScenarioError("v0.1 rate contract is 100 Hz telemetry / 20 Hz camera")
  if not isinstance(validity.get("allow_frame_drop"), bool):
    raise ScenarioError("allow_frame_drop must be boolean")
  actuation = data.get("actuation")
  if actuation is not None:
    if not isinstance(actuation, dict) or set(actuation) != {"steer_ratio"} or not isinstance(actuation.get("steer_ratio"), (int, float)):
      raise ScenarioError("actuation must contain only numeric steer_ratio")
    if float(actuation["steer_ratio"]) not in (1.0, 2.0, 4.0, 8.0):
      raise ScenarioError("actuation.steer_ratio must be one of 1, 2, 4, 8")
  if "min_traffic_vehicle_count" in validity and (not isinstance(validity["min_traffic_vehicle_count"], int) or validity["min_traffic_vehicle_count"] < 0):
    raise ScenarioError("min_traffic_vehicle_count must be a non-negative integer")
  if "max_traffic_ego_nearest_distance_m" in validity and (not isinstance(validity["max_traffic_ego_nearest_distance_m"], (int, float)) or validity["max_traffic_ego_nearest_distance_m"] <= 0):
    raise ScenarioError("max_traffic_ego_nearest_distance_m must be positive")
  diagnostics = data.get("diagnostics")
  if diagnostics is not None:
    frames = diagnostics.get("camera_capture_frames") if isinstance(diagnostics, dict) else None
    if not isinstance(frames, list) or not frames or not all(isinstance(frame, int) and frame > 0 for frame in frames):
      raise ScenarioError("diagnostics.camera_capture_frames must be a non-empty positive integer list")
    if frames != sorted(set(frames)):
      raise ScenarioError("diagnostics.camera_capture_frames must be unique and increasing")
    if "dataset_collection" in diagnostics and diagnostics["dataset_collection"] is not True:
      raise ScenarioError("diagnostics.dataset_collection must be true when specified")
    if "require_visible_lead" in diagnostics and not isinstance(diagnostics["require_visible_lead"], bool):
      raise ScenarioError("diagnostics.require_visible_lead must be boolean")
  dataset = data.get("dataset")
  if dataset is not None:
    seeds = dataset.get("seeds") if isinstance(dataset, dict) else None
    if not isinstance(seeds, list) or not seeds or not all(isinstance(seed, int) for seed in seeds) or len(set(seeds)) != len(seeds):
      raise ScenarioError("dataset.seeds must be a non-empty unique integer list")
    validation_seeds = dataset.get("validation_seeds", [])
    if not isinstance(validation_seeds, list) or not all(isinstance(seed, int) for seed in validation_seeds) or not set(validation_seeds) < set(seeds):
      raise ScenarioError("dataset.validation_seeds must be a strict subset of dataset.seeds")
    directions = dataset.get("map_curve_directions", [env.get("map_curve_direction", 0)])
    if not isinstance(directions, list) or not directions or set(directions) - {0, 1}:
      raise ScenarioError("dataset.map_curve_directions must contain only 0 and/or 1")
  specialist_dataset = data.get("specialist_dataset")
  if specialist_dataset is not None:
    teacher = specialist_dataset.get("teacher") if isinstance(specialist_dataset, dict) else None
    if not isinstance(teacher, dict):
      raise ScenarioError("specialist_dataset.teacher must be a mapping")
    for key in ("lookahead_m", "curvature_to_steer_gain"):
      if not isinstance(teacher.get(key), (int, float)) or teacher[key] <= 0:
        raise ScenarioError(f"specialist_dataset.teacher.{key} must be positive")
  specialist_replay = data.get("specialist_replay")
  if specialist_replay is not None:
    if not isinstance(specialist_replay, dict) or not isinstance(specialist_replay.get("artifact_path"), str) or not specialist_replay["artifact_path"]:
      raise ScenarioError("specialist_replay.artifact_path must be a non-empty string")
    if not isinstance(specialist_replay.get("target_speed_mps"), (int, float)) or specialist_replay["target_speed_mps"] <= 0:
      raise ScenarioError("specialist_replay.target_speed_mps must be positive")
    if actuation is not None:
      raise ScenarioError("actuation is not permitted with specialist_replay")
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
    if actuation is not None:
      raise ScenarioError("actuation is not permitted with simulator_control")


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


def scenario_with_seed(scenario: Scenario, seed: int) -> Scenario:
  data = json.loads(json.dumps(scenario.data))
  data["environment"]["seed"] = seed
  validate_scenario(data)
  return Scenario(data=data, source=scenario.source)


def scenario_with_map_curve_direction(scenario: Scenario, direction: int) -> Scenario:
  data = json.loads(json.dumps(scenario.data))
  data["environment"]["map_curve_direction"] = direction
  validate_scenario(data)
  return Scenario(data=data, source=scenario.source)


def scenario_with_actuation_ratio(scenario: Scenario, steer_ratio: float) -> Scenario:
  data = json.loads(json.dumps(scenario.data))
  data["actuation"] = {"steer_ratio": steer_ratio}
  validate_scenario(data)
  return Scenario(data=data, source=scenario.source)
