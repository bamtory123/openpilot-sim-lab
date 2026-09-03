#!/usr/bin/env python3
"""Run the bounded v0.2 pretrained actuator-calibration evaluation gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from simlab.config import load_scenario, scenario_with_actuation_ratio
from simlab.manifest import write_json
from simlab.runner import run_once


def passed(summary_path: Path) -> bool:
  summary = json.loads(summary_path.read_text(encoding="utf-8"))
  return summary.get("validity") == "valid" and summary.get("outcome") == "pass"


def run_repetitions(scenario, ratio: float, repetitions: int, output_root: Path, allow_dirty: bool) -> list[Path]:
  return [run_once(scenario_with_actuation_ratio(scenario, ratio), output_root=output_root, allow_dirty=allow_dirty)
          for _ in range(repetitions)]


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--selection", type=Path, required=True)
  parser.add_argument("--fixed-scenario", type=Path, required=True)
  parser.add_argument("--heldout-scenario", type=Path, required=True)
  parser.add_argument("--output-root", type=Path, required=True)
  parser.add_argument("--allow-dirty", action="store_true")
  args = parser.parse_args()

  selection = json.loads(args.selection.read_text(encoding="utf-8"))
  candidate_ratio = selection.get("selected_steer_ratio")
  if selection.get("status") != "selected" or not isinstance(candidate_ratio, (int, float)):
    raise RuntimeError("actuation tuning did not select an eligible candidate")
  if float(candidate_ratio) == 8.0:
    result = {"schema_version": 1, "scope": "pretrained_actuation_calibration_evaluation_not_road_performance",
              "selection": {"path": str(args.selection), "steer_ratio": candidate_ratio}, "runs": {},
              "candidate_success": False, "next_step": "retain_negative_result_no_changed_candidate",
              "reason": "baseline_ratio_selected_no_actuation_change"}
    args.output_root.mkdir(parents=True, exist_ok=True)
    write_json(args.output_root / "evaluation.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return
  fixed, heldout = load_scenario(args.fixed_scenario), load_scenario(args.heldout_scenario)
  output = args.output_root
  runs = {
    "fixed_baseline": run_repetitions(fixed, 8.0, 3, output / "fixed-baseline-ratio8", args.allow_dirty),
    "fixed_candidate": run_repetitions(fixed, float(candidate_ratio), 3, output / "fixed-candidate", args.allow_dirty),
    "heldout_baseline": run_repetitions(heldout, 8.0, 3, output / "heldout-baseline-ratio8", args.allow_dirty),
    "heldout_candidate": run_repetitions(heldout, float(candidate_ratio), 3, output / "heldout-candidate", args.allow_dirty),
  }
  evidence = {key: [str(path / "summary.json") for path in value] for key, value in runs.items()}
  candidate_paths = runs["fixed_candidate"] + runs["heldout_candidate"]
  candidate_success = all(passed(path / "summary.json") for path in candidate_paths)
  result = {"schema_version": 1, "scope": "pretrained_actuation_calibration_evaluation_not_road_performance",
            "selection": {"path": str(args.selection), "steer_ratio": candidate_ratio}, "runs": evidence,
            "candidate_success": candidate_success,
            "next_step": "run_delay_matrix" if candidate_success else "retain_negative_result_no_delay_matrix"}
  write_json(output / "evaluation.json", result)
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()
