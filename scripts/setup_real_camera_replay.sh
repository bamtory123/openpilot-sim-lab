#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "$script_dir/.." && pwd)
tool_root="$repo_root/.tools"
archive_name=ffmpeg-n7.1.5-12-g1fdbca85aa-linux64-gpl-7.1.tar.xz
archive_url="https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-07-31-14-10/$archive_name"
archive_sha256=c1e6caf48923dd8e6bc5e54d51ba70c321175b8162ae9c414c392990e72f0e79

if [[ $(uname -m) != x86_64 ]]; then
  echo "This pinned helper supports x86_64 WSL only." >&2
  exit 2
fi

mkdir -p "$tool_root/downloads" "$tool_root/bin"
curl -fL --retry 3 -o "$tool_root/downloads/$archive_name" "$archive_url"
printf '%s  %s\n' "$archive_sha256" "$tool_root/downloads/$archive_name" | sha256sum -c -
tar -xf "$tool_root/downloads/$archive_name" -C "$tool_root"
ln -sfn "$tool_root/ffmpeg-n7.1.5-12-g1fdbca85aa-linux64-gpl-7.1/bin/ffmpeg" "$tool_root/bin/ffmpeg"
ln -sfn "$tool_root/ffmpeg-n7.1.5-12-g1fdbca85aa-linux64-gpl-7.1/bin/ffprobe" "$tool_root/bin/ffprobe"

echo "FFmpeg replay tools installed under $tool_root."
echo "Run with: PATH=$tool_root/bin:\$PATH <openpilot-python> scripts/run_real_camera_model_replay.py ..."
