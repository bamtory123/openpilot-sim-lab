from simlab.model_replay import summarize_replay


def _model(frame_id: int, execution_time: float = 0.02) -> dict:
  return {
    "frame_id": frame_id,
    "frame_age": 0,
    "frame_drop_pct": 0.0,
    "model_execution_time_s": execution_time,
    "path_horizon_m": 120.0,
    "left_lane_probability": 0.8,
    "right_lane_probability": 0.7,
    "desired_curvature_1pm": 0.001,
  }


def test_real_camera_replay_separates_function_and_timing():
  summary = summarize_replay([_model(10, 0.20), _model(11, 0.20)],
                             [{"model_execution_time_s": 0.10}] * 2, expected_frames=2)

  assert summary["functional_status"] == "pass"
  assert summary["timing_status"] == "not_qualified"
  assert summary["classification"] == "functional_pass_timing_not_qualified"
  assert summary["model_frame_coverage"] == 1.0
  assert summary["model"]["path_horizon_m"]["mean"] == 120.0


def test_real_camera_replay_rejects_missing_or_reordered_outputs():
  summary = summarize_replay([_model(11), _model(10)], [{"model_execution_time_s": 0.01}], expected_frames=2)

  assert summary["functional_status"] == "fail"
  assert not summary["frame_ids_strictly_increasing"]


def test_real_camera_replay_can_qualify_bounded_timing():
  summary = summarize_replay([_model(10, 0.02), _model(11, 0.02)],
                             [{"model_execution_time_s": 0.01}] * 2, expected_frames=2)

  assert summary["classification"] == "functional_pass_timing_pass"
