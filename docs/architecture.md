# Architecture

```text
OpenPilot (SUT) ← camera/control bridge → MetaDrive (SIL)
                    ↑
 openpilot-sim-lab: scenario → orchestration → telemetry/camera/events
                                      → validity/outcome → report/artifacts
```

The bridge receives camera frames through the non-blocking delay queue. MetaDrive ground truth is calculated against the fixed reference-lane index, not nearest lane. `telemetry.csv` and `camera.csv` remain separate rates; `events.jsonl` carries asynchronous lifecycle events. See [openpilot patch](openpilot-patch.md) for the minimal SUT instrumentation boundary.

The manifest records actual source/runtime state. Before each run, `configs/compatibility.yaml` is enforced: the configured OpenPilot base and instrumentation commits must be ancestors of the checkout, and the Python major version must match.

The v0.2 CARLA pilot is a separate path:

```text
OpenPilot commands → CARLA adapter → CARLA VehicleControl → vehicle response telemetry
CARLA RGB/state ───────────────────→ existing camera transport / simulated sensors → OpenPilot
```

The adapter owns synchronous CARLA ticks and actor lifetime. It consumes a prebuilt route asset only for town/start-pose validation; it must not feed route or CARLA ground truth into control. Each run records command versus applied control and physical transform/velocity/yaw response separately. Optional CARLA RGB capture has a bounded asynchronous PNG writer; its route labels are joined offline into `analysis_only` samples, so neither the queue nor its labels can affect control.
