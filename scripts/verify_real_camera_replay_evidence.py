#!/usr/bin/env python3
"""Verify the public-only real-camera model replay evidence bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_real_camera_replay_evidence import FORBIDDEN, render_readme, render_svg


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("directory", type=Path)
  args = parser.parse_args()
  evidence_path = args.directory / "evidence.json"
  evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
  real, meta = evidence["real_camera_reference"], evidence["metadrive_closed_loop"]
  if evidence.get("scope") != "real_camera_replay_vs_metadrive_model_output_contrast_not_accuracy_or_road_performance":
    raise SystemExit("incorrect evidence scope")
  if real["functional_status"] != "pass" or real["model_v2_count"] != real["expected_frames"]:
    raise SystemExit("real-camera functional replay is incomplete")
  if meta["validity"] != "valid" or meta["outcome"] != "fail":
    raise SystemExit("MetaDrive diagnostic boundary changed")
  digests = {"real": real["summary_sha256"], "meta_summary": meta["summary_sha256"],
             "meta_telemetry": meta["telemetry_sha256"]}
  invalid_digests = [name for name, value in digests.items() if len(value) != 64]
  if invalid_digests:
    raise SystemExit(f"invalid source SHA-256: {', '.join(invalid_digests)}")
  serialized = evidence_path.read_text(encoding="utf-8")
  if any(token in serialized for token in FORBIDDEN):
    raise SystemExit("public evidence exposes a local token")
  if (args.directory / "README.md").read_text(encoding="utf-8") != render_readme(evidence):
    raise SystemExit("README differs from evidence")
  if (args.directory / "comparison.svg").read_text(encoding="utf-8") != render_svg(evidence):
    raise SystemExit("SVG differs from evidence")
  print(json.dumps({"schema_version": 1, "scope": "public_real_camera_replay_evidence_only", "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
  main()
