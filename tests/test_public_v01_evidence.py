import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_v01_evidence_preserves_result_boundaries():
  evidence = json.loads((ROOT / "examples/v0.1-portfolio-evidence/evidence.json").read_text(encoding="utf-8"))

  assert evidence["formal_matrix"]["representative_summary"]["outcome"] == "fail"
  assert evidence["baseline_audit"]["status"] == "approved"
  assert evidence["regression_review"]["verdict"] == "hard_gate_fail"
  assert evidence["host_confirmation"]["scope"] == "compatibility_only_not_driving_performance"
  assert all(summary["validity"] == "valid" and summary["outcome"] == "pass"
             for summary in evidence["host_confirmation"]["confirmed_summaries"])
  sources = [evidence["formal_matrix"]["source"], evidence["baseline_audit"]["source"],
             evidence["regression_review"]["source"], *evidence["host_confirmation"]["sources"]]
  assert all(re.fullmatch(r"[0-9a-f]{64}", source["sha256"]) for source in sources)


def test_public_v01_evidence_is_linked_from_portfolio_documents():
  link = "../examples/v0.1-portfolio-evidence/README.md"
  for document in ("docs/portfolio-summary.md", "docs/release-checklist.md", "docs/evaluation-boundary.md"):
    assert link in (ROOT / document).read_text(encoding="utf-8")
