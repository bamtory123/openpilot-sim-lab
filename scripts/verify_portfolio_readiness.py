from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from build_v01_public_evidence import render_summary as render_v01_summary

ROOT = Path(__file__).resolve().parents[1]


def run(name: str, *args: str) -> None:
  result = subprocess.run([sys.executable, str(ROOT / "scripts" / name), *args], capture_output=True, text=True)
  if result.returncode:
    raise SystemExit(result.stderr.strip() or result.stdout.strip() or f"{name} failed")


def main() -> None:
  parser = argparse.ArgumentParser(description="Verify portfolio-ready public and optional local evidence boundaries")
  parser.add_argument("--repro-root", type=Path)
  parser.add_argument("--host-stack", type=Path)
  parser.add_argument("--carla-result", type=Path)
  parser.add_argument("--verify-local-v01", action="store_true")
  args = parser.parse_args()

  v01_evidence = json.loads((ROOT / "examples/v0.1-portfolio-evidence/evidence.json").read_text(encoding="utf-8"))
  v01_summary = (ROOT / "examples/v0.1-portfolio-evidence/SUMMARY.md").read_text(encoding="utf-8")
  if v01_summary != render_v01_summary(v01_evidence):
    raise SystemExit("public v0.1 summary differs from evidence.json")
  report = (ROOT / "docs/qualification-report.md").read_text(encoding="utf-8")
  snapshot = (ROOT / "docs/portfolio-snapshot.md").read_text(encoding="utf-8")
  carla = (ROOT / "examples/v0.2-carla-client-smoke/evidence.json").read_text(encoding="utf-8")
  carla_summary = (ROOT / "examples/v0.2-carla-client-smoke/README.md").read_text(encoding="utf-8")
  adapter = (ROOT / "examples/v0.2-carla-adapter-pilot/evidence.json").read_text(encoding="utf-8")
  adapter_summary = (ROOT / "examples/v0.2-carla-adapter-pilot/README.md").read_text(encoding="utf-8")
  if "`not_qualified_yet`" not in report or "not a new GitHub release, tag" not in snapshot:
    raise SystemExit("v0.1 qualification boundary is missing")
  if any(token in carla for token in ("172.28.", "C:\\", "server.stdout.log", "client.log")):
    raise SystemExit("public CARLA evidence exposes a local detail")
  if "outside the v0.1 MetaDrive release gate" not in carla_summary or "does not demonstrate an OpenPilot bridge, closed loop" not in carla_summary:
    raise SystemExit("public CARLA sample boundary is missing")
  if '"scope": "carla_adapter_pilot_public_summary_only"' not in adapter or "does not demonstrate successful OpenPilot driving" not in adapter_summary:
    raise SystemExit("public CARLA adapter sample boundary is missing")

  checks = {"public_v01": "pass", "public_carla": "pass"}
  if args.verify_local_v01:
    run("verify_v01_public_evidence.py")
    checks["v01_retained_source"] = "pass"
  if args.repro_root is not None:
    run("verify_reproducibility_package.py", str(args.repro_root))
    checks["reproducibility_package"] = "pass"
  if args.host_stack is not None:
    run("verify_host_stack_artifact.py", str(args.host_stack))
    checks["host_stack"] = "pass"
  if args.carla_result is not None:
    run("verify_carla_smoke_public_evidence.py", str(args.carla_result), "--output-dir",
        str(ROOT / "examples/v0.2-carla-client-smoke"))
    checks["carla_retained_source"] = "pass"
  print(json.dumps({"schema_version": 1, "scope": "portfolio_readiness_only", "status": "pass", "checks": checks},
                   sort_keys=True))


if __name__ == "__main__":
  main()
