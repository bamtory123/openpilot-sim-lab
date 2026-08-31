import math
from simlab.metrics import calculate_metrics, camera_timestamps_valid


def test_hand_calculated_lateral_rmse_and_delay():
  telemetry = [
    {"mono_ns": 0, "lateral_error_m": 0.0, "heading_error_rad": 0.0, "speed_mps": 5.0, "applied_steering_angle_deg": 0.0},
    {"mono_ns": 100_000_000, "lateral_error_m": 0.1, "heading_error_rad": 0.1, "speed_mps": 5.0, "applied_steering_angle_deg": 1.0},
    {"mono_ns": 200_000_000, "lateral_error_m": -0.1, "heading_error_rad": -0.1, "speed_mps": 5.0, "applied_steering_angle_deg": 2.0},
    {"mono_ns": 300_000_000, "lateral_error_m": 0.2, "heading_error_rad": 0.2, "speed_mps": 5.0, "applied_steering_angle_deg": 3.0},
  ]
  result = calculate_metrics(telemetry, [{"actual_delay_ms": 50.0, "dropped": False}, {"actual_delay_ms": 52.0, "dropped": False}])
  assert math.isclose(result["lateral_rmse_m"], math.sqrt(0.015), rel_tol=1e-9)
  assert result["applied_steering_rate_rms_deg_s"] == 10.0 and result["actual_delay_median_ms"] == 51.0


def test_camera_timestamp_validation_checks_order_and_causality():
  valid = [
    {"camera": "road", "source_frame_id": 0, "capture_mono_ns": 10, "scheduled_publish_mono_ns": 20, "actual_publish_mono_ns": 21},
    {"camera": "road", "source_frame_id": 1, "capture_mono_ns": 30, "scheduled_publish_mono_ns": 40, "actual_publish_mono_ns": 42},
  ]
  assert camera_timestamps_valid(valid)
  assert not camera_timestamps_valid([{**valid[0], "actual_publish_mono_ns": 9}])
  assert not camera_timestamps_valid([valid[1], valid[0]])


def test_model_inference_health_metrics():
  telemetry = [
    {"model_valid": True, "model_frame_age": 0, "model_frame_drop_perc": 0.0,
     "model_execution_time_s": 0.01, "model_path_end_x_m": 4.0, "model_path_end_speed_mps": 2.0},
    {"model_valid": True, "model_frame_age": 1, "model_frame_drop_perc": 2.0,
     "model_execution_time_s": 0.03, "model_path_end_x_m": 6.0, "model_path_end_speed_mps": 4.0},
  ]

  result = calculate_metrics(telemetry, [])

  assert result["model_valid_coverage_ratio"] == 1.0
  assert result["model_frame_age_max"] == 1.0 and result["model_frame_drop_perc_max"] == 2.0
  assert math.isclose(result["model_execution_time_p95_s"], 0.029)
  assert result["model_path_horizon_median_m"] == 5.0


def test_traffic_vehicle_count_metrics():
  result = calculate_metrics([
    {"traffic_vehicle_count": 2, "traffic_active_vehicle_count": 1, "traffic_nearest_distance_m": 8.0, "traffic_nearest_closing_speed_mps": 1.0, "traffic_nearest_ttc_s": 8.0},
    {"traffic_vehicle_count": 4, "traffic_active_vehicle_count": 3, "traffic_nearest_distance_m": 4.0, "traffic_nearest_closing_speed_mps": 2.0, "traffic_nearest_ttc_s": 2.0},
  ], [])

  assert result["traffic_vehicle_count_mean"] == 3.0
  assert result["traffic_vehicle_count_max"] == 4.0
  assert result["traffic_active_vehicle_count_mean"] == 2.0
  assert result["traffic_ego_nearest_distance_min_m"] == 4.0
  assert result["traffic_ego_nearest_distance_p05_m"] == 4.2
  assert result["traffic_nearest_closing_speed_max_mps"] == 2.0
  assert result["traffic_nearest_ttc_min_s"] == 2.0


def test_active_time_uses_simulation_timestamps():
  result = calculate_metrics([{"simulation_time_s": 10.0}, {"simulation_time_s": 14.25}], [])

  assert result["active_time_s"] == 4.25
