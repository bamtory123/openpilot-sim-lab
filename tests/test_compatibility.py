from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simlab.runner import _compatibility_check


def test_compatibility_accepts_configured_openpilot_ancestors(tmp_path):
  completed = Mock(return_value=Mock(returncode=0))
  with patch("simlab.runner.subprocess.run", completed):
    _compatibility_check(tmp_path)
  assert completed.call_count == 2


def test_compatibility_rejects_missing_openpilot_ancestor(tmp_path):
  with patch("simlab.runner.subprocess.run", return_value=Mock(returncode=1)):
    with pytest.raises(RuntimeError, match="not compatible"):
      _compatibility_check(tmp_path)
