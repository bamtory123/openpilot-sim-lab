#!/usr/bin/env bash
set -euo pipefail

mode="${1:---install}"
if [[ "$mode" != "--install" && "$mode" != "--check" ]]; then
  echo "usage: $0 [--install|--check]" >&2
  exit 2
fi

root="${SIMLAB_WORK_ROOT:-$(cd .. && pwd)}"
openpilot_root="${OPENPILOT_ROOT:-$root/openpilot}"
metadrive_root="${METADRIVE_ROOT:-$root/metadrive}"
openpilot_commit="${OPENPILOT_COMMIT:-d7ee3435737d7e0bd88f14ffedd45999b6d2e957}"
metadrive_commit="${METADRIVE_COMMIT:-2716f55a9c7b928ce957a497a15c2c19840c08bc}"

check() {
  command -v git >/dev/null
  command -v uv >/dev/null
  [[ -x "$openpilot_root/.venv/bin/python" ]]
  [[ "$(git -C "$openpilot_root" rev-parse HEAD)" == "$openpilot_commit" ]]
  [[ "$(git -C "$metadrive_root" rev-parse HEAD)" == "$metadrive_commit" ]]
  "$openpilot_root/.venv/bin/python" -c 'import importlib.metadata, metadrive; print(importlib.metadata.version("metadrive-simulator"))'
  echo "bootstrap check: PASS"
}

if [[ "$mode" == "--check" ]]; then
  check
  exit 0
fi

command -v git >/dev/null || { echo "install git first" >&2; exit 1; }
command -v uv >/dev/null || { echo "install uv first: https://docs.astral.sh/uv/" >&2; exit 1; }
mkdir -p "$root"
if [[ ! -d "$openpilot_root/.git" ]]; then
  git clone --recurse-submodules https://github.com/bamtory123/openpilot.git "$openpilot_root"
fi
git -C "$openpilot_root" fetch origin
git -C "$openpilot_root" checkout "$openpilot_commit"
git -C "$openpilot_root" submodule update --init --recursive
(cd "$openpilot_root" && uv sync --group standalone)
if [[ ! -d "$metadrive_root/.git" ]]; then
  git clone https://github.com/commaai/metadrive.git "$metadrive_root"
fi
git -C "$metadrive_root" fetch origin
git -C "$metadrive_root" checkout "$metadrive_commit"
uv pip install --python "$openpilot_root/.venv/bin/python" -e "$metadrive_root"
uv pip install --python "$openpilot_root/.venv/bin/python" -e .
uv sync --group dev
check
