import json

from simlab.baseline import audit_historical_baseline


def _write_run(root, run_id, *, delay=0, scenario_hash="same"):
  path = root / "outputs/history" / run_id
  path.mkdir(parents=True)
  (path / "manifest.json").write_text(json.dumps({"run_id": run_id, "scenario_hash": scenario_hash, "openpilot": {"commit": "op", "dirty": False}, "sim_lab": {"commit": "lab", "dirty": False}}))
  (path / "scenario.yaml").write_text("scenario_id: md_default_loop_lane0_v1\nfault:\n  target_delay_ms: 0\n")
  (path / "summary.json").write_text(json.dumps({"run_id": run_id, "scenario_id": "md_default_loop_lane0_v1", "target_delay_ms": delay, "validity": "valid", "outcome": "fail"}))
  for name in ("telemetry.csv", "camera.csv", "events.jsonl"):
    (path / name).write_text("data\n")


def _contract(path):
  path.write_text("""baseline_id: test\nbaseline_evidence:\n  historical_artifact_root: outputs/history\n  formal_run_ids: [one, two]\n  expected:\n    scenario_id: md_default_loop_lane0_v1\n    target_delay_ms: 0\n    validity: valid\n    outcome: fail\n""")


def test_historical_baseline_audit_approves_complete_matching_runs(tmp_path):
  _write_run(tmp_path, "one")
  _write_run(tmp_path, "two")
  contract = tmp_path / "contract.yaml"
  _contract(contract)

  result = audit_historical_baseline(contract, tmp_path)

  assert result["status"] == "approved" and result["findings"] == []
  assert result["runs"][0]["artifacts"]["telemetry.csv"]["sha256"]


def test_historical_baseline_audit_reports_an_evidence_gap(tmp_path):
  _write_run(tmp_path, "one")
  _write_run(tmp_path, "two", delay=50)
  (tmp_path / "outputs/history/one/events.jsonl").unlink()
  contract = tmp_path / "contract.yaml"
  _contract(contract)

  result = audit_historical_baseline(contract, tmp_path)

  assert result["status"] == "evidence_gap"
  assert "one:missing_or_empty:events.jsonl" in result["findings"]
  assert "two:check_failed:target_delay_ms" in result["findings"]
