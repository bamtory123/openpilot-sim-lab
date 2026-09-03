#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
python_runner="${SIMLAB_PYTHON:-}"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "portfolio snapshot requires a clean sim-lab working tree" >&2
  exit 1
fi
if [[ -n "$(git tag --contains HEAD)" ]]; then
  echo "portfolio snapshot must not be a release-tag commit" >&2
  exit 1
fi

if [[ -n "$python_runner" ]]; then
  "$python_runner" -m pytest -q
  "$python_runner" scripts/verify_portfolio_readiness.py
else
  uv run pytest -q
  uv run python scripts/verify_portfolio_readiness.py
fi
echo "portfolio snapshot: PASS $(git rev-parse HEAD)"
