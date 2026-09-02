from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_carla_smoke_public_evidence import build_evidence, render_summary


def main() -> None:
  parser = argparse.ArgumentParser(description="Verify generated public CARLA client-smoke evidence")
  parser.add_argument("result", type=Path)
  parser.add_argument("--output-dir", type=Path, required=True)
  args = parser.parse_args()
  expected = build_evidence(args.result)
  evidence_path = args.output_dir / "evidence.json"
  summary_path = args.output_dir / "README.md"
  try:
    actual = json.loads(evidence_path.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError) as error:
    raise SystemExit(f"cannot read public CARLA evidence: {error}") from error
  if actual != expected:
    raise SystemExit("public CARLA evidence differs from retained source")
  if summary_path.read_text(encoding="utf-8") != render_summary(expected):
    raise SystemExit("public CARLA summary differs from generated evidence")
  print(json.dumps({"schema_version": 1, "scope": expected["scope"], "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
  main()
