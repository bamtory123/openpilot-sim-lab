from unittest.mock import Mock, patch
from pathlib import Path

from simlab.config import load_scenario
from simlab.runner import RunData, _classify, _stop_process_group


def test_stops_the_manager_process_group():
  process = Mock()
  process.pid = 4242
  process.poll.return_value = None
  with patch("simlab.runner.os.killpg") as killpg:
    _stop_process_group(process)
  killpg.assert_called_once_with(4242, __import__("signal").SIGTERM)
  process.wait.assert_called_once_with(timeout=10)


def test_lane_departure_is_a_valid_failure_before_full_coverage():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(
    measured=True,
    telemetry=[{"measurement": True, "lane_departure": True}],
    termination={"out_of_lane": True},
  )

  validity, outcome, reasons = _classify(data, scenario, "simulator_termination")

  assert (validity, outcome, reasons) == ("valid", "fail", ["lane_departure"])


def test_timestamp_error_is_invalid_without_a_measured_failure():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(measured=True, camera=[{"camera": "road", "source_frame_id": 0, "capture_mono_ns": 2,
                                           "scheduled_publish_mono_ns": 1, "actual_publish_mono_ns": 2}])

  validity, outcome, reasons = _classify(data, scenario, None)

  assert (validity, outcome, reasons) == ("invalid", "not_evaluated", ["telemetry_coverage", "camera_timestamp"])


def test_lateral_kpi_threshold_is_a_valid_failure():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(measured=True, telemetry=[{"measurement": True, "lateral_error_m": 1.26}])

  validity, outcome, reasons = _classify(data, scenario, None)

  assert (validity, outcome, reasons) == ("valid", "fail", ["lateral_error_threshold"])


def test_disengagement_after_measurement_starts_is_a_valid_failure():
  scenario = load_scenario(Path("configs/scenarios/md_default_loop_lane0_v1.yaml"))
  data = RunData(measured=True, events=[{"type": "run_state", "state": "MEASURE"},
                                        {"type": "openpilot_state", "engaged": False}])

  validity, outcome, reasons = _classify(data, scenario, None)

  assert (validity, outcome, reasons) == ("valid", "fail", ["disengagement"])
