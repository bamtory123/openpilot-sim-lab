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
| Target speed 3.0 m/s using v0.6 gamma-0.8 artifact | 1 × `valid/pass`, 1,200 frames, 0.52325 m lateral RMSE | One later artifact and one fixed speed point only; not speed robustness. |
| Target speed 4.0 m/s using v0.6 gamma-0.8 artifact | `invalid/not_evaluated`, 50.44 s, coverage 0.841; lane departure observed | Insufficient measurement coverage prevents a driving-performance verdict. |
| Target speed 4.0 m/s | `valid/fail`, 653 frames, 0.49527 m lateral RMSE | Higher-speed sensitivity. |
| 45 m loop after v0.6 targeted data | `valid/fail`, 1,200 frames, 0.50021 m lateral RMSE | Partial RMSE improvement, but no geometry-generalized pass. |
| 45 m loop after v0.6 tight DAgger data | 3 × `valid/pass`, 1,200 frames each, 0.41224 m mean lateral RMSE | Repeatable result only for the fixed 45 m/2.0 m/s contract. |
| 52 m intermediate loop using the tight DAgger artifact | 3 × `valid/pass`, 1,200 frames each, 0.49060 m mean lateral RMSE | A second deterministic geometry point, not arbitrary geometry generalization. |
| 45 m tight loop, 0/50/100/150 ms delay matrix | 3 × `valid/pass` per delay; median RMSE 0.42030/0.42123/0.42140/0.42123 m | Non-blocking delay delivery under the fixed tight-loop contract only. |
| 45 m tight loop, gamma 1.2 | 3 × `valid/pass`, 1,200 frames each, 0.39387 m lateral RMSE | One synthetic rendering parameter; not real-camera appearance robustness. |
| 45 m tight loop, gamma 0.8 | 1 × `valid/pass`, 1,200 frames, 0.46903 m lateral RMSE | One-run geometry/rendering interaction probe only. |
| v0.2 60 m serpentine topology | 3 × `valid/pass`, 1,200 frames each, 0.44492 m mean lateral RMSE | One versioned synthetic topology; not arbitrary route generalization. |
| v0.2 serpentine, 0/50/100/150 ms delay matrix | 3 × `valid/pass` per delay; median RMSE 0.44571/0.44598/0.44598/0.44564 m | Non-blocking delay delivery only for the fixed serpentine contract. |
| v0.2 mirrored serpentine, 0 ms | 3 × `valid/pass`, 1,200 frames each, 0.23674 m mean lateral RMSE | A second fixed direction contract; not arbitrary direction robustness. |
| v0.2 mirrored serpentine, 0/50/100/150 ms delay matrix | 3 × `valid/pass` per delay; median RMSE 0.23643/0.23651/0.23654/0.23672 m | Non-blocking delay delivery only for the fixed mirrored contract. |
| v0.2 serpentine, `traffic_density: 0.03`, 0 ms | 3 × `valid/pass`, 1,200 frames each; 3.34–3.35 mean traffic actors, maximum 4 | Fixed-seed low-density synthetic traffic lane-following only; no interaction, yielding, braking, or avoidance evaluation. |
| v0.2 low-traffic serpentine, 0/50/100/150 ms delay matrix | 3 × `valid/pass` per delay; median RMSE 0.44696/0.44734/0.44628/0.44710 m; maximum 4 actors/run | Delay delivery only for this fixed low-density synthetic-traffic contract, not traffic-interaction robustness. |
| v0.2 low-traffic active-actor proximity probe | 0.656 mean active actors; closest ego-to-active-actor distance 239.57 m | Confirms no meaningful encounter exposure; this is not an interaction, following, braking, or avoidance test. |
| v0.2 respawn-traffic proximity probe | 2 active actors throughout; closest ego-to-active-actor distance 28.00 m | Meets a versioned ≤30 m exposure contract only; it does not evaluate traffic policy, following, braking, or avoidance. |
| v0.2 respawn-traffic closing-speed/TTC probe | Closest distance 27.87 m; maximum closing speed −2.60 m/s; no positive TTC | Actor and ego are separating, not approaching; no longitudinal interaction exposure exists. |
| v0.2 fixed static lead, 20 m gap | `valid/fail: collision`; closest distance 4.47 m; maximum closing speed 2.00 m/s; minimum TTC 2.29 s | Reproducible approaching-lead baseline failure, not following, braking, or avoidance capability. |
| v0.2 static-lead camera alignment | RGB captures at 2/4/8 s are joined to 18.17/14.63/6.76 m and 11.61/7.69/3.40 s TTC labels | Physics lead is absent from RGB under minimal assets; analysis-only telemetry/camera alignment, not lead-perception data. |
| v0.2 static-lead three-seed dataset matrix | 30 RGB labels, 20/10 train/held-out split; 3 × `valid/fail: collision` | Repeats one fixed collision/data contract; invisible lead means it is not a visual-perception dataset. |
| v0.2 visible static box-obstacle smoke | Box visible at 2/8 s; 10 traffic-labeled RGB samples; `valid/fail` | A fixed black box only, not a vehicle/pedestrian/traffic-object detector or avoidance evaluation. |
| v0.2 visible static box-obstacle matrix | 30 RGB labels, 20/10 train/held-out split; 3 × `valid/fail` | Repeats one visible black-box failure/data contract; not object detection or avoidance capability. |
| 60 m gamma 0.8 using the tight DAgger artifact | `valid/pass`, 1,200 frames, 0.54819 m lateral RMSE | Passes the KPI but regresses versus the gamma-curve artifact; artifacts remain condition-specific. |

These are valid measurements, not invalid infrastructure runs. Their failure is retained as evidence and is not hidden by selecting the 2.0 m/s result.

## Claims allowed

- Deterministic MetaDrive orchestration, provenance, telemetry, actual-delay measurement, and valid/pass/fail classification work as documented.
- The model-driven baseline has a repeatable simulator camera-domain failure under the fixed scenario.
- The local specialist artifact meets the KPI only under its explicitly documented fixed 2.0 m/s simulator contract.

## Claims excluded

- Successful openpilot automated driving, a better pretrained openpilot model, or a real-vehicle control improvement.
- Generalization across road geometry, rendering, speed, traffic interaction, weather, camera hardware, or real-world data.
- HIL, CAN-bus integration, EPS/actuator validation, safety validation, or CARLA closed-loop validation.

For experiment details see [simulator-specialist](simulator-specialist.md), [camera-domain-gap](camera-domain-gap.md), and [reproducibility](reproducibility.md).
