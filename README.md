# SDV ADAS SIL Regression Validation Lab

OpenPilot is the System Under Test (SUT), MetaDrive is the SIL environment, and this repository is the validation orchestration, telemetry, fault-injection, verdict and report framework. The v0.1 question is: *after normal engagement, how does a fixed camera transport delay change one fixed reference-lane tracking scenario?*

## What this repository adds

- deterministic scenario validation and environment manifests
- MetaDrive ground-truth telemetry against a fixed reference lane
- non-blocking 0/50/100/150 ms camera transport-delay experiments
- valid/pass/fail separation, KPI calculation, batch orchestration, and Markdown/SVG reporting

The environment uses openpilot's existing synthetic Honda Civic CAN/Panda emulation. It does **not** implement SocketCAN, reverse engineer a vehicle CAN bus, validate real EPS/actuator dynamics, train an AI model, perform HIL, or prove real-road performance. Its opt-in low-density traffic probe records actor presence only; it is not an obstacle-avoidance evaluation.

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
scripts/check_environment.sh
$OPENPILOT_PYTHON -m simlab.runner batch --outputs outputs
$OPENPILOT_PYTHON -m simlab.runner report --outputs outputs
```

The runner rejects dirty repositories by default. Use `--allow-dirty` only during development; dirty state is recorded in `manifest.json`.

The environment script also runs the short CUDA sanity check. In this workstation's intended dirty MetaDrive source state, use `SIMLAB_ALLOW_DIRTY=1 scripts/check_environment.sh`.

Before any long CUDA-backed matrix, follow the bounded checks and Windows-event collection procedure in [host stability](docs/host-stability.md). A host interruption is invalid infrastructure data, not a driving result.

For unit tests of the orchestration package, use `uv run pytest -q` from this repository. The MetaDrive runtime itself is intentionally supplied by the instrumented openpilot virtual environment above.

For the one-command bounded reproducibility package, follow [reproducibility](docs/reproducibility.md). It produces a self-checking output directory without starting the long formal matrix.

## Output contract

Each run contains `manifest.json`, the resolved `scenario.yaml`, 100 Hz `telemetry.csv`, 20 Hz `camera.csv`, `events.jsonl`, `summary.json`, and process logs. `validity` describes whether the infrastructure/data is usable; `outcome` describes closed-loop performance. Lane departure and disengagement are valid failures, not invalid data.

If Windows/WSL restarts during a run, run `scripts/recover_interrupted_runs.sh outputs`. It recovers both manifest-backed run directories and pre-manifest host-probe attempts as `invalid/not_evaluated: host_interrupted`, never overwriting an existing result. Reports flag an unrecovered host attempt as an evidence gap rather than silently omitting it.

## Limitations

This is SIL only. Camera rendering, timing, synthetic CAN, vehicle dynamics, and actuator behaviour differ from an ECU and a real vehicle. CARLA is documented as a Windows–WSL smoke-test effort and is not a v0.1 release gate.

See [the instrumentation summary](docs/openpilot-patch.md), [formal progress/results](docs/progress.md), and [CARLA smoke-test status](docs/carla-smoke.md).
The validation plan and requirement/test traceability are [PLAN](PLAN.md), [requirements](docs/requirements.md), [test plan](docs/test-plan.md), and [traceability](docs/traceability.md).
The current framework qualification is [not qualified yet](docs/qualification-report.md); its governing choices are in the [decision log](docs/decisions.md).
For the concise portfolio framing, see [portfolio summary](docs/portfolio-summary.md).
The separate MetaDrive-only RGB replay experiment is documented in [simulator-specialist](docs/simulator-specialist.md).
For the exact formal-run procedure and result checks, see [reproducibility](docs/reproducibility.md).
The release-friendly formal sample is in [examples/v0.2-formal-delay-matrix](examples/v0.2-formal-delay-matrix/README.md).
The constrained simulator-specialist delay sample is in [examples/v0.5-specialist-speed2-delay-matrix](examples/v0.5-specialist-speed2-delay-matrix/README.md).
The gamma-0.8 specialist delay sample is in [examples/v0.6-specialist-gamma08-delay-matrix](examples/v0.6-specialist-gamma08-delay-matrix/README.md).
The fixed 3.0 m/s specialist delay sample is in [examples/v0.6-specialist-speed3-delay-matrix](examples/v0.6-specialist-speed3-delay-matrix/README.md); it remains limited to its declared speed contract.
The separate tight-loop specialist samples are [three 0 ms repeats](examples/v0.6-specialist-tight-dagger/README.md) and its [0/50/100/150 ms delay matrix](examples/v0.6-specialist-tight-dagger-delay-matrix/README.md); both remain limited to their declared local artifact and fixed MetaDrive contract.
The v0.2 serpentine delay sample is in [examples/v0.2-specialist-serpentine-delay-matrix](examples/v0.2-specialist-serpentine-delay-matrix/README.md); it is a separate versioned synthetic topology and not part of the v0.1 release result.
The separate low-traffic serpentine delay sample is in [examples/v0.2-specialist-serpentine-low-traffic-delay-matrix](examples/v0.2-specialist-serpentine-low-traffic-delay-matrix/README.md); it records actor presence but is not a traffic-interaction or avoidance result.
The planned public release boundary is recorded in the [release checklist](docs/release-checklist.md).
Camera input diagnostics and their limits are documented in [camera-domain-gap](docs/camera-domain-gap.md).
The consolidated scope of every positive and negative evaluation result is in [evaluation boundary](docs/evaluation-boundary.md).
