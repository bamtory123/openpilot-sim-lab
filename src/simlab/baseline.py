from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


REQUIRED_ARTIFACTS = ("manifest.json", "scenario.yaml", "telemetry.csv", "camera.csv", "events.jsonl", "summary.json")


def _sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for block in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(block)
  return digest.hexdigest()


def audit_historical_baseline(contract_path: Path, repo_root: Path) -> dict:
  """Audit the immutable artifact set selected by a baseline contract."""
  contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
  evidence = contract["baseline_evidence"]
  root = repo_root / evidence["historical_artifact_root"]
  expected = evidence["expected"]
  findings, runs, provenance = [], [], []
  for run_id in evidence["formal_run_ids"]:
    run_dir = root / run_id
    run = {"run_id": run_id, "artifacts": {}}
    for name in REQUIRED_ARTIFACTS:
      path = run_dir / name
      if not path.is_file() or path.stat().st_size == 0:
        findings.append(f"{run_id}:missing_or_empty:{name}")
      else:
        run["artifacts"][name] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    if len(run["artifacts"]) == len(REQUIRED_ARTIFACTS):
      manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
      summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
      scenario = yaml.safe_load((run_dir / "scenario.yaml").read_text(encoding="utf-8"))
      checks = {
        "manifest_run_id": manifest.get("run_id") == run_id,
        "summary_run_id": summary.get("run_id") == run_id,
        "scenario_id": summary.get("scenario_id") == expected["scenario_id"] == scenario.get("scenario_id"),
        "target_delay_ms": summary.get("target_delay_ms") == expected["target_delay_ms"] == scenario.get("fault", {}).get("target_delay_ms"),
        "validity": summary.get("validity") == expected["validity"],
        "outcome": summary.get("outcome") == expected["outcome"],
        "clean_openpilot": manifest.get("openpilot", {}).get("dirty") is False,
        "clean_sim_lab": manifest.get("sim_lab", {}).get("dirty") is False,
      }
      for name, passed in checks.items():
        if not passed:
          findings.append(f"{run_id}:check_failed:{name}")
      run["checks"] = checks
      provenance.append({key: manifest.get(key) for key in ("scenario_hash", "metadrive_version", "driver", "gpu", "python_version", "wsl_kernel")}
                      | {"openpilot_commit": manifest.get("openpilot", {}).get("commit"), "sim_lab_commit": manifest.get("sim_lab", {}).get("commit")})
    runs.append(run)
  if len({json.dumps(item, sort_keys=True) for item in provenance}) > 1:
    findings.append("provenance_mismatch_between_runs")
  return {"schema_version": 1, "baseline_id": contract["baseline_id"], "contract": str(contract_path),
          "artifact_root": str(root), "status": "approved" if not findings else "evidence_gap",
          "findings": findings, "provenance": provenance[0] if provenance else {}, "runs": runs}
