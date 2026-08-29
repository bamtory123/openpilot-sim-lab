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
