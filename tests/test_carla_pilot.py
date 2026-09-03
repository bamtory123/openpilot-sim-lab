from simlab.carla_pilot import classify_pilot


def test_pilot_invalid_without_measurement():
  verdict = classify_pilot(lifecycle=["WAIT_SIM_READY"], telemetry=[], camera=[], termination=None, expected_camera_frames=1200)
  assert verdict.status == "invalid"


def test_pilot_reports_integrated_but_unstable():
  lifecycle = ["WAIT_SIM_READY", "WAIT_OPENPILOT_READY", "MEASURE"]
  verdict = classify_pilot(lifecycle=lifecycle, telemetry=[{"measurement": True, "engaged": True}],
                           camera=[{}] * 1140, termination={"collision": True}, expected_camera_frames=1200)
  assert verdict.status == "integrated-but-not-stable"
  assert verdict.reasons == ("collision",)


def test_safety_termination_is_not_hidden_by_short_coverage():
  lifecycle = ["WAIT_SIM_READY", "WAIT_OPENPILOT_READY", "MEASURE"]
  verdict = classify_pilot(lifecycle=lifecycle, telemetry=[{"measurement": True, "engaged": True}],
                           camera=[{}] * 2, termination={"lane_departure": True}, expected_camera_frames=1200)
  assert verdict.status == "integrated-but-not-stable"


def test_pilot_reports_bounded_pass():
  lifecycle = ["WAIT_SIM_READY", "WAIT_OPENPILOT_READY", "MEASURE"]
  verdict = classify_pilot(lifecycle=lifecycle, telemetry=[{"measurement": True, "engaged": True}],
                           camera=[{}] * 1140, termination={"timeout": True}, expected_camera_frames=1200)
  assert verdict.status == "bounded-pass"
