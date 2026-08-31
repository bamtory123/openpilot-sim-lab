#!/usr/bin/env python3
"""Exercise MetaDrive's offscreen road camera without starting openpilot."""

import argparse
import json
import time

from metadrive.envs.metadrive_env import MetaDriveEnv
from openpilot.tools.sim.bridge.metadrive.metadrive_bridge import RGBCameraRoad, create_map
from openpilot.tools.sim.bridge.metadrive.metadrive_process import apply_metadrive_patches
from openpilot.tools.sim.lib.camerad import H, W


parser = argparse.ArgumentParser(description="MetaDrive renderer sanity check")
parser.add_argument("--steps", type=int, default=100)
args = parser.parse_args()
if args.steps < 1:
  parser.error("--steps must be positive")

apply_metadrive_patches(arrive_dest_done=False)
env = MetaDriveEnv({
  "use_render": False,
  "vehicle_config": {"enable_reverse": False, "render_vehicle": False, "image_source": "rgb_road"},
  "sensors": {"rgb_road": (RGBCameraRoad, W, H)},
  "image_on_cuda": False,
  "image_observation": True,
  "interface_panel": [],
  "out_of_route_done": False,
  "on_continuous_line_done": False,
  "crash_vehicle_done": False,
  "crash_object_done": False,
  "random_spawn_lane_index": False,
  "map_config": create_map(track_size=60, curve_direction=0, route_profile="loop"),
  "decision_repeat": 1,
  "physics_world_step_size": 0.05,
  "preload_models": False,
  "start_seed": 20260831,
  "num_scenarios": 1,
})
started, captures = time.monotonic(), 0
try:
  env.reset()
  for step in range(args.steps):
    env.step([0.0, 0.0])
    if step % 5 == 0:
      image = env.engine.sensors["rgb_road"].perceive(to_float=False)
      if tuple(image.shape) != (H, W, 3):
        raise RuntimeError(f"unexpected road image shape: {image.shape}")
      captures += 1
finally:
  env.close()

print(json.dumps({"steps": args.steps, "captures": captures, "image_shape": [H, W, 3],
                  "elapsed_ms": round((time.monotonic() - started) * 1000, 3)}, sort_keys=True))
