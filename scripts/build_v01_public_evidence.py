from __future__ import annotations

import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "examples/v0.1-portfolio-evidence/evidence.json"
SUMMARY = ROOT / "examples/v0.1-portfolio-evidence/SUMMARY.md"
FORMAL_ROOT = ROOT / "outputs/v0.2-formal-delay-matrix-20260828"
HOST_ROOT = ROOT / "outputs/v0.1-host-confirmation-probe-20260901"


def read(path: Path) -> dict:
  return json.loads(path.read_text(encoding="utf-8"))


def source(path: Path) -> dict:
  return {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def render_summary(evidence: dict) -> str:
  formal = evidence["formal_matrix"]
  host = evidence["host_confirmation"]
  delays = " | ".join(f"{delay} ms: {rmse:.6f} m" for delay, rmse in formal["aggregate"].items())
  return "\n".join([
    "# v0.1 public evidence summary",
    "",
    "## Qualification boundary",
    "",
    "The final v0.1 pretrained-driving disposition is `not_qualified_yet`. This bundle demonstrates validation-framework evidence, not successful pretrained OpenPilot driving.",
    "",
    "## Selected evidence",
    "",
    f"- **Formal model-driven matrix:** representative `{formal['representative_summary']['validity']}/{formal['representative_summary']['outcome']}` with `{', '.join(formal['representative_summary']['reasons'])}`. All retained formal results are lane-departure failures; delay-group median lateral RMSE: {delays}.",
    f"- **Baseline audit:** `{evidence['baseline_audit']['status']}` `{evidence['baseline_audit']['baseline_id']}` with {len(evidence['baseline_audit']['run_ids'])} retained runs.",
    f"- **Current candidate review:** Phase 1 `{evidence['regression_review']['verdict']}`. KPI deltas are `{evidence['regression_review']['scope']}`.",
    f"- **Host confirmation:** {len(host['confirmed_summaries'])} `valid/pass` 200-frame compatibility probes. Scope: `{host['scope']}`.",
    "",
    "## Evidence integrity",
    "",
    "`evidence.json` records the full local source paths and SHA-256 digests. This public bundle excludes raw telemetry, camera data, frames, and process logs. Regenerate with `uv run python scripts/build_v01_public_evidence.py` and verify retained local sources with `uv run python scripts/verify_v01_public_evidence.py`.",
    "",
  ])


def main() -> None:
  audit_path = ROOT / "baselines/md_default_loop_lane0_v1/historical-audit.json"
  regression_path = ROOT / "outputs/v0.1-current-host-confirmation-20260901/regression-review.json"
  audit, regression = read(audit_path), read(regression_path)
  formal_path = FORMAL_ROOT / f"{audit['runs'][0]['run_id']}/summary.json"
  formal = read(formal_path)
  host_ids = ["md_default_loop_lane0_host_confirmation_v1-20260901T142447Z-257091f7",
              "md_default_loop_lane0_host_confirmation_v1-20260901T142600Z-e5d6bd08"]
  host_paths = [next(HOST_ROOT.rglob(f"{run_id}/summary.json")) for run_id in host_ids]
  host = [read(path) for path in host_paths]
  evidence = {
    "schema_version": 1,
    "scope": "public_small_evidence_bundle",
    "excludes": ["telemetry.csv", "camera.csv", "raw_frames", "process_logs"],
    "formal_matrix": {"source": source(formal_path), "representative_summary": formal,
                      "aggregate": {"0": 0.663898, "50": 0.665897, "100": 0.663629, "150": 0.675149}},
    "baseline_audit": {"source": source(audit_path), "status": audit["status"],
                       "baseline_id": audit["baseline_id"], "scenario_hash": audit["provenance"]["scenario_hash"],
                       "run_ids": [run["run_id"] for run in audit["runs"]]},
    "regression_review": {"source": source(regression_path),
                          "verdict": regression["verdict"], "phase_1_hard_gate_failures": regression["phase_1_hard_gate_failures"],
                          "metric_deltas": regression["metric_deltas"], "scope": "diagnostic_only_after_phase_1_failure"},
    "host_confirmation": {"sources": [source(path) for path in host_paths], "scope": "compatibility_only_not_driving_performance",
                          "confirmed_summaries": host},
  }
  OUTPUT.parent.mkdir(parents=True, exist_ok=True)
  OUTPUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  SUMMARY.write_text(render_summary(evidence), encoding="utf-8")
  print(OUTPUT)
  print(SUMMARY)


if __name__ == "__main__":
  main()
