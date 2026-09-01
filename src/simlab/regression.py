from __future__ import annotations

import json
from pathlib import Path


METRICS = ("lateral_rmse_m", "lateral_abs_p95_m", "applied_steering_rate_rms_deg_s", "speed_mean_mps", "actual_delay_median_ms")


def _summaries(root: Path, scenario_id: str, delay_ms: int) -> list[dict]:
  records = []
  for path in root.rglob("summary.json"):
    if "warmup" in path.parts:
      continue
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("scenario_id") == scenario_id and record.get("target_delay_ms") == delay_ms:
      manifest_path = path.with_name("manifest.json")
      record["_scenario_hash"] = json.loads(manifest_path.read_text(encoding="utf-8")).get("scenario_hash") if manifest_path.is_file() else None
      records.append(record)
  return records


def _median(values: list[float]) -> float | None:
  if not values:
    return None
  values.sort()
  middle = len(values) // 2
  return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2


def review_regression(baseline_root: Path, candidate_root: Path, *, scenario_id: str, delay_ms: int) -> dict:
  baseline, candidate = _summaries(baseline_root, scenario_id, delay_ms), _summaries(candidate_root, scenario_id, delay_ms)
  hard_gate_failures = []
  baseline_hashes = {record.get("_scenario_hash") for record in baseline}
  candidate_hashes = {record.get("_scenario_hash") for record in candidate}
  if not baseline_hashes or None in baseline_hashes or len(baseline_hashes) != 1:
    hard_gate_failures.append("baseline:scenario_provenance_incomplete")
  if not candidate_hashes or None in candidate_hashes or candidate_hashes != baseline_hashes:
    hard_gate_failures.append("candidate:scenario_hash_mismatch")
  for record in candidate:
    reasons = set(record.get("reasons", []))
    if record.get("validity") == "invalid":
      hard_gate_failures.append(f"{record.get('run_id')}:invalid")
    if "collision" in reasons or "disengagement" in reasons:
      hard_gate_failures.append(f"{record.get('run_id')}:new_functional_event")
  deltas = {}
  if baseline and candidate:
    for metric in METRICS:
      before = _median([float(r["metrics"][metric]) for r in baseline if r.get("metrics", {}).get(metric) is not None])
      after = _median([float(r["metrics"][metric]) for r in candidate if r.get("metrics", {}).get(metric) is not None])
      deltas[metric] = None if before is None or after is None else {"baseline_median": before, "candidate_median": after, "delta": after - before}
  review_required = any(item is not None and item["delta"] != 0 for item in deltas.values()) and not hard_gate_failures
  return {"schema_version": 1, "scenario_id": scenario_id, "target_delay_ms": delay_ms,
          "baseline_runs": len(baseline), "candidate_runs": len(candidate), "phase_1_hard_gate_failures": hard_gate_failures,
          "baseline_scenario_hash": next(iter(baseline_hashes), None), "candidate_scenario_hashes": sorted(item for item in candidate_hashes if item),
          "phase_2_review_required": review_required, "phase_3_performance_gate": "disabled_pending_approved_thresholds",
          "metric_deltas_scope": "diagnostic_only" if hard_gate_failures else "evaluated",
          "metric_deltas": deltas, "verdict": "hard_gate_fail" if hard_gate_failures else ("review_required" if review_required else "no_change")}
