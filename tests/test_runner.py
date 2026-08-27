from unittest.mock import Mock, patch

from simlab.runner import _stop_process_group


def test_stops_the_manager_process_group():
  process = Mock()
  process.pid = 4242
  process.poll.return_value = None
  with patch("simlab.runner.os.killpg") as killpg:
    _stop_process_group(process)
  killpg.assert_called_once_with(4242, __import__("signal").SIGTERM)
  process.wait.assert_called_once_with(timeout=10)
