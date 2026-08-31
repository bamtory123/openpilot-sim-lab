# Camera-domain-gap diagnostic

This document records evidence about the simulator camera input. It does not measure real-road perception accuracy or justify a steering-gain change.

## Fixed input contract

- MetaDrive road camera: 1928×1208 RGB.
- Bridge transport: immediate copy, BT.601 NV12 conversion, then VisionIPC at the same resolution.
- Modeld PC/tici narrow-camera expectation: 1928×1208 with 2648 px focal length.
- Simulator horizontal FOV: 40 degrees, equivalent to about 2648 px at 1928 px width.

The first-order resolution/FOV/focal-length geometry therefore matches. The RGB→NV12 limited-range contract has a unit fixture: black RGB becomes luma 16 with neutral chroma 128.

## Frame-aligned evidence

The 2026-08-29 diagnostic run captured the road image at simulation frame 2500 and emitted a JSON companion file. The matching telemetry row reported:

| Field | Value |
|---|---:|
| Current reference curvature | 0.000000 1/m |
| Reference curvature from frame 2600 | +0.008658 1/m |
| Lateral error | -0.978 m |
| Model/control target curvature | about +0.0000035 1/m |

The image visibly contains the upcoming left curve while the current segment is still straight. This is consistent with a near-zero model response to a visually present upcoming turn. It is not a ground-truth label for model outputs.

A later three-frame set used the same 40-degree, 2648.57 px camera contract:

| Simulation frame | Reference curvature (1/m) | Model/control target curvature (1/m) | Lateral error (m) |
|---:|---:|---:|---:|
| 2400 | 0.000000 | +0.0000054 | -0.877 |
| 2600 | +0.008658 | -0.0000066 | -1.029 |
| 2800 | +0.008658 | -0.0000054 | -0.737 |

The frame set reinforces that the near-zero model response persists after the reference segment enters the curve. It does not identify the cause within rendering, camera pose, calibration, or model generalization.

An explicit zero-pose diagnostic (`camera_position_m: [0, 0, 1.22]`, `camera_hpr_deg: [0, 0, 0]`) completed with the same valid lane-departure/KPI failure contract and zero transport drops. Symmetric ±2 degree pitch diagnostics are therefore isolated next experiments; they are excluded from the formal matrix.

The pitch sweep showed sensitivity but no solution: at 0°, −2°, and +2°, curve-segment model-target absolute means were 0.00000495, 0.00006109, and 0.00001110 1/m respectively, versus +0.008658 1/m reference curvature. Lateral RMSE was 0.633, 0.665, and 0.616 m; all runs remained valid lane/KPI failures. A single −4° exploratory point is retained only to determine whether the negative-pitch response is monotonic.

The −4° point was a valid failure before reaching the curve (simulation frame 835; no curved-segment telemetry), with high speed variance and 2.26 deg/s applied steering-rate RMS. It is not comparable to the other pitch points and ends the pitch sweep: no pose is promoted from these diagnostics. Subsequent work should inspect model path output rather than continue uncalibrated camera-pose tuning.

## Model inference health

The 0 ms inference-health diagnostic recorded `model_valid` on every measured sample, zero model frame age and drop percentage, and a 9.9 ms P95 model execution time. The latest camera source ID and `model_frame_id` both reached 643. The model therefore consumed current delayed-queue output, but its median predicted path horizon was only 4.91 m and predicted terminal speed 2.74 m/s while actual vehicle speed averaged 4.55 m/s. This rules out camera queue staleness as the explanation for the near-zero lateral response; it does not establish which image-domain or model-input contract mismatch causes the short prediction.

The calibration-telemetry retry recorded `calibrated` on all 2,895 measurement samples with RPY exactly `[0, 0, 0]`. The modeld image warp is therefore initialized and stable; no calibration adjustment is justified by the current evidence.

Runtime camera-contract telemetry also confirmed all 2,875 measurement samples used modeld key `pc/unknown` with 1928×1208, 2648 px narrow-road intrinsics. This verifies the actual modeld selection, not merely the intended simulator configuration. Resolution, focal-length, calibration state, queue freshness, and model frame contract are now ruled out as primary causes of the short path output.

The next controlled probe is an opt-in gamma 0.8 camera transform. It alters only pixel luminance before NV12 conversion; map, pose, intrinsics, delay, and controls remain fixed. It is a domain-gap sensitivity diagnostic, never a formal-baseline replacement.

## Repeatable alignment fixture

`md_default_loop_lane0_frame_alignment_diagnostic_v1` opt-in captures simulation frames 2400, 2600, and 2800 into the run's `debug/` directory. The runner writes `camera_alignment.json`, joining each image metadata record to its nearest simulator telemetry record. This diagnostic artifact is intentionally separate from the formal delay matrix and gives every later camera-contract experiment the same image/ground-truth/model-path evidence.

The first fixture run produced all three PNG/metadata pairs and exact frame joins. Reference curvature changed from 0 at frame 2400 to +0.008658 1/m at frames 2600 and 2800; model curvature remained about 10⁻⁶ 1/m, while its path horizon remained 4–5 m. This is repeatable evidence for the domain/input-contract investigation, not a control-tuning result.

## Photometric baseline

For that capture, simple RGB-derived statistics were:

| Region | Luma mean | Luma std | Luma median | Chroma mean |
|---|---:|---:|---:|---:|
| Full frame | 128.33 | 33.07 | 130.72 | 18.21 |
| Lower-half road region | 98.73 | 13.33 | 95.94 | 10.20 |
| Centre lower road region | 98.58 | 11.76 | 96.24 | 9.84 |

These values are regression baselines only. They cannot be compared to a real camera without a matched real-road data protocol.

## Next controlled work

1. Capture matched frame sets at fixed map positions before and during the curve; retain frame metadata and telemetry joins.
2. Inspect model path/curvature output against those frame sets without changing controller gains.
3. If a camera change is proposed, alter one documented variable at a time and preserve the 40-degree formal baseline unchanged.

## Minimal-asset traffic limitation

The installed MetaDrive `0.4.2.3` minimal asset package contains road assets but no vehicle meshes. A deterministic static physics lead can therefore generate collision, distance, closing-speed, and TTC telemetry while remaining absent from the RGB road camera. Enabling vehicle rendering raises a missing `models/ferra/right_tire_front.gltf` error and terminates the bridge. Static-lead runs are consequently retained only for simulator-physics/telemetry contracts; no RGB lead-perception dataset, training, or evaluation claim is permitted until a versioned asset package with a renderable vehicle is installed and separately verified. A scenario that declares `diagnostics.require_visible_lead: true` is now rejected at preflight when that mesh is unavailable.

## Gamma sensitivity result

With every camera/model contract field fixed, gamma 0.8 increased curve-segment mean absolute model curvature from about `4.7e-06` to `1.09e-05 1/m`; gamma 1.2 produced `4.05e-06 1/m`. Required reference curvature is about `8.66e-03 1/m`. All three gamma conditions remained valid lane/KPI failures with a roughly 4–5 m model path horizon. Global luminance affects output slightly but is not the primary camera/model mismatch.

## Lane-semantic telemetry result

The frame-alignment fixture was repeated after adding read-only `modelV2` lane-line telemetry. The infrastructure result remained `valid/fail` (lane departure and lateral-error KPI), while model validity remained 100%, frame age/drop remained zero, and inference P95 was 9.97 ms. This preserves the earlier conclusion that the model receives current frames.

| Segment | Samples | Left lane probability mean | Right lane probability mean | Model path horizon mean |
|---|---:|---:|---:|---:|
| Straight (`|reference curvature| < 0.001`) | 2,550 | 0.0115 | 0.0223 | 5.03 m |
| Curve (`|reference curvature| >= 0.001`) | 635 | 0.0137 | 0.0273 | 4.41 m |

The lane-line probabilities are low in both segments and do not rise when the simulator enters the known curve. The corresponding near-field lane positions remain populated, so an empty Cap'n Proto field is not being misread as a low score. Together with the short 4–5 m path and near-zero curvature, this is strong simulator-domain evidence that the pretrained model does not assign meaningful lane confidence to the current MetaDrive rendering. It is not evidence about real-road lane perception.

The next controlled work is therefore rendering-domain isolation: preserve camera pose, intrinsics, map, timing, and controls, while changing one lane-appearance variable at a time. Each experiment must reuse the alignment fixture and compare lane probabilities, path horizon, and curvature before any control change is considered.

## Geometry and overlay controls

The following single-variable diagnostics used the same fixed map, seed, timing, and lane-semantic telemetry. The navigation-mark-off, 60-degree FOV, and +2-degree pitch reruns also retain the same three frame-aligned camera captures as the baseline. All are `valid/fail`; none are formal delay-matrix results.

| Condition | Straight left/right probability | Curve left/right probability | Curve path horizon | Lateral RMSE |
|---|---:|---:|---:|---:|
| 40° baseline | 0.0115 / 0.0223 | 0.0137 / 0.0273 | 4.41 m | 0.585 m |
| Navigation mark off | 0.0112 / 0.0225 | 0.0139 / 0.0281 | 4.37 m | 0.592 m |
| 60° FOV | 0.0057 / 0.0115 | 0.0057 / 0.0121 | 5.15 m | 0.527 m |
| −2° pitch | 0.0308 / 0.0209 | 0.0105 / 0.0105 | 1.79 m | 0.605 m |
| +2° pitch | 0.0304 / 0.0472 | 0.0219 / 0.0340 | 3.95 m | 0.553 m |

Disabling the MetaDrive navigation mark makes no material difference, and widening FOV lowers lane confidence further. Positive pitch increases reported lane confidence, demonstrating geometric sensitivity, but it shortens the predicted path and still produces near-zero curve response and a lane-departure failure. Negative pitch degrades curved-segment confidence and path horizon. These controls rule out a navigation overlay and a small fixed pitch/FOV adjustment as a complete remedy.

The RGB-to-NV12 transport is additionally guarded by deterministic unit fixtures for black, white, red, green, and blue frames. They fix the BT.601 limited-range luma and interleaved U/V output, so an RGB/BGR channel swap or limited-range conversion regression is not an open explanation for these results.

## Conclusion and boundary

The evidence is sufficient to classify the present baseline as a **pretrained-model versus MetaDrive image-domain mismatch**, not an OpenPilot control-gain or transport-delay defect. The exact visual features responsible cannot be inferred from simulator-only data, and no camera pose, gamma, FOV, or overlay setting tested here yields an acceptable model path or closed-loop result. The appropriate next development path is a separately labeled simulator-specialist perception/replay experiment, evaluated with this fixed harness; it must not be represented as a real-road openpilot improvement.
