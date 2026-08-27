import math
from simlab.metrics import calculate_metrics


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
