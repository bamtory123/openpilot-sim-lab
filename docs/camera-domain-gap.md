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

An explicit zero-pose diagnostic (`camera_position_m: [0, 0, 1.22]`, `camera_hpr_deg: [0, 0, 0]`) completed with the same valid lane-departure/KPI failure contract and zero transport drops. Symmetric ±2 degree pitch diagnostics were then isolated outside the formal matrix.

The pitch sweep showed sensitivity but no solution: at 0°, −2°, and +2°, curve-segment model-target absolute means were 0.00000495, 0.00006109, and 0.00001110 1/m respectively, versus +0.008658 1/m reference curvature. Lateral RMSE was 0.633, 0.665, and 0.616 m; all runs remained valid lane/KPI failures. A single −4° exploratory point is retained only to determine whether the negative-pitch response is monotonic.

The −4° point was a valid failure before reaching the curve (simulation frame 835; no curved-segment telemetry), with high speed variance and 2.26 deg/s applied steering-rate RMS. It is not comparable to the other pitch points and ends the pitch sweep: no pose is promoted from these diagnostics. Subsequent work should inspect model path output rather than continue uncalibrated camera-pose tuning.

## Model inference health

The 0 ms inference-health diagnostic recorded `model_valid` on every measured sample, zero model frame age and drop percentage, and a 9.9 ms P95 model execution time. The latest camera source ID and `model_frame_id` both reached 643. The model therefore consumed current delayed-queue output, but its median predicted path horizon was only 4.91 m and predicted terminal speed 2.74 m/s while actual vehicle speed averaged 4.55 m/s. This rules out camera queue staleness as the explanation for the near-zero lateral response; it does not establish which image-domain or model-input contract mismatch causes the short prediction.

The calibration-telemetry retry recorded `calibrated` on all 2,895 measurement samples with RPY exactly `[0, 0, 0]`. The modeld image warp is therefore initialized and stable; no calibration adjustment is justified by the current evidence.

Runtime camera-contract telemetry also confirmed all 2,875 measurement samples used modeld key `pc/unknown` with 1928×1208, 2648 px narrow-road intrinsics. This verifies the actual modeld selection, not merely the intended simulator configuration. Resolution, focal-length, calibration state, queue freshness, and model frame contract are now ruled out as primary causes of the short path output.

An opt-in gamma 0.8 camera transform then altered only pixel luminance before NV12 conversion while map, pose, intrinsics, delay, and controls remained fixed. It was a domain-gap sensitivity diagnostic, never a formal-baseline replacement.

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

## Completed controlled sequence

The following sequence is complete and produced the rendering-domain conclusion recorded below:

1. Captured matched frame sets at fixed map positions before and during the curve, with frame metadata and telemetry joins.
2. Inspected model path/curvature output against those frame sets without changing controller gains.
3. Tested one documented camera variable at a time while preserving the 40-degree formal baseline unchanged.

No further camera-pose, gamma, FOV, or overlay tuning is planned for the pretrained baseline under this contract. Any future perception work must remain separately labeled as a simulator-specialist experiment.

## Minimal-asset traffic limitation

The installed MetaDrive `0.4.2.3` minimal asset package contains road assets but no vehicle meshes. A deterministic static physics lead can therefore generate collision, distance, closing-speed, and TTC telemetry while remaining absent from the RGB road camera. Enabling vehicle rendering raises a missing `models/ferra/right_tire_front.gltf` error and terminates the bridge. Static-lead runs are consequently retained only for simulator-physics/telemetry contracts; no RGB lead-perception dataset, training, or evaluation claim is permitted until a versioned asset package with a renderable vehicle is installed and separately verified. A scenario that declares `diagnostics.require_visible_lead: true` is now rejected at preflight when that mesh is unavailable.

The minimal package's `box.bam` is separately usable as an explicitly declared black static-obstacle proxy. It makes an object visible in the RGB camera, but does not reduce the vehicle-mesh limitation: box-proxy results are synthetic obstacle-alignment diagnostics, not vehicle or road-object perception evidence.

## Rendered-vehicle asset smoke boundary

MetaDrive 0.4.2.3's full upstream asset archive contains the Ferra vehicle mesh absent from the minimal asset package. The harness therefore supports an explicit `lead_vehicle.render_vehicle: true` smoke contract and records the asset version, vehicle-mesh availability, and vehicle-mesh SHA-256 in every manifest. It is deliberately opt-in so the established minimal-asset experiments are unchanged.

On this Windows/WSL host, the first full-asset smoke rendered the red Ferra lead vehicle in the road RGB capture. A subsequent attempt left no `summary.json` and coincided with WSL `dxg` ioctl errors and an unclean journal restart. The full archive is retained outside the source tree for investigation, but the active environment has been restored to the known-stable minimal assets. Consequently the rendered-vehicle scenario is currently a guarded environment smoke only, not a release artifact or a repeatable test claim.

A shorter 400-camera-frame rerun did complete and recorded the full asset provenance: MetaDrive asset version `0.4.2.3`, Ferra mesh SHA-256 `6f99d045…5182e79e`. It was `valid/fail: collision` with no lane departure (0.360 m lateral RMSE). The collision is expected: the lead is rendered and physically static, but no perception input, distance estimation, longitudinal response, or avoidance policy consumes it. This confirms only camera visibility plus physics alignment for one fixed synthetic vehicle asset.

## Gamma sensitivity result

With every camera/model contract field fixed, gamma 0.8 increased curve-segment mean absolute model curvature from about `4.7e-06` to `1.09e-05 1/m`; gamma 1.2 produced `4.05e-06 1/m`. Required reference curvature is about `8.66e-03 1/m`. All three gamma conditions remained valid lane/KPI failures with a roughly 4–5 m model path horizon. Global luminance affects output slightly but is not the primary camera/model mismatch.

## Lane-semantic telemetry result

The frame-alignment fixture was repeated after adding read-only `modelV2` lane-line telemetry. The infrastructure result remained `valid/fail` (lane departure and lateral-error KPI), while model validity remained 100%, frame age/drop remained zero, and inference P95 was 9.97 ms. This preserves the earlier conclusion that the model receives current frames.

| Segment | Samples | Left lane probability mean | Right lane probability mean | Model path horizon mean |
|---|---:|---:|---:|---:|
| Straight (`|reference curvature| < 0.001`) | 2,550 | 0.0115 | 0.0223 | 5.03 m |
| Curve (`|reference curvature| >= 0.001`) | 635 | 0.0137 | 0.0273 | 4.41 m |

The lane-line probabilities are low in both segments and do not rise when the simulator enters the known curve. The corresponding near-field lane positions remain populated, so an empty Cap'n Proto field is not being misread as a low score. Together with the short 4–5 m path and near-zero curvature, this is strong simulator-domain evidence that the pretrained model does not assign meaningful lane confidence to the current MetaDrive rendering. It is not evidence about real-road lane perception.

The completed rendering-domain isolation sequence preserved camera pose, intrinsics, map, timing, and controls while changing one lane-appearance variable at a time. Each experiment reused the alignment fixture and compared lane probabilities, path horizon, and curvature before any control change; the resulting controls are recorded below.

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

## Official real-camera replay control

The pinned pretrained model now has a separate 60-frame control using OpenPilot's own `model_replay.py` route. It completed 60/60 `modelV2` and 60/60 `driverStateV2` outputs with zero reported model frame age/drop. Mean left/right lane probabilities were about `0.923/0.910`, and mean path horizon was about `244.45 m`. The retained MetaDrive lane-semantic run reported about `0.012/0.024` and `4.73 m` over its measurement samples.

These are different scenes, so their ratio is not an accuracy metric and cannot identify one causal pixel feature. The result does establish a strong control: the pinned model/runtime is capable of producing confident, long-horizon output on the upstream real-camera route, while the MetaDrive transport is fresh but produces low-confidence, short-horizon output. The leading explanation is therefore the simulator input domain rather than queue staleness, first-order intrinsics, or a missing model process.

The replay's host timing is intentionally separate. It is functionally complete but does not meet upstream device-oriented execution limits on this WSL host. See [real-camera model replay](real-camera-model-replay.md) and its [public-safe comparison](../examples/v0.2-real-camera-model-replay/README.md).

## Reference-bound color-match diagnostic

The harness now has a bounded `camera_color_affine` input contract for a new diagnostic only. It applies a per-channel RGB gain and bias after the existing optional gamma transform, before NV12 conversion. Values are explicit and bounded (`gain_rgb` 0.5–2.0; `bias_rgb` −64–64); the default identity `[1, 1, 1]` / `[0, 0, 0]` leaves every established v0.1 and v0.2 scenario unchanged.

`scripts/audit_camera_domain.py` accepts matched simulator and road-camera reference frames, hashes every input, computes lower-half RGB/luma/saturation/edge statistics, and produces a moment-matching affine proposal. This proposal is not a lane-semantic metric, a perception calibration, or a driving candidate. It may be copied into the separate `md_default_loop_lane0_color_match_diagnostic_v2` scenario only after the reference frames' camera geometry and provenance are documented.

No suitable real-road reference frame is retained in this workspace. Consequently the first tool smoke uses an identical MetaDrive frame as both inputs and returns exactly the identity transform. The next legitimate experiment requires a versioned, permission-cleared road-camera reference set; it must compare the identity and derived-affine conditions with the fixed frame-alignment fixture before any closed-loop candidate claim.

`scripts/run_pretrained_camera_color_evaluation.py` enforces that comparison. It source-hashes the audit, refuses an identity proposal as `retain_no_change_audit`, and otherwise runs identity baseline plus the derived affine candidate three times each on the fixed default loop and held-out serpentine contract. All six candidate runs must be `valid/pass`; only then is a delay matrix eligible. This does not alter the frozen v0.1 result.

## Conclusion and boundary

The evidence is sufficient to classify the present baseline as a **pretrained-model versus MetaDrive input-domain mismatch**, not an OpenPilot control-gain or transport-delay defect. The exact visual features responsible cannot be inferred without matched-scene data, and no camera pose, gamma, FOV, or overlay setting tested here yields an acceptable model path or closed-loop result. MetaDrive should remain the integration/fault/actuator environment; pretrained perception changes should use real-camera replay and a later permission-cleared matched-scene protocol. Simulator-specialist experiments remain a separate positive-control track and must not be represented as real-road OpenPilot improvement.

The follow-up [source-aligned model overlay](model-overlay-diagnostic.md) now verifies this visually using exact camera source IDs. A realistic 3.7 m lane-width candidate reduced rather than improved lane confidence. Supplying a separate 120-degree wide stream increased early path horizon but produced a severe false-left path, 106.96° steering-command RMS, and only 3.29 s of measured active time. Both candidates are rejected; neither changes the frozen baseline.

An FHWA-dimensioned 3.048 m line / 9.144 m gap diagnostic then produced a small relative lane-confidence increase but no path-horizon or closed-loop improvement. It remains an opt-in negative diagnostic and confirms that dash cadence alone does not close the domain gap.

Darkening only the asphalt texture to 75% intensity was also ineffective. Captured lower-centre luma decreased from 96.30 to 81.53, but both lane confidence and path horizon fell and the early-departure validity failure was unchanged. This separates lane/road contrast from the previously rejected full-image gamma adjustment and rejects both as complete remedies.
