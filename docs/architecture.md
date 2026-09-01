# Architecture

```text
OpenPilot (SUT) ← camera/control bridge → MetaDrive (SIL)
                    ↑
 openpilot-sim-lab: scenario → orchestration → telemetry/camera/events
                                      → validity/outcome → report/artifacts
```

The bridge receives camera frames through the non-blocking delay queue. MetaDrive ground truth is calculated against the fixed reference-lane index, not nearest lane. `telemetry.csv` and `camera.csv` remain separate rates; `events.jsonl` carries asynchronous lifecycle events. See [openpilot patch](openpilot-patch.md) for the minimal SUT instrumentation boundary.
