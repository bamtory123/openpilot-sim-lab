#!/usr/bin/env bash
set -euo pipefail
: "${OPENPILOT_ROOT:?Set OPENPILOT_ROOT to the instrumented openpilot checkout}"
: "${OPENPILOT_PYTHON:=$OPENPILOT_ROOT/.venv/bin/python}"
"$OPENPILOT_PYTHON" -m simlab.runner preflight --scenario "${1:-configs/scenarios/md_default_loop_lane0_v1.yaml}"
