"""Create a frozen Town04 route asset before any synchronous adapter run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def yaw_delta(before: float, after: float) -> float:
  return (after - before + 180.0) % 360.0 - 180.0


def trace_route(carla, game_map, start, steps: int = 220) -> tuple[list, list[str]]:
  route, turns = [start], []
  for _ in range(steps):
    choices = route[-1].next(2.0)
    if not choices:
      break
    previous = route[-1].transform.rotation.yaw
    deltas = [yaw_delta(previous, choice.transform.rotation.yaw) for choice in choices]
    selected_index = min(range(len(choices)), key=lambda index: abs(deltas[index]))
    choice = choices[selected_index]
    if len(choices) > 1:
      selected = deltas[selected_index]
      turns.append("left" if selected < -5 else "right" if selected > 5 else "straight")
    route.append(choice)
  return route, turns


def main() -> None:
  parser = argparse.ArgumentParser(description="Build a deterministic CARLA city route asset")
  parser.add_argument("--host", required=True)
  parser.add_argument("--port", type=int, default=2000)
  parser.add_argument("--town", default="Town04")
  parser.add_argument("--output", type=Path, required=True)
  args = parser.parse_args()
  import carla
  client = carla.Client(args.host, args.port)
  client.set_timeout(60.0)
  world = client.get_world()
  if world.get_map().name.rsplit("/", 1)[-1] != args.town:
    world = client.load_world(args.town)
  game_map = world.get_map()
  candidates = []
  spawn_points = game_map.get_spawn_points()
  stride = max(1, len(spawn_points) // 24)
  for spawn in spawn_points[::stride]:
    start = game_map.get_waypoint(spawn.location, project_to_road=True, lane_type=carla.LaneType.Driving)
    if start is None:
      continue
    route, turns = trace_route(carla, game_map, start)
    # A turn-bearing route avoids the historical all-straight asset; the route
    # is still only a reproducible spawn/reference artifact, never controller input.
    score = (len(set(turns) & {"left", "right"}), len(turns), len(route))
    candidates.append((score, route, turns))
  if not candidates:
    raise SystemExit("Town04 has no usable driving waypoint route")
  _, route, turns = max(candidates, key=lambda item: item[0])
  if len(route) < 80 or not ({"left", "right"} & set(turns)):
    raise SystemExit("Town04 route search did not produce a turn-bearing city route")
  points = [[waypoint.transform.location.x, waypoint.transform.location.y, waypoint.transform.location.z,
             waypoint.transform.rotation.pitch, waypoint.transform.rotation.yaw, waypoint.transform.rotation.roll]
            for waypoint in route]
  asset = {"schema_version": 1, "route_kind": "city_mixed", "town": args.town, "point_spacing_m": 2.0, "points": points,
           "turn_plan": ["straight", "left", "right"], "turns_realized": turns}
  canonical = json.dumps(asset, sort_keys=True, separators=(",", ":")).encode()
  asset["sha256"] = hashlib.sha256(canonical).hexdigest()
  args.output.parent.mkdir(parents=True, exist_ok=True)
  args.output.write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")
  print(json.dumps({"output": str(args.output), "points": len(points), "turns_realized": turns,
                    "sha256": asset["sha256"]}, sort_keys=True))


if __name__ == "__main__":
  main()
