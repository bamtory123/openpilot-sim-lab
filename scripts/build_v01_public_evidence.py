from __future__ import annotations

import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "examples/v0.1-portfolio-evidence/evidence.json"
FORMAL_ROOT = ROOT / "outputs/v0.2-formal-delay-matrix-20260828"
HOST_ROOT = ROOT / "outputs/v0.1-host-confirmation-probe-20260901"


def read(path: Path) -> dict:
  return json.loads(path.read_text(encoding="utf-8"))


def source(path: Path) -> dict:
  return {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


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
  print(OUTPUT)


if __name__ == "__main__":
  main()
