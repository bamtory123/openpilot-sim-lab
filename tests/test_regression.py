import json

import pytest

from simlab.regression import review_regression


def _summary(root, run_id, *, invalid=False, collision=False, rmse=1.0):
  path = root / run_id
  path.mkdir(parents=True)
  path.joinpath("summary.json").write_text(json.dumps({"run_id": run_id, "scenario_id": "scenario", "target_delay_ms": 0,
    "validity": "invalid" if invalid else "valid", "reasons": ["collision"] if collision else [],
    "metrics": {"lateral_rmse_m": rmse, "lateral_abs_p95_m": 2.0, "applied_steering_rate_rms_deg_s": 3.0,
                "speed_mean_mps": 4.0, "actual_delay_median_ms": 5.0}}))
  path.joinpath("manifest.json").write_text(json.dumps({"scenario_hash": "same"}))


def test_regression_review_reports_relative_metrics(tmp_path):
  _summary(tmp_path / "base", "one", rmse=1.0)
  _summary(tmp_path / "candidate", "one", rmse=1.2)

  result = review_regression(tmp_path / "base", tmp_path / "candidate", scenario_id="scenario", delay_ms=0)

  assert result["verdict"] == "review_required"
  assert result["metric_deltas_scope"] == "evaluated"
  assert result["metric_deltas"]["lateral_rmse_m"]["delta"] == pytest.approx(0.2)


def test_regression_review_hard_fails_invalid_or_new_collision(tmp_path):
  _summary(tmp_path / "base", "one")
  _summary(tmp_path / "candidate", "one", invalid=True, collision=True)

  result = review_regression(tmp_path / "base", tmp_path / "candidate", scenario_id="scenario", delay_ms=0)

  assert result["verdict"] == "hard_gate_fail"
  assert result["metric_deltas_scope"] == "diagnostic_only"
  assert len(result["phase_1_hard_gate_failures"]) == 2


def test_regression_review_marks_identical_evidence_as_no_change(tmp_path):
  _summary(tmp_path / "base", "one")
  _summary(tmp_path / "candidate", "one")

  result = review_regression(tmp_path / "base", tmp_path / "candidate", scenario_id="scenario", delay_ms=0)

  assert result["verdict"] == "no_change" and result["phase_2_review_required"] is False


def test_regression_review_rejects_a_scenario_hash_mismatch(tmp_path):
  _summary(tmp_path / "base", "one")
  _summary(tmp_path / "candidate", "one")
  (tmp_path / "candidate/one/manifest.json").write_text('{"scenario_hash":"other"}')

  result = review_regression(tmp_path / "base", tmp_path / "candidate", scenario_id="scenario", delay_ms=0)

  assert result["verdict"] == "hard_gate_fail"
  assert "candidate:scenario_hash_mismatch" in result["phase_1_hard_gate_failures"]
