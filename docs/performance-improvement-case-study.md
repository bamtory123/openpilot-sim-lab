# v0.2 SIL performance-improvement case study

## Claim boundary

v0.1 is frozen: its pretrained OpenPilot qualification remains `not_qualified_yet`. v0.2 demonstrates that the same SIL framework can isolate a candidate change, use fixed and held-out evidence to reject or retain it, and package the result without turning simulator evidence into a road-performance claim.

There are two deliberately separate tracks.

| Track | Change under test | What it may show | What it cannot show |
|---|---|---|---|
| Pretrained actuator calibration | Only the OpenPilot steering-angle to MetaDrive normalized-steer ratio; model, planner, CAN/Panda, and ground-truth control stay unchanged | Whether the simulator actuator interface is a measurable source of error under this contract | Improved pretrained perception, planning, real-vehicle behavior, or road safety |
| Simulator-specialist positive controls | Retained targeted-data and DAgger artifacts | That the SIL loop can preserve a reproducible simulator-only improvement and held-out check | Any claim about upstream pretrained OpenPilot or real-road generalization |

## Pretrained actuator-calibration protocol

The `actuation.steer_ratio` scenario contract defaults to `8.0`; the tuning candidates are `8`, `4`, `2`, and `1`. It is applied only when OpenPilot supplies `steeringAngleDeg`; it is excluded for `simulator_control` and `specialist_replay`. Route, lane, and simulator ground truth stay telemetry-only and never enter this runtime control path.

Each telemetry record keeps the configured ratio, OpenPilot command, normalized simulator steer, applied steering angle, yaw rate, and actual curvature. The report adds command/applied sign agreement and gain plus normalized-steer and actual-curvature RMS/P95.

1. Run the 400-camera-frame tuning scenario once per ratio in the fixed order `8 → 4 → 2 → 1`.
2. Preserve every attempt. Exclude `invalid` runs and collision candidates. Select the lowest lateral RMSE; on a tie choose the larger ratio.
3. If a non-8 ratio is selected, run baseline ratio 8 and the changed candidate three times on the fixed loop, then three times each on the held-out serpentine loop. If ratio 8 wins, retain that no-change selection as a negative calibration result instead of fabricating a candidate identity.
4. A candidate is a success only if all six candidate runs are `valid/pass` with the full frame, coverage, timing, no-drop, no-collision, and no-lane-departure contract. Otherwise retain the negative calibration result and do not run its delay matrix.
5. Only a successful candidate proceeds to the interleaved 0/50/100/150 ms × 3 matrix for each scenario.

The commands are intentionally separate so long local runs can use the retained durable-attempt and host-event collection workflow:

```bash
OPENPILOT_ROOT=/home/hyunsung/src/openpilot/openpilot \
  .venv/bin/python -m simlab.runner actuation-tune --allow-dirty \
  --scenario configs/scenarios/md_default_loop_lane0_pretrained_actuation_tuning_v2.yaml \
  --outputs outputs/v0.2-actuation-tuning

.venv/bin/python scripts/run_pretrained_actuation_evaluation.py --allow-dirty \
  --selection outputs/v0.2-actuation-tuning/actuation-selection.json \
  --fixed-scenario configs/scenarios/md_default_loop_lane0_pretrained_actuation_fixed_v2.yaml \
  --heldout-scenario configs/scenarios/md_serpentine_lane0_pretrained_actuation_heldout_v2.yaml \
  --output-root outputs/v0.2-actuation-evaluation
```

If `evaluation.json` has `candidate_success: true`, run `scripts/run_pretrained_actuation_delay_matrix.py` with the same selection scenarios and an empty output root. All long attempts must retain their attempt/manifest, WSL boot ID, GPU before/after snapshot, and Windows System/VmSwitch event correlation. An interruption is `invalid/not_evaluated`, not a functional failure.

## Simulator-specialist positive controls

The public-safe [aggregate bundle](../examples/v0.2-performance-improvement-case-study/SUMMARY.md) is source-hash bound to retained local summaries and contains no raw frame, telemetry, local path, process log, or model artifact.

- Targeted gamma/curve data: a gamma-0.8 baseline `valid/fail` is followed by three `valid/pass` candidates and a retained 12-run delay matrix.
- Tight DAgger geometry: a 45 m baseline `valid/fail` is followed by three 45 m fixed `valid/pass` runs and three 52 m held-out `valid/pass` runs.

These are simulator-specialist positive controls, not a replacement for the frozen pretrained result.
