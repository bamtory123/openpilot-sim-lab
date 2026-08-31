#!/usr/bin/env bash
set -euo pipefail

: "${OPENPILOT_ROOT:?Set OPENPILOT_ROOT to the instrumented openpilot checkout}"
: "${OPENPILOT_PYTHON:=$OPENPILOT_ROOT/.venv/bin/python}"

scenario="${1:?Pass a scenario path}"
output_root="${2:?Pass an output root}"
attempt_dir="$output_root/host-probe-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$attempt_dir"
boot_before="$(cat /proc/sys/kernel/random/boot_id)"

"$OPENPILOT_PYTHON" - "$attempt_dir/attempt.json" "$scenario" "$boot_before" <<'PY'
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

path, scenario, boot_id = map(str, sys.argv[1:])
Path(path).write_text(json.dumps({
  "schema_version": 1,
  "created_at_utc": datetime.now(timezone.utc).isoformat(),
  "scenario_path": scenario,
  "recorded_wsl_boot_id": boot_id,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

set +e
PYTHONPATH=src "$OPENPILOT_PYTHON" -m simlab.runner --allow-dirty run --scenario "$scenario" --outputs "$attempt_dir/runs"
exit_code=$?
set -e
boot_after="$(cat /proc/sys/kernel/random/boot_id)"

"$OPENPILOT_PYTHON" - "$attempt_dir/attempt.json" "$exit_code" "$boot_after" <<'PY'
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

path, exit_code, boot_id = sys.argv[1:]
payload = json.loads(Path(path).read_text(encoding="utf-8"))
payload.update({
  "completed_at_utc": datetime.now(timezone.utc).isoformat(),
  "runner_exit_code": int(exit_code),
  "observed_wsl_boot_id": boot_id,
  "wsl_boot_changed": payload["recorded_wsl_boot_id"] != boot_id,
})
Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

exit "$exit_code"
