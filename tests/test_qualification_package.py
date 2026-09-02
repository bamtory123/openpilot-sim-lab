from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_qualification_package_preserves_current_verdict_and_boundaries():
  report = (ROOT / "docs/qualification-report.md").read_text(encoding="utf-8")
  checklist = (ROOT / "docs/release-checklist.md").read_text(encoding="utf-8")
  test_plan = (ROOT / "docs/test-plan.md").read_text(encoding="utf-8")
  snapshot = (ROOT / "docs/portfolio-snapshot.md").read_text(encoding="utf-8")

  assert "`not_qualified_yet`" in report
  assert "# v0.1 qualification report\n" in report
  assert "(draft)" not in report
  assert "valid/fail" in report
  assert "limitations](limitations.md)" in report
  assert "Phase 1 hard-gate failed" in report
  assert "`not_qualified_yet`" in checklist
  assert "| Requirements-to-artifact release trace | complete |" in checklist
  assert "qualification draft in progress" not in test_plan
  assert "`not_qualified_yet`" in snapshot
  assert "not a new GitHub release, tag" in snapshot
  assert "../examples/v0.1-portfolio-evidence/README.md" in snapshot
  assert "../examples/v0.1-portfolio-evidence/SUMMARY.md" in snapshot
  assert "verify_portfolio_snapshot.sh" in snapshot


def test_portfolio_snapshot_verifier_enforces_non_release_boundary():
  verifier = (ROOT / "scripts/verify_portfolio_snapshot.sh").read_text(encoding="utf-8")

  assert "git status --porcelain" in verifier
  assert "git tag --contains HEAD" in verifier
  assert "verify_portfolio_readiness.py" in verifier
  assert "--verify-local-v01" in verifier


def test_portfolio_readiness_check_keeps_public_boundaries():
  result = __import__("subprocess").run([__import__("sys").executable, str(ROOT / "scripts/verify_portfolio_readiness.py")],
                                         check=True, capture_output=True, text=True)
  readiness = __import__("json").loads(result.stdout)
  assert readiness == {"checks": {"public_carla": "pass", "public_v01": "pass"},
                       "schema_version": 1, "scope": "portfolio_readiness_only", "status": "pass"}


def test_windows_collector_covers_wsl_vmswitch_operational_log():
  collector = (ROOT / "scripts/collect_windows_wsl_events.ps1").read_text(encoding="utf-8")
  host_stability = (ROOT / "docs/host-stability.md").read_text(encoding="utf-8")

  assert "Microsoft-Windows-Hyper-V-VmSwitch-Operational" in collector
  assert "OID_GEN_STATISTICS" in collector
  assert "Windows `System` and Hyper-V `VmSwitch Operational`" in host_stability
