#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json

from build_performance_case_study import FORBIDDEN, build, parser, render_summary, render_svg


def main() -> None:
  args = parser().parse_args()
  expected = build(args)
  evidence_path = args.output_dir / "evidence.json"
  evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
  if evidence != expected:
    raise SystemExit("case-study evidence differs from retained sources")
  if (args.output_dir / "SUMMARY.md").read_text(encoding="utf-8") != render_summary(evidence):
    raise SystemExit("case-study summary differs from evidence")
  if (args.output_dir / "comparison.svg").read_text(encoding="utf-8") != render_svg(evidence):
    raise SystemExit("case-study SVG differs from evidence")
  if any(token in evidence_path.read_text(encoding="utf-8") for token in FORBIDDEN):
    raise SystemExit("case-study evidence exposes a local token")
  print(json.dumps({"schema_version": 1, "scope": "public_performance_case_study_only", "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
  main()
