#!/usr/bin/env bash
set -euo pipefail
python -m simlab.runner batch --scenario "${1:-configs/scenarios/md_default_loop_lane0_v1.yaml}" --outputs "${2:-outputs}"
