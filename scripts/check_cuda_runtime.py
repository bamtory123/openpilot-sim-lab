#!/usr/bin/env python3
"""Small CUDA sanity check kept separate from the long simulator bridge."""

import json
import time

from tinygrad import Device, Tensor


started = time.monotonic()
value = (Tensor.arange(1024).to(Device.DEFAULT) * 2).sum().realize().item()
print(json.dumps(
  {"device": Device.DEFAULT, "expected_sum": 1047552, "sum": int(value),
   "elapsed_ms": round((time.monotonic() - started) * 1000, 3)},
  sort_keys=True,
))
if Device.DEFAULT != "CUDA" or int(value) != 1047552:
  raise SystemExit("CUDA sanity check failed")
