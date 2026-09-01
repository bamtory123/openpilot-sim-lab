import json
from pathlib import Path
from simlab.report import generate_report

ROOT = Path(__file__).resolve().parents[1]


def test_public_example_summaries_have_required_contract_fields():
  paths = sorted(ROOT.glob("examples/*/representative-summary.json"))
  assert paths
  for path in paths:
    assert (path.parent / "README.md").is_file()
    summary = json.loads(path.read_text(encoding="utf-8"))
    assert summary["schema_version"] == 1
    assert summary["validity"] in ("valid", "invalid")
    assert summary["outcome"] in ("pass", "fail", "not_evaluated")
    assert isinstance(summary["target_delay_ms"], int)
    assert isinstance(summary["metrics"]["lateral_rmse_m"], (int, float))
    assert isinstance(summary["metrics"]["camera_frames_published"], int)

def test_report_writes_markdown_and_svg(tmp_path):
  run = tmp_path / "run-1"; run.mkdir()
  (run / "summary.json").write_text(json.dumps({"target_delay_ms": 0, "validity": "valid", "outcome": "pass", "reasons": [], "metrics": {"lateral_rmse_m": 0.12}}))
  invalid = tmp_path / "run-2"; invalid.mkdir()
  (invalid / "summary.json").write_text(json.dumps({"target_delay_ms": 0, "validity": "invalid", "outcome": "not_evaluated", "metrics": {}}))
  report = generate_report(tmp_path, tmp_path / "report.md")
  assert "| 0 | 1 | 0 | 1 | - | - | n/a | 0.12 |" in report.read_text() and report.with_suffix(".svg").is_file()


def test_report_discovers_nested_host_probe_runs(tmp_path):
  run = tmp_path / "host-probe" / "runs" / "run-1"
  run.mkdir(parents=True)
  (run / "summary.json").write_text(json.dumps({"target_delay_ms": 0, "validity": "valid", "outcome": "pass",
                                                   "reasons": [], "metrics": {"lateral_rmse_m": 0.12}}))

  report = generate_report(tmp_path, tmp_path / "report.md")

  assert "| 0 | 1 | 0 | 0 | - | - | n/a | 0.12 |" in report.read_text()


def test_report_surfaces_unrecovered_host_probe_attempts(tmp_path):
  attempt = tmp_path / "host-probe"; attempt.mkdir()
  (attempt / "attempt.json").write_text("{}")

  report = generate_report(tmp_path, tmp_path / "report.md")

  assert "## Incomplete host probe attempts" in report.read_text()
  assert "`host-probe` has no runner summary" in report.read_text()


def test_report_excludes_warmup_results(tmp_path):
  warmup = tmp_path / "warmup" / "run"; warmup.mkdir(parents=True)
  (warmup / "summary.json").write_text(json.dumps({"target_delay_ms": 0, "validity": "valid", "outcome": "pass",
                                                      "reasons": [], "metrics": {"lateral_rmse_m": 9.0}}))
  run = tmp_path / "run"; run.mkdir()
  (run / "summary.json").write_text(json.dumps({"target_delay_ms": 0, "validity": "valid", "outcome": "pass",
                                                   "reasons": [], "metrics": {"lateral_rmse_m": 0.2}}))

  report = generate_report(tmp_path, tmp_path / "report.md")

  assert "| 0 | 1 | 0 | 0 | - | - | n/a | 0.2 |" in report.read_text()


def test_report_groups_valid_failure_reasons(tmp_path):
  run = tmp_path / "run"; run.mkdir()
  (run / "summary.json").write_text(json.dumps({"target_delay_ms": 50, "validity": "valid", "outcome": "fail",
                                                   "reasons": ["lane_departure", "lateral_error_threshold"],
                                                   "metrics": {"lateral_rmse_m": 0.2}}))
  report = generate_report(tmp_path, tmp_path / "report.md")
  assert "lane_departure:1, lateral_error_threshold:1" in report.read_text()


def test_report_groups_invalid_reasons_separately(tmp_path):
  run = tmp_path / "run"; run.mkdir()
  (run / "summary.json").write_text(json.dumps({"target_delay_ms": 0, "validity": "invalid", "outcome": "not_evaluated",
                                                   "reasons": ["host_interrupted"], "metrics": {}}))

  report = generate_report(tmp_path, tmp_path / "report.md")

  assert "| 0 | 0 | 0 | 1 | - | host_interrupted:1 | n/a | n/a |" in report.read_text()


def test_report_summarizes_adjacent_host_manifests(tmp_path):
  run = tmp_path / "run"; run.mkdir()
  (run / "summary.json").write_text(json.dumps({"target_delay_ms": 0, "validity": "valid", "outcome": "pass", "metrics": {"lateral_rmse_m": 0.2}}))
  (run / "manifest.json").write_text(json.dumps({"gpu": "RTX", "driver": "616.56", "wsl_boot_id": "boot-a",
                                                    "gpu_runtime_snapshot": {"temperature_c": "52"}}))

  report = generate_report(tmp_path, tmp_path / "report.md")

  text = report.read_text()
  assert "## Host provenance" in text and "Distinct WSL boot IDs: 1" in text and "52–52 °C" in text


def test_report_summarizes_measurement_coverage(tmp_path):
  run = tmp_path / "run"; run.mkdir()
  (run / "summary.json").write_text(json.dumps({"target_delay_ms": 0, "validity": "valid", "outcome": "pass",
                                                   "metrics": {"lateral_rmse_m": 0.2, "telemetry_coverage_ratio": 1.0,
                                                               "road_camera_coverage_ratio": 0.99}}))

  report = generate_report(tmp_path, tmp_path / "report.md")

  text = report.read_text()
  assert "## Measurement coverage" in text and "| telemetry coverage | 1.000 |" in text and "| road-camera coverage | 0.990 |" in text
