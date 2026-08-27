#!/usr/bin/env bash
set -euo pipefail
: "${OPENPILOT_ROOT:?Set OPENPILOT_ROOT to the instrumented openpilot checkout}"
python -m simlab.runner preflight --scenario "${1:-configs/scenarios/md_default_loop_lane0_v1.yaml}"
