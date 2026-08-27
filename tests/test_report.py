import json
from simlab.report import generate_report

def test_report_writes_markdown_and_svg(tmp_path):
  run = tmp_path / "run-1"; run.mkdir()
  (run / "summary.json").write_text(json.dumps({"target_delay_ms": 0, "validity": "valid", "outcome": "pass", "metrics": {"lateral_rmse_m": 0.12}}))
  report = generate_report(tmp_path, tmp_path / "report.md")
  assert "MetaDrive Repeatability Study" in report.read_text() and report.with_suffix(".svg").is_file()
