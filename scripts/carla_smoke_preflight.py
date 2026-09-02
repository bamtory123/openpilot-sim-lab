from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
from queue import Queue


def main() -> None:
  parser = argparse.ArgumentParser(description="CARLA v0.2 smoke preflight; no simulator is started")
  parser.add_argument("--server-exe", type=Path)
  parser.add_argument("--connect", action="store_true")
  parser.add_argument("--host", default="127.0.0.1")
  parser.add_argument("--port", type=int, default=2000)
  parser.add_argument("--timeout-s", type=float, default=5.0)
  parser.add_argument("--sync-ticks", type=int, default=0)
  parser.add_argument("--camera-state-control-smoke", action="store_true")
  parser.add_argument("--camera-ticks", type=int, default=3)
  args = parser.parse_args()
  if args.sync_ticks < 0:
    parser.error("--sync-ticks must be non-negative")
  if args.sync_ticks and not args.connect:
    parser.error("--sync-ticks requires --connect")
  if args.camera_state_control_smoke and not args.connect:
    parser.error("--camera-state-control-smoke requires --connect")

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
    if args.sync_ticks or args.camera_state_control_smoke:
      world = client.get_world()
      original_settings = world.get_settings()
      settings = world.get_settings()
      settings.synchronous_mode = True
      settings.fixed_delta_seconds = 0.05
      vehicle = camera = None
      try:
        world.apply_settings(settings)
        if args.camera_state_control_smoke:
          spawn = world.get_map().get_spawn_points()[0]
          vehicle = world.try_spawn_actor(world.get_blueprint_library().filter("vehicle.*")[0], spawn)
          if vehicle is None:
            raise RuntimeError("CARLA vehicle spawn failed")
          camera_blueprint = world.get_blueprint_library().find("sensor.camera.rgb")
          camera_blueprint.set_attribute("image_size_x", "320")
          camera_blueprint.set_attribute("image_size_y", "180")
          images: Queue = Queue()
          camera = world.spawn_actor(camera_blueprint, carla.Transform(carla.Location(x=1.5, z=2.4)), attach_to=vehicle)
          camera.listen(images.put)
          vehicle.apply_control(carla.VehicleControl(throttle=0.0, steer=0.0, brake=1.0))
        tick_count = max(args.sync_ticks, args.camera_ticks if args.camera_state_control_smoke else 0)
        result["sync_tick_frames"] = [world.tick() for _ in range(tick_count)]
        if args.camera_state_control_smoke:
          image = images.get(timeout=args.timeout_s)
          velocity = vehicle.get_velocity()
          control = vehicle.get_control()
          result["camera"] = {"frame": image.frame, "width": image.width, "height": image.height}
          result["vehicle_control"] = {"throttle": control.throttle, "steer": control.steer, "brake": control.brake}
          result["vehicle_speed_mps"] = (velocity.x ** 2 + velocity.y ** 2 + velocity.z ** 2) ** 0.5
      finally:
        if camera is not None:
          camera.stop()
          camera.destroy()
        if vehicle is not None:
          vehicle.destroy()
        world.apply_settings(original_settings)
      result["sync_tick_count"] = tick_count
      result["world_settings_restored"] = True
      if args.camera_state_control_smoke:
        result["actors_destroyed"] = True
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()
