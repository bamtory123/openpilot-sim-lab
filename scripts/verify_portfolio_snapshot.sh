#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "portfolio snapshot requires a clean sim-lab working tree" >&2
  exit 1
fi
if [[ -n "$(git tag --contains HEAD)" ]]; then
  echo "portfolio snapshot must not be a release-tag commit" >&2
  exit 1
fi

uv run pytest -q
uv run python scripts/verify_v01_public_evidence.py
echo "portfolio snapshot: PASS $(git rev-parse HEAD)"
