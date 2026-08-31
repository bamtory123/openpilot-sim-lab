#!/usr/bin/env python3
"""Small CUDA sanity check kept separate from the long simulator bridge."""

import argparse
import json
import time

from tinygrad import Device, Tensor


parser = argparse.ArgumentParser(description="tinygrad CUDA sanity check")
parser.add_argument("--duration-s", type=float, default=0.0)
args = parser.parse_args()

started, iterations, size = time.monotonic(), 0, 1024 if args.duration_s <= 0 else 4096
expected = size * (size - 1)
value = 0
while iterations == 0 or time.monotonic() - started < args.duration_s:
  value = (Tensor.arange(size).to(Device.DEFAULT) * 2).sum().realize().item()
  iterations += 1
print(json.dumps(
  {"device": Device.DEFAULT, "expected_sum": expected, "sum": int(value), "iterations": iterations,
   "elapsed_ms": round((time.monotonic() - started) * 1000, 3)},
  sort_keys=True,
))
if Device.DEFAULT != "CUDA" or int(value) != expected:
  raise SystemExit("CUDA sanity check failed")
