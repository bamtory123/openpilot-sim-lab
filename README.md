# OpenPilot ADAS SIL Validation Lab

Reproducible **MetaDrive closed-loop repeatability study** for openpilot. The v0.1 question is: *after normal engagement, how does a fixed camera transport delay change one fixed reference-lane tracking scenario?*

## What this repository adds

- deterministic scenario validation and environment manifests
- MetaDrive ground-truth telemetry against a fixed reference lane
- non-blocking 0/50/100/150 ms camera transport-delay experiments
- valid/pass/fail separation, KPI calculation, batch orchestration, and Markdown/SVG reporting

The environment uses openpilot's existing synthetic Honda Civic CAN/Panda emulation. It does **not** implement SocketCAN, reverse engineer a vehicle CAN bus, validate real EPS/actuator dynamics, train an AI model, perform HIL, or prove real-road performance.

## Scenario and protocol

`md_default_loop_lane0_v1` fixes the openpilot default two-lane loop map, seed, and reference lane. A warm-up run is excluded; then 0, 50, 100, and 150 ms are each run three times in interleaved blocks. This is a repeatability study, not a statistical validation or road-generalization claim.

The fault is applied only after openpilot engagement. After a five-second queue-settle interval, 1,200 camera frames are measured. Producer capture copies RGB immediately; an independent scheduler publishes immutable YUV frames at their monotonic release deadline.

The default scenario is model-driven. Its current 0 ms baseline is a valid lane-departure failure, so it is a diagnostic baseline rather than a passing driving claim. A separate 60-degree-FOV scenario exists only to inspect camera-domain sensitivity and is excluded from formal delay results.

## Quick start (WSL)

```bash
cd /home/hyunsung/src/openpilot-sim-lab
export OPENPILOT_ROOT=/home/hyunsung/src/openpilot
export OPENPILOT_PYTHON="$OPENPILOT_ROOT/.venv/bin/python3"
$OPENPILOT_PYTHON -m pip install --no-deps -e .
$OPENPILOT_PYTHON -m simlab.runner preflight
$OPENPILOT_PYTHON -m simlab.runner batch --outputs outputs
$OPENPILOT_PYTHON -m simlab.runner report --outputs outputs
```

The runner rejects dirty repositories by default. Use `--allow-dirty` only during development; dirty state is recorded in `manifest.json`.

For unit tests of the orchestration package, use `uv run pytest -q` from this repository. The MetaDrive runtime itself is intentionally supplied by the instrumented openpilot virtual environment above.

## Output contract

Each run contains `manifest.json`, the resolved `scenario.yaml`, 100 Hz `telemetry.csv`, 20 Hz `camera.csv`, `events.jsonl`, `summary.json`, and process logs. `validity` describes whether the infrastructure/data is usable; `outcome` describes closed-loop performance. Lane departure and disengagement are valid failures, not invalid data.

## Limitations

This is SIL only. Camera rendering, timing, synthetic CAN, vehicle dynamics, and actuator behaviour differ from an ECU and a real vehicle. CARLA is documented as a Windows–WSL smoke-test effort and is not a v0.1 release gate.

See [the instrumentation summary](docs/openpilot-patch.md) and [CARLA smoke-test status](docs/carla-smoke.md).
