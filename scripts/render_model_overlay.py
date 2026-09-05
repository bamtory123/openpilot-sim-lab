#!/usr/bin/env python3
"""Render one analysis-only OpenPilot model snapshot over its camera frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from simlab.model_overlay import save_overlay


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--image", type=Path, required=True)
  parser.add_argument("--model-snapshot", type=Path, required=True)
  parser.add_argument("--output", type=Path, required=True)
  args = parser.parse_args()
  snapshot = json.loads(args.model_snapshot.read_text(encoding="utf-8"))
  result = save_overlay(args.image, snapshot, args.output)
  print(json.dumps({"schema_version": 1, "scope": "analysis_only_model_overlay", **result}, sort_keys=True))


if __name__ == "__main__":
  main()
