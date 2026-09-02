from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path


def main() -> None:
  parser = argparse.ArgumentParser(description="CARLA v0.2 smoke preflight; no simulator is started")
  parser.add_argument("--server-exe", type=Path)
  parser.add_argument("--connect", action="store_true")
  parser.add_argument("--host", default="127.0.0.1")
  parser.add_argument("--port", type=int, default=2000)
  parser.add_argument("--timeout-s", type=float, default=5.0)
  parser.add_argument("--sync-ticks", type=int, default=0)
  args = parser.parse_args()
  if args.sync_ticks < 0:
    parser.error("--sync-ticks must be non-negative")
  if args.sync_ticks and not args.connect:
    parser.error("--sync-ticks requires --connect")

  try:
    import carla
  except ImportError as error:
    raise SystemExit("CARLA Python client is not installed in this runtime") from error
  if args.server_exe is not None and not args.server_exe.is_file():
    raise SystemExit(f"CARLA server executable is missing: {args.server_exe}")

  result = {"schema_version": 1, "scope": "carla_client_or_connectivity_smoke_only",
            "client_version": importlib.metadata.version("carla"), "server_exe": str(args.server_exe) if args.server_exe else None,
            "connect_requested": args.connect}
  if args.connect:
    client = carla.Client(args.host, args.port)
    client.set_timeout(args.timeout_s)
    result.update({"host": args.host, "port": args.port, "server_version": client.get_server_version()})
    if args.sync_ticks:
      world = client.get_world()
      original_settings = world.get_settings()
      settings = world.get_settings()
      settings.synchronous_mode = True
      settings.fixed_delta_seconds = 0.05
      try:
        world.apply_settings(settings)
        result["sync_tick_frames"] = [world.tick() for _ in range(args.sync_ticks)]
      finally:
        world.apply_settings(original_settings)
      result["sync_tick_count"] = args.sync_ticks
      result["world_settings_restored"] = True
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()
