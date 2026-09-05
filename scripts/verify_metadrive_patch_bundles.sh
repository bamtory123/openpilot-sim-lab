#!/usr/bin/env bash
set -euo pipefail

base="2716f55a9c7b928ce957a497a15c2c19840c08bc"
root=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --metadrive-root) root="$2"; shift 2 ;;
    *) echo "usage: $0 --metadrive-root <checkout>" >&2; exit 2 ;;
  esac
done
[[ -n "$root" && -d "$root/.git" ]] || { echo "--metadrive-root must be a Git checkout" >&2; exit 2; }

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
traffic="$here/patches/metadrive-0.4.2.3-traffic-render-vehicle.patch"
markings="$here/patches/metadrive-0.4.2.3-road-marking-profile.patch"
expected_traffic="3a3a7b9b0e2e80de951c5b77416d87a42a4bb3bf72f4a01fb0085189d79cd78d"
expected_markings="fe28d2bc76fce42a516c9d5483d41112e850c0b8c688669db21a79912e2e12a8"
[[ "$(sha256sum "$traffic" | cut -d' ' -f1)" == "$expected_traffic" ]] || { echo "traffic patch checksum mismatch" >&2; exit 1; }
[[ "$(sha256sum "$markings" | cut -d' ' -f1)" == "$expected_markings" ]] || { echo "road-marking patch checksum mismatch" >&2; exit 1; }
git -C "$root" cat-file -e "$base^{commit}"

worktree="$(mktemp -d "${TMPDIR:-/tmp}/metadrive-patch-check.XXXXXX")"
cleanup() { git -C "$root" worktree remove --force "$worktree" >/dev/null 2>&1 || true; }
trap cleanup EXIT
git -C "$root" worktree add --detach "$worktree" "$base" >/dev/null
git -C "$worktree" apply --check "$traffic"
git -C "$worktree" apply "$traffic"
git -C "$worktree" apply --check "$markings"
git -C "$worktree" apply "$markings"
git -C "$worktree" diff --check
printf 'MetaDrive patch bundles: PASS base=%s\n' "$base"
