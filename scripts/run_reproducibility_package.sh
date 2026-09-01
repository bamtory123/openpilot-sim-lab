#!/usr/bin/env bash
set -euo pipefail

: "${OPENPILOT_ROOT:?Set OPENPILOT_ROOT to the instrumented openpilot checkout}"
: "${OPENPILOT_PYTHON:=$OPENPILOT_ROOT/.venv/bin/python}"
output_root="${1:-outputs/reproducibility-package-$(date -u +%Y%m%dT%H%M%SZ)}"
scenario="configs/scenarios/md_default_loop_lane0_host_confirmation_v1.yaml"

uv run pytest -q
PYTHONPATH=src "$OPENPILOT_PYTHON" -m simlab.runner preflight --allow-dirty --scenario "$scenario"
OPENPILOT_ROOT="$OPENPILOT_ROOT" OPENPILOT_PYTHON="$OPENPILOT_PYTHON" scripts/run_host_stability_probe.sh "$scenario" "$output_root"
PYTHONPATH=src "$OPENPILOT_PYTHON" -m simlab.runner report --outputs "$output_root"
"$OPENPILOT_PYTHON" scripts/verify_reproducibility_package.py "$output_root"
