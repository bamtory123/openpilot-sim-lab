#!/usr/bin/env bash
set -euo pipefail

base="084747c75d2cbd23af65ab7a9e770bbd7b98bac9"
root=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --openpilot-root) root="$2"; shift 2 ;;
    *) echo "usage: $0 --openpilot-root <checkout>" >&2; exit 2 ;;
  esac
done
[[ -n "$root" && -d "$root/.git" ]] || { echo "--openpilot-root must be a Git checkout" >&2; exit 2; }

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
v01="$here/patches/openpilot-v01-sim-instrumentation.patch"
v02="$here/patches/openpilot-v02-carla-adapter.patch"
expected_v01="959e1846cd9b1a0111de346befcf749218f70ad74e06af574f284d687e6661c4"
expected_v02="05fef675a69d91dd0c37a88ffbe3d49cc5919e5151d7b37526f14595bee5d085"
[[ "$(sha256sum "$v01" | cut -d' ' -f1)" == "$expected_v01" ]] || { echo "v0.1 patch checksum mismatch" >&2; exit 1; }
[[ "$(sha256sum "$v02" | cut -d' ' -f1)" == "$expected_v02" ]] || { echo "v0.2 patch checksum mismatch" >&2; exit 1; }
git -C "$root" cat-file -e "$base^{commit}"

worktree="$(mktemp -d "${TMPDIR:-/tmp}/openpilot-patch-check.XXXXXX")"
cleanup() { git -C "$root" worktree remove --force "$worktree" >/dev/null 2>&1 || true; }
trap cleanup EXIT
git -C "$root" worktree add --detach "$worktree" "$base" >/dev/null
git -C "$worktree" apply --check "$v01"
git -C "$worktree" apply "$v01"
git -C "$worktree" apply --check "$v02"
git -C "$worktree" apply "$v02"
git -C "$worktree" diff --check
printf 'patch bundles: PASS base=%s\n' "$base"
