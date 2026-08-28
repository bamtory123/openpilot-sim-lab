import json
from simlab.report import generate_report

def test_report_writes_markdown_and_svg(tmp_path):
  run = tmp_path / "run-1"; run.mkdir()
  (run / "summary.json").write_text(json.dumps({"target_delay_ms": 0, "validity": "valid", "outcome": "pass", "reasons": [], "metrics": {"lateral_rmse_m": 0.12}}))
  invalid = tmp_path / "run-2"; invalid.mkdir()
  (invalid / "summary.json").write_text(json.dumps({"target_delay_ms": 0, "validity": "invalid", "outcome": "not_evaluated", "metrics": {}}))
  report = generate_report(tmp_path, tmp_path / "report.md")
  assert "| 0 | 1 | 0 | 1 | - | 0.12 |" in report.read_text() and report.with_suffix(".svg").is_file()


def test_report_groups_valid_failure_reasons(tmp_path):
  run = tmp_path / "run"; run.mkdir()
  (run / "summary.json").write_text(json.dumps({"target_delay_ms": 50, "validity": "valid", "outcome": "fail",
                                                   "reasons": ["lane_departure", "lateral_error_threshold"],
                                                   "metrics": {"lateral_rmse_m": 0.2}}))
  report = generate_report(tmp_path, tmp_path / "report.md")
  assert "lane_departure:1, lateral_error_threshold:1" in report.read_text()
