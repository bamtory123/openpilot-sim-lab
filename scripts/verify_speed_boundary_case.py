#!/usr/bin/env python3
"""Verify the checked-in public 3.5 m/s boundary case without local raw runs."""

import argparse
import json
import re
from pathlib import Path

from build_speed_boundary_case import FORBIDDEN, render_summary, render_svg


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("output_dir", type=Path)
  args = parser.parse_args()
  evidence_path = args.output_dir / "evidence.json"
  evidence_text = evidence_path.read_text(encoding="utf-8")
  evidence = json.loads(evidence_text)

  if evidence.get("scope") != "simulator_specialist_speed_boundary_negative_case_not_road_performance":
    raise SystemExit("unexpected speed-boundary evidence scope")
  if evidence.get("decision") != "reject_candidate_stop_before_repeat_and_delay_matrix":
    raise SystemExit("unexpected speed-boundary decision")
  if evidence["baseline"].get("performance_eligible") is not False:
    raise SystemExit("incomplete baseline must remain performance-ineligible")
  if (evidence["candidate"].get("validity"), evidence["candidate"].get("outcome")) != ("invalid", "not_evaluated"):
    raise SystemExit("candidate verdict drifted")
  if evidence["candidate"]["observed_lateral_rmse_m"] <= evidence["baseline"]["observed_mean_lateral_rmse_m"]:
    raise SystemExit("retained rejection no longer shows the documented RMSE regression")
  hashes = [evidence["baseline"]["gate_sha256"], evidence["localization"]["analysis_sha256"],
            evidence["training"]["metrics_sha256"], evidence["training"]["artifact_sha256"],
            *evidence["training"]["manifest_sha256"], evidence["candidate"]["summary_sha256"],
            evidence["candidate"]["analysis_sha256"], evidence["candidate"]["attempt_sha256"]]
  if any(re.fullmatch(r"[0-9a-f]{64}", value) is None for value in hashes):
    raise SystemExit("invalid source hash")
  if any(token in evidence_text for token in FORBIDDEN):
    raise SystemExit("public evidence exposes a forbidden local token")
  if (args.output_dir / "SUMMARY.md").read_text(encoding="utf-8") != render_summary(evidence):
    raise SystemExit("summary differs from evidence")
  if (args.output_dir / "comparison.svg").read_text(encoding="utf-8") != render_svg(evidence):
    raise SystemExit("SVG differs from evidence")
  print(json.dumps({"schema_version": 1, "scope": "public_speed_boundary_case_only", "status": "pass"}, sort_keys=True))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
