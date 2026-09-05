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
OPENPILOT_ROOT=/home/hyunsung/src/openpilot \
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

## Pretrained camera-domain candidate protocol

The separate color-match diagnostic requires permission-cleared road-camera reference frames. It hashes inputs and produces only a bounded RGB affine proposal; it does not use route/lane ground truth at runtime. An identity proposal is retained as no change. A non-identity proposal follows the same fixed/held-out three-run candidate gate as actuator calibration, then may enter a delay matrix only after all six candidate runs pass. See [camera-domain gap](camera-domain-gap.md) for the command boundary and limitations.

## Simulator-specialist positive controls

The public-safe [aggregate bundle](../examples/v0.2-performance-improvement-case-study/SUMMARY.md) is source-hash bound to retained local summaries and contains no raw frame, telemetry, local path, process log, or model artifact.

- Targeted gamma/curve data: a gamma-0.8 baseline `valid/fail` is followed by three `valid/pass` candidates and a retained 12-run delay matrix.
- Tight DAgger geometry: a 45 m baseline `valid/fail` is followed by three 45 m fixed `valid/pass` runs and three 52 m held-out `valid/pass` runs.

These are simulator-specialist positive controls, not a replacement for the frozen pretrained result.

## Simulator-specialist negative gate

The retained v0.6 artifact produced three incomplete 3.5 m/s runs with observed departure on the same right curve at 87.86–91.42 m. A source-hashed localizer selected frames 4,960–5,600 before that common failure, and two durable runs added 33 train and 33 validation teacher-labelled samples. The resulting v0.7 candidate worsened offline validation RMSE (`0.00880 → 0.01027` normalized steer) and, in its single held-out diagnostic, departed at 49.48 m with observed partial-run lateral RMSE `0.98317 m` versus the v0.6 three-run observed mean `0.62414 m`.

The candidate was therefore rejected before repeat or delay-matrix expansion. Both baseline and candidate runs were `invalid/not_evaluated` because departure caused incomplete coverage, so their RMSE values are explicitly performance-ineligible. The public-safe [negative case bundle](../examples/v0.2-specialist-speed-boundary/SUMMARY.md) preserves the data/model/result hashes and demonstrates that the improvement loop can reject a regression rather than only showcase positive results.

A constrained follow-up blended the unchanged v0.6 output with the rejected update. Its offline gate selected the minimum alpha `0.5`, improving targeted validation RMSE by 41.77% while limiting original-validation degradation to 1.08%. Three fresh-seed repeats then produced two `valid/pass` and one `valid/fail` result; RMSE was `0.49987`, `0.53219`, and `0.70821 m`, with the failed run departing at 49.85 m. This is a partial improvement over the full update, but it fails the required 3/3 repeatability gate. The candidate remains unadopted, and no 3.0 m/s regression or delay matrix is permitted.
