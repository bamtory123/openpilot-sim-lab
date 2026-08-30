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

`md_default_loop_lane0_reference_assist_diagnostic_v1` is a separate simulator-only controller experiment. It records openpilot output but does not use it for vehicle actuation. Its initial gain trials remain valid lane-departure failures, so it is not a replacement for the model-driven baseline and is not a closed-loop openpilot success claim.

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

See [the instrumentation summary](docs/openpilot-patch.md), [formal progress/results](docs/progress.md), and [CARLA smoke-test status](docs/carla-smoke.md).
The separate MetaDrive-only RGB replay experiment is documented in [simulator-specialist](docs/simulator-specialist.md).
For the exact formal-run procedure and result checks, see [reproducibility](docs/reproducibility.md).
The release-friendly formal sample is in [examples/v0.2-formal-delay-matrix](examples/v0.2-formal-delay-matrix/README.md).
The constrained simulator-specialist delay sample is in [examples/v0.5-specialist-speed2-delay-matrix](examples/v0.5-specialist-speed2-delay-matrix/README.md).
The gamma-0.8 specialist delay sample is in [examples/v0.6-specialist-gamma08-delay-matrix](examples/v0.6-specialist-gamma08-delay-matrix/README.md).
The separate tight-loop specialist samples are [three 0 ms repeats](examples/v0.6-specialist-tight-dagger/README.md) and its [0/50/100/150 ms delay matrix](examples/v0.6-specialist-tight-dagger-delay-matrix/README.md); both remain limited to their declared local artifact and fixed MetaDrive contract.
The v0.2 serpentine delay sample is in [examples/v0.2-specialist-serpentine-delay-matrix](examples/v0.2-specialist-serpentine-delay-matrix/README.md); it is a separate versioned synthetic topology and not part of the v0.1 release result.
The planned public release boundary is recorded in the [release checklist](docs/release-checklist.md).
Camera input diagnostics and their limits are documented in [camera-domain-gap](docs/camera-domain-gap.md).
The consolidated scope of every positive and negative evaluation result is in [evaluation boundary](docs/evaluation-boundary.md).
