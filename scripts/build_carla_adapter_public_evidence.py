from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SCOPE = "carla_adapter_pilot_public_summary_only"


def build_evidence(summary_path: Path) -> dict:
  source = summary_path.read_bytes()
  summary = json.loads(source)
  if summary.get("schema_version") != 1 or summary.get("scope") != "carla_v02_adapter_pilot_not_road_qualification":
    raise ValueError("source is not a CARLA adapter-pilot summary")
  if not isinstance(summary.get("run_count"), int) or not isinstance(summary.get("status_counts"), dict):
    raise ValueError("source summary is incomplete")
  return {"schema_version": 1, "scope": SCOPE, "source_sha256": hashlib.sha256(source).hexdigest(),
          "formal": {"run_count": summary["run_count"], "status_counts": summary["status_counts"],
                     "reason_counts": summary.get("reason_counts", {})}}


def render_summary(evidence: dict) -> str:
  formal = evidence["formal"]
  statuses = ", ".join(f"{key}={value}" for key, value in sorted(formal["status_counts"].items())) or "none"
  reasons = ", ".join(f"{key}={value}" for key, value in sorted(formal["reason_counts"].items())) or "none"
  return f"""# CARLA adapter-pilot public summary

This is a public-safe aggregate from a retained bounded CARLA v0.2 adapter-pilot matrix. It is outside the v0.1 MetaDrive release gate and does not demonstrate successful OpenPilot driving, CARLA closed-loop qualification, real-road performance, or generalization.

## Formal aggregate

| Field | Value |
|---|---|
| Retained pilot runs | {formal["run_count"]} |
| Pilot status counts | {statuses} |
| Termination reason counts | {reasons} |

All retained matrix runs were preserved as `integrated-but-not-stable: lane_departure`, rather than discarded as infrastructure failures or relabeled as a driving pass. The source SHA-256 is `{evidence["source_sha256"]}`. This public sample excludes local paths, host/IP data, raw RGB, telemetry, logs, route transforms, and individual run IDs.
"""


def main() -> None:
  parser = argparse.ArgumentParser(description="Build a public-safe CARLA adapter-pilot aggregate")
  parser.add_argument("summary", type=Path)
  parser.add_argument("--output-dir", type=Path, required=True)
  args = parser.parse_args()
  evidence = build_evidence(args.summary)
  args.output_dir.mkdir(parents=True, exist_ok=True)
  (args.output_dir / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  (args.output_dir / "README.md").write_text(render_summary(evidence), encoding="utf-8")


if __name__ == "__main__":
  main()
