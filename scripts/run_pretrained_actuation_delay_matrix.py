#!/usr/bin/env python3
"""Run v0.2 fault matrices only after the candidate passes both evaluation gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from simlab.config import load_scenario, scenario_with_actuation_ratio
from simlab.manifest import write_json
from simlab.runner import run_batch


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--evaluation", type=Path, required=True)
  parser.add_argument("--fixed-scenario", type=Path, required=True)
  parser.add_argument("--heldout-scenario", type=Path, required=True)
  parser.add_argument("--output-root", type=Path, required=True)
  parser.add_argument("--allow-dirty", action="store_true")
  args = parser.parse_args()
  evaluation = json.loads(args.evaluation.read_text(encoding="utf-8"))
  if evaluation.get("candidate_success") is not True:
    raise RuntimeError("candidate did not pass the fixed and held-out six-run gate")
  ratio = evaluation.get("selection", {}).get("steer_ratio")
  if not isinstance(ratio, (int, float)):
    raise RuntimeError("evaluation does not identify a candidate steer ratio")
  fixed = run_batch(scenario_with_actuation_ratio(load_scenario(args.fixed_scenario), float(ratio)),
                    output_root=args.output_root / "fixed", allow_dirty=args.allow_dirty)
  heldout = run_batch(scenario_with_actuation_ratio(load_scenario(args.heldout_scenario), float(ratio)),
                      output_root=args.output_root / "heldout", allow_dirty=args.allow_dirty)
  result = {"schema_version": 1, "scope": "pretrained_actuation_fault_robustness_not_road_performance",
            "steer_ratio": ratio, "fixed_runs": [str(path / "summary.json") for path in fixed],
            "heldout_runs": [str(path / "summary.json") for path in heldout]}
  write_json(args.output_root / "delay-matrix.json", result)
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()
