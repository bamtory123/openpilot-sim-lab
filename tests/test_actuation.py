import json
from pathlib import Path

from simlab.actuation import select_actuation_candidate
from simlab.config import load_scenario, scenario_with_actuation_ratio


ROOT = Path(__file__).resolve().parents[1]


def _candidate(root: Path, name: str, ratio: float, rmse: float, *, validity="valid", reasons=None) -> Path:
  run = root / name
  run.mkdir()
  (run / "manifest.json").write_text(json.dumps({"actuation": {"steer_ratio": ratio}}))
  summary = run / "summary.json"
  summary.write_text(json.dumps({"run_id": name, "validity": validity, "outcome": "fail", "reasons": reasons or [],
                                 "metrics": {"lateral_rmse_m": rmse}}))
  return summary


def test_actuation_selection_uses_lowest_rmse_then_higher_ratio(tmp_path):
  paths = [_candidate(tmp_path, "ratio8", 8, 0.5), _candidate(tmp_path, "ratio4", 4, 0.4),
           _candidate(tmp_path, "ratio2", 2, 0.4), _candidate(tmp_path, "collision", 1, 0.1, reasons=["collision"])]

  result = select_actuation_candidate(paths)

  assert result["status"] == "selected"
  assert result["selected_run_id"] == "ratio4"
  assert result["selected_steer_ratio"] == 4
  assert result["changed_candidate_selected"] is True


def test_actuation_selection_retains_invalid_candidates_without_selecting_them(tmp_path):
  result = select_actuation_candidate([_candidate(tmp_path, "invalid", 8, 0.1, validity="invalid")])

  assert result["status"] == "no_eligible_candidate"
  assert result["candidates"][0]["eligible"] is False
  assert result["changed_candidate_selected"] is False


def test_actuation_scenarios_keep_openpilot_control_and_support_ratio_variants():
  scenario = load_scenario(ROOT / "configs/scenarios/md_default_loop_lane0_pretrained_actuation_tuning_v2.yaml")

  assert scenario.data["actuation"]["steer_ratio"] == 8
  assert scenario.data.get("simulator_control") is None and scenario.data.get("specialist_replay") is None
  assert scenario_with_actuation_ratio(scenario, 2).data["actuation"]["steer_ratio"] == 2
