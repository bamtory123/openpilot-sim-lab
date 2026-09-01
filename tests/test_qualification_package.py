from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_qualification_package_preserves_current_verdict_and_boundaries():
  report = (ROOT / "docs/qualification-report.md").read_text(encoding="utf-8")
  checklist = (ROOT / "docs/release-checklist.md").read_text(encoding="utf-8")
  test_plan = (ROOT / "docs/test-plan.md").read_text(encoding="utf-8")

  assert "`not_qualified_yet`" in report
  assert "valid/fail" in report
  assert "limitations](limitations.md)" in report
  assert "Phase 1 hard-gate failed" in report
  assert "`not_qualified_yet`" in checklist
  assert "| Requirements-to-artifact release trace | complete |" in checklist
  assert "qualification draft in progress" not in test_plan


def test_windows_collector_covers_wsl_vmswitch_operational_log():
  collector = (ROOT / "scripts/collect_windows_wsl_events.ps1").read_text(encoding="utf-8")

  assert "Microsoft-Windows-Hyper-V-VmSwitch-Operational" in collector
