# Evaluation boundary

This page is the decision record for what the repository's results do and do not support. `valid/pass` means only that a specified simulator contract met its recorded KPI for one measurement budget; it is not a claim about a vehicle, road, or the pretrained openpilot driving stack.

## Controller paths

| Path | Input used for actuation | Result boundary |
|---|---|---|
| Pretrained openpilot baseline | Normal openpilot model/planner/control path | Reproducible MetaDrive `valid/fail` lane departure. Camera/transport diagnostics point to a rendering-domain mismatch, not a proven controller defect. |
| Simulator-specialist replay | Local RGB temporal ridge artifact, road camera only | Opt-in MetaDrive experiment. It does not modify the pretrained model, openpilot control gains, CAN, or Panda behavior. |
| Ground-truth teacher | Reference-lane geometry | Dataset-label and instrumentation validation only; never used by specialist replay at runtime. |

## Strongest positive result

The retained v0.4 specialist has a repeatable pass on the fixed 60 m loop with seed `20260829`, reference lane 0, default rendering, and 2.0 m/s target speed. Three 0 ms repeats and the 12-run 0/50/100/150 ms matrix all completed the 1,200-camera-frame budget as `valid/pass` with no lane departure, collision, or camera drop. A separate v0.6 targeted-data artifact repeats that result under gamma 0.8 at 2.0 m/s only.

The delay matrix proves that the non-blocking delay injector delivered its configured transport delay in this narrow contract. It does not prove delay robustness outside that contract.

## Boundary probes

| Changed factor from the 2.0 m/s fixed contract | Result | Meaning |
|---|---|---|
| 45 m tighter loop | `valid/fail`, 1,145 frames, 0.54032 m lateral RMSE | No route-geometry generalization. |
| Camera gamma 0.8 | `valid/fail`, 1,030 frames, 1.34232 m lateral RMSE | No appearance generalization. |
| Gamma 0.8 after v0.6 targeted data | 3 × `valid/pass`; 12-run 0/50/100/150 ms matrix also all `valid/pass` | Improvement only for the same 60 m/2.0 m/s/gamma-0.8 contract. |
| Target speed 3.0 m/s | 3 × `valid/fail`, 882–883 frames | No speed/dynamics robustness at the collection condition. |
| Target speed 4.0 m/s | `valid/fail`, 653 frames, 0.49527 m lateral RMSE | Higher-speed sensitivity. |
| 45 m loop after v0.6 targeted data | `valid/fail`, 1,200 frames, 0.50021 m lateral RMSE | Partial RMSE improvement, but no geometry-generalized pass. |
| 45 m loop after v0.6 tight DAgger data | 3 × `valid/pass`, 1,200 frames each, 0.41224 m mean lateral RMSE | Repeatable result only for the fixed 45 m/2.0 m/s contract. |
| 60 m gamma 0.8 using the tight DAgger artifact | `valid/pass`, 1,200 frames, 0.54819 m lateral RMSE | Passes the KPI but regresses versus the gamma-curve artifact; artifacts remain condition-specific. |

These are valid measurements, not invalid infrastructure runs. Their failure is retained as evidence and is not hidden by selecting the 2.0 m/s result.

## Claims allowed

- Deterministic MetaDrive orchestration, provenance, telemetry, actual-delay measurement, and valid/pass/fail classification work as documented.
- The model-driven baseline has a repeatable simulator camera-domain failure under the fixed scenario.
- The local specialist artifact meets the KPI only under its explicitly documented fixed 2.0 m/s simulator contract.

## Claims excluded

- Successful openpilot automated driving, a better pretrained openpilot model, or a real-vehicle control improvement.
- Generalization across road geometry, rendering, speed, traffic, weather, camera hardware, or real-world data.
- HIL, CAN-bus integration, EPS/actuator validation, safety validation, or CARLA closed-loop validation.

For experiment details see [simulator-specialist](simulator-specialist.md), [camera-domain-gap](camera-domain-gap.md), and [reproducibility](reproducibility.md).
