# Progress

## Completed

- MetaDrive reference-lane ground truth, scenario manifest, lifecycle events, and non-blocking camera-delay telemetry.
- Formal `md_default_loop_lane0_v1` delay matrix: warm-up excluded, then 0/50/100/150 ms in three interleaved repetitions each.
- World-frame geometry diagnostics and simulator-only controller experiments, kept separate from the formal model-driven result.
- Unit tests, report generation, and public instrumentation branches.

## Formal matrix: 2026-08-28

Output root: `outputs/v0.2-formal-delay-matrix-20260828` (local, reproducible run artifact).

| Delay (ms) | Runs | Result | Median lateral RMSE (m) |
|---:|---:|---|---:|
| 0 | 3 | all `valid/fail`: lane departure | 0.664 |
| 50 | 3 | all `valid/fail`: lane departure | 0.666 |
| 100 | 3 | all `valid/fail`: lane departure | 0.664 |
| 150 | 3 | all `valid/fail`: lane departure | 0.675 |

All 12 formal runs met the data-validity contract. This is a repeatable failure of the current model-driven simulator baseline, not evidence of a passing driving system or a real-road conclusion. The generated `report.md` and `report.svg` remain local artifacts; the release packaging step will select a small reproducible sample rather than commit the full run data.

Camera transport audit across the formal runs found monotonic unique source frame IDs, capture-before-publish timestamps, and zero dropped road frames. Actual delay ranges were 17.65–40.15 ms for the 0 ms scheduler path, 50.34–61.14 ms for 50 ms, 100.29–106.66 ms for 100 ms, and 150.31–159.97 ms for 150 ms. The nonzero 0 ms range is publisher scheduling overhead and must be reported as actual delay rather than treated as an exact zero-latency path.

On 2026-08-29, the workstation was revalidated after updating the Windows NVIDIA driver to 616.56. Windows and WSL both exposed an RTX 4080 with CUDA UMD 13.4; tinygrad CUDA arithmetic, MetaDrive reset/step/close, OpenPilot static checks, and the sim-lab test suite succeeded. A fresh manifest smoke check recorded driver 616.56, the WSL kernel, MetaDrive 0.4.2.3, and clean repository state.

The runner now applies `configs/thresholds.yaml` during classification. In addition to lane departure and collision, measured absolute lateral error above 1.25 m is recorded as `lateral_error_threshold` and produces `valid/fail`. Reclassifying the frozen formal matrix preserves its validity and adds this expected KPI failure reason to every run.

The runner also treats an `openpilot_state.engaged: false` event after `run_state: MEASURE` as `valid/fail: disengagement`. The frozen formal event logs contain no such measurement-period disengagements.

Generated reports now aggregate valid failure reasons per delay condition. Frozen summaries retain the classifier reasons produced at their original run time; newly collected runs include the later KPI and disengagement reasons where applicable.

A clean post-driver smoke run on 2026-08-29 verified the complete current contract at 0 ms: driver 616.56 in the manifest, `camera_timestamps_valid: true`, zero drops, and `valid/fail` with `lane_departure` plus `lateral_error_threshold`. Its lateral RMSE was 0.658 m; it is a diagnostic confirmation, not an additional formal replicate.

The same day, a frame-2500 camera/telemetry alignment capture showed a visible upcoming left curve in the 40-degree road image before the current reference segment changed from straight to +0.008658 1/m at frame 2600. Model/control target curvature at the capture was only about +3.5e-06 1/m with -0.978 m lateral error. This reinforces the camera/model domain-gap hypothesis and is kept separate from formal results.

The instrumentation now records the model-predicted path horizon/end geometry, and only records its 20 m offset/heading if the path really reaches 20 m. The first run exposed an approximately 4.3 m path horizon, so clamped interpolation is explicitly avoided. This isolates a perception-path failure from a downstream curvature/planner failure without introducing a simulator-only steering controller. A fresh diagnostic run is the next verification step.

The next diagnostic also records `modelV2` validity, consumed camera frame age/drop percentage, execution time, and predicted terminal speed. These fields distinguish a stale/invalid inference stream from a valid but simulator-domain-mismatched prediction.

The first inference-health attempt exposed a bridge schema mistake (`modelV2.valid` does not exist); it is preserved as an invalid crash artifact. The instrumentation was corrected to record the owning SubMaster's `valid['modelV2']` status before retrying, rather than treating a message field as valid.

The corrected 0 ms inference-health run is a valid lane/KPI failure with `model_valid_coverage_ratio: 1.0`, frame age/drop maxima of 0, and 9.9 ms P95 inference time. Its path-horizon median is 4.91 m and terminal-speed median 2.74 m/s while actual mean speed is 4.55 m/s. Camera source IDs and `model_frame_id` both reached 643 with zero frame age, so the model is consuming current simulator frames; the short prediction is not caused by the delay queue or a stale-frame handoff.

The first opt-in frame-alignment fixture run generated three PNG/metadata pairs plus `camera_alignment.json` inside its run directory. It reproduced the expected 2400/2600/2800 join: reference curvature changed from 0 to +0.008658 1/m, while model curvature stayed near zero and path horizon stayed 4–5 m. The fixture is now the baseline evidence for future camera-input experiments.

Calibration RPY/status telemetry is now recorded before any calibration change. The next diagnostic must establish the observed warp state before proposing a calibration experiment.

The calibration diagnostic completed with `calibrated` status and zero RPY throughout the 2,895-sample measurement period. This removes calibration initialization/drift from the current failure hypotheses; the next evidence should quantify the captured image domain rather than tune camera pose or calibration.

The gamma sweep is complete: 0.8 slightly increased curve model curvature but remained orders of magnitude below reference curvature, while 1.2 decreased it and worsened RMSE. All conditions remained valid lane/KPI failures. The next camera/model evidence should inspect semantic rendering features, not apply more global brightness tuning.

The simulator dataset collection path now writes run-relative PNGs plus `dataset_manifest.jsonl` containing fixed camera metadata, reference-lane ground truth, and model state. Its first fixed-seed smoke collection produced 18 labeled images, including 5 curved-segment samples. This verifies the contract only; it is not enough data to train or evaluate a perception model.

The first three-seed collection matrix completed with 54 labeled images and 15 curved-segment samples. Seeds `20260827`, `20260828`, and `20260829` are preserved in each run-local scenario artifact. It establishes deterministic multi-run collection, not sufficient training coverage.

The split-aware rerun verified 36 train / 18 validation samples, with 10 / 5 curved-segment samples. This creates a leakage-free evaluation contract for the upcoming simulator-specialist model; the sample count remains smoke-scale only.

Dataset audit confirms curvature coverage only from 0 to +0.008658 1/m, with no negative-turn samples. Training is intentionally gated until route/map coverage is expanded; otherwise a model could appear to improve while only memorizing one loop direction.

The directional map smoke run verified `map_curve_direction: 1` produces negative curvature (`−0.008032 … 0 1/m`) with 370 negative-curve telemetry samples. The dataset collector now supports both curve directions; the next collection matrix should use that expansion before training.

Runtime camera-contract telemetry initially observed an `unknown/unknown` key before device/camera state initialization. It is now recorded as missing intrinsics rather than crashing the bridge; steady-state verification will distinguish this startup state from the actual modeld camera contract.

The lane-semantic audit is complete for the fixed frame-alignment fixture. In 2,550 straight and 635 curve telemetry rows, mean model left/right lane-line probabilities were only 0.0115/0.0223 and 0.0137/0.0273 respectively. Model validity remained 100% with zero frame age/drop, so this is not a stale-frame symptom. The current primary camera/model hypothesis is consequently MetaDrive lane-rendering domain mismatch, rather than camera transport, intrinsics, calibration, or controller gain. The next experiments isolate individual lane-appearance variables with the same capture fixture.

The rendering/geometry controls are now complete. Turning off MetaDrive's navigation mark had no material effect; 60-degree FOV lowered lane confidence; −2-degree pitch shortened the curved path; and +2-degree pitch raised lane confidence but retained a short path, near-zero curve response, and valid lane/KPI failure. RGB-to-NV12 primary-color fixtures also now guard the transport channel order. The camera/model diagnosis is therefore complete: the fixed pretrained model does not produce a usable path from this MetaDrive visual domain, and controller tuning must remain out of scope until a separately evaluated simulator-specialist perception/replay path exists.

The first simulator-specialist path is now implemented and evaluated separately. It trains a local RGB-only ridge replay artifact from reference-lane teacher labels, then actuates MetaDrive without route or ground-truth inputs. The fixed validation steering RMSE was 0.00715 normalized steer after two replay-aggregation rounds. Closed-loop lateral RMSE moved from 1.340 m on the initial artifact to 0.549 m on v2, compared with the pretrained baseline's 0.585 m; every specialist result remains `valid/fail` for lane departure/lateral error. This is a repeatable simulator-only experiment, not a passing system or a real-road result.

The next expert-data study established a stable pure-pursuit ground-truth teacher (1,200 camera frames, `valid/pass`, 0.0249 m lateral RMSE) and collected a held-out mixed straight/curve set. The camera-only ridge artifact trained from 54/54 train/held-out samples failed after 404 frames (1.029 m lateral RMSE); adding 32/32 train/held-out learner-visited DAgger samples extended this to 594 frames and 0.995 m. Both closed-loop results remain `valid/fail` due to lane departure/lateral error. The improvement is retained as controlled evidence, not promoted to a driving success.

The temporal RGB specialist then added a current-frame/0.2-second-difference artifact with camera-frame-gated runtime history. Its expert-only run failed after 196 frames (1.085 m); 62/62 temporal DAgger samples improved it to 883 frames and 0.491 m. A subsequent curve-state DAgger collection (122/122 samples, 154 curved) regressed slightly to 809 frames and 0.505 m. All are valid lane/KPI failures. The first temporal DAgger result is retained as the best specialist experiment; the curve artifact is retained as a non-adopted result.

The retained temporal DAgger artifact also failed both held-out appearance checks without retraining: gamma 0.8 reached 682 frames with 1.344 m lateral RMSE and gamma 1.2 reached 139 frames with 1.174 m. This is evidence of fixed-rendering overfit, so no simulator-specialist artifact is promoted beyond the gamma 1.0 experimental condition.

A training-only 0.8/1.0/1.2 gamma augmentation study then improved appearance robustness: gamma 0.8 reached 867 frames and 0.704 m RMSE; gamma 1.2 reached 873 frames and 0.668 m. Its gamma 1.0 result regressed to 858 frames and 0.685 m, versus 883/0.491 for the unaugmented artifact. All remain valid lane/KPI failures, so the augmentation result is retained as a robustness trade-off rather than a promoted driving model.

The bridge now exposes `map_track_size_m` while preserving the official 60 m default. A held-out 45 m tighter-loop run of the retained temporal DAgger artifact reached 747 frames and 0.528 m, again a valid lane/KPI failure. This is a controlled geometry variation, not a route-generalization claim.

Tighter-loop temporal expert data (124/124 samples, 54 curved) was combined with the retained 60 m temporal DAgger set. Its unseen 52 m intermediate-loop evaluation reached 311 frames and 0.980 m, a valid lane/KPI failure. This negative interpolation result means the multi-geometry artifact is not adopted.

Three independent process-to-collection repeats of the retained 60 m temporal DAgger held-out contract are now complete. All were `valid/fail` for the same lane/lateral criteria without collision or camera drops. Lateral RMSE was 0.48694–0.49146 m (mean 0.48857 m, sample standard deviation 0.00251 m); heading RMSE was 0.06336–0.06371 rad. This is repeatability evidence for the fixed-condition failure, not a driving success or a generalization result.

The retained temporal artifact was then evaluated unchanged at a held-out 4.0 m/s target speed, versus its 3.0 m/s collection condition. It remained `valid/fail`, ending after 653 camera frames with 0.49527 m lateral RMSE and no collision/drop. Since the fixed 3.0 m/s repeats reached 882–883 frames, this is controlled speed/dynamics sensitivity evidence; it does not promote the artifact or establish road capability.

The complementary 2.0 m/s held-out contract was repeated three times. All reached the full 1,200 camera-frame measurement limit as `valid/pass`, without lane departure, collision, or camera drops; lateral RMSE was 0.33269–0.33285 m (mean 0.33274 m, sample standard deviation 0.000095 m). This is a repeatable pass only for the exact 60 m loop/seed/camera/0 ms/2.0 m/s simulator contract. It does not change openpilot, resolve the 3.0/4.0 m/s failures, or establish generalization or real-road capability.

The same 2.0 m/s contract then completed the standard 12-run interleaved 0/50/100/150 ms camera transport-delay matrix. Every formal run was `valid/pass` with all 1,200 camera frames and no drop, collision, or lane departure. Median lateral RMSE was 0.33304, 0.33290, 0.33316, and 0.33276 m respectively; recorded actual-delay medians were 23.48, 50.57, 100.66, and 150.63 ms. This validates fault delivery only in the documented narrow specialist contract, not the model-driven baseline or real driving.

The 2.0 m/s artifact was also evaluated unchanged on the 45 m tighter loop. It remained `valid/fail`, ending after 1,145 camera frames with lane departure and 0.54032 m lateral RMSE, while retaining valid timestamps and no collision/drop. The low-speed pass is consequently constrained to the fixed 60 m loop and is not route-geometry generalization.

Changing only camera gamma to 0.8 at the same 2.0 m/s caused a `valid/fail` after 1,030 camera frames with lane departure and 1.34232 m lateral RMSE. The low-speed pass is therefore also appearance-sensitive and remains a fixed-rendering result.

Targeted v0.6 data expansion then corrected the low-speed gamma collection schedule after its first 244-sample run contained no curves. The curve-targeted rerun yielded 160 gamma-0.8 curve samples (80/80 train/validation) with both turn signs. Combined temporal expert/DAgger/gamma data produced a new artifact that repeated `valid/pass` three times on the gamma-0.8, 2.0 m/s held-out contract (1,200 frames each; RMSE mean 0.28765 m, sample standard deviation 0.00027 m). This is a narrow appearance-contract improvement, not a general driving claim.

That v0.6 gamma artifact also completed the full 12-run interleaved 0/50/100/150 ms delay matrix at gamma 0.8 and 2.0 m/s: every formal run was `valid/pass` with no lane departure, collision, or camera drop. Median RMSE by target delay was 0.28691, 0.28774, 0.28697, and 0.28758 m. The result is limited to the same fixed simulator appearance and speed contract.

An analogous telemetry-targeted 45 m low-speed collection yielded 272 curve samples (136/136 train/validation) and was combined into a gamma+tight artifact. Its 45 m held-out replay reached 1,200 frames and improved RMSE to 0.50021 m, but remained `valid/fail` for lane departure/lateral-error. Geometry generalization is therefore still not achieved.

A second 45 m DAgger collection captured 272 learner-visited curve samples (136/136 train/validation). The resulting gamma+tight+DAgger temporal artifact trained on 522/522 temporal train/validation pairs. Three independent fixed 45 m/2.0 m/s held-out repeats were all `valid/pass`, completed 1,200 frames, and had no lane departure, collision, or camera drop; lateral RMSE was 0.40798–0.41767 m (mean 0.41224 m; population standard deviation 0.00404 m). A separate 60 m/gamma-0.8 regression run was also `valid/pass` but had 0.54819 m RMSE versus the gamma-curve artifact's 0.28765 m mean. The new artifact is therefore scoped to the fixed tight-loop result and does not replace the gamma-curve artifact or establish geometry/appearance generalization.

A 52 m intermediate-loop probe, not used in the 45 m collection, was then repeated three times. All were `valid/pass` at 1,200 frames with no lane departure, collision, or camera drop; lateral RMSE was 0.48670–0.49496 m (mean 0.49060 m; population standard deviation 0.00339 m). This adds a second deterministic geometry point, but does not justify a generalization claim.

The fixed 45 m tight-DAgger artifact also completed the excluded-warm-up, interleaved 12-run 0/50/100/150 ms transport-delay matrix. Every formal run was `valid/pass` at 1,200 frames without lane departure, collision, or camera drop. Median RMSE by target delay was 0.42030, 0.42123, 0.42140, and 0.42123 m; actual-delay medians were 24.57, 50.63, 100.69, and 150.76 ms. This validates the delay injector under the narrow fixed tight-loop contract only.

At the same 45 m/2.0 m/s contract, changing only camera gamma from 1.0 to 1.2 completed three identical `valid/pass` runs at 1,200 frames with 0.39387 m lateral RMSE, no departure/collision, and no frame drop. This is a deterministic synthetic-rendering observation, not real-camera robustness.

The corresponding 45 m/gamma-0.8 single probe was also `valid/pass` at 1,200 frames, with no departure/collision/drop and 0.46903 m lateral RMSE. It is preserved as a one-run geometry/rendering interaction measurement, not an appearance-generalization result.

v0.2 adds the opt-in `openpilot_serpentine_v1` map profile with alternating left/right curves while preserving the v0.1 default loop unchanged. The first three 60 m/2.0 m/s serpentine repeats were all `valid/pass` at 1,200 frames with no departure/collision/drop; RMSE was 0.44456–0.44550 m (mean 0.44492 m; population standard deviation 0.00042 m). This is a second versioned synthetic topology, not a general route or road claim.

The serpentine contract then completed the excluded-warm-up, interleaved 12-run 0/50/100/150 ms delay matrix: every formal run was `valid/pass` at 1,200 frames with no departure/collision/drop. Median RMSE by target delay was 0.44571, 0.44598, 0.44598, and 0.44564 m; actual-delay medians were 24.48, 50.59, 100.70, and 150.71 ms.

The mirrored serpentine (`map_curve_direction: 0`) also repeated 3 × `valid/pass` at 0 ms with no departure/collision/drop; RMSE was 0.23646–0.23724 m (mean 0.23674 m; population standard deviation 0.00035 m). This is a second fixed direction contract, not general direction robustness.

The mirrored contract then completed the excluded-warm-up 12-run delay matrix. Every 0/50/100/150 ms formal run was `valid/pass` at 1,200 frames with no departure/collision/drop; median RMSE was 0.23643, 0.23651, 0.23654, and 0.23672 m.

The opt-in low-traffic serpentine probe now records MetaDrive's traffic-manager actor count on every telemetry row. After preserving the original actor-spawn configuration failure, the corrected fixed-seed `traffic_density: 0.03` contract completed three 0 ms repeats as `valid/pass`: all reached 1,200 frames with no ego collision, lane departure, or camera drop; lateral RMSE was 0.44683–0.44747 m (mean 0.44712 m, population standard deviation 0.00027 m), and the recorded traffic count was 3.34–3.35 on average (maximum 4). This establishes only a deterministic, low-density synthetic-traffic lane-following probe. It neither tests nor claims traffic perception, yielding, braking for actors, or obstacle avoidance.

The same low-traffic contract completed its excluded-warm-up, interleaved 12-run 0/50/100/150 ms delay matrix. All formal runs were `valid/pass` at 1,200 frames with no ego collision, lane departure, or camera drop. Median lateral RMSE was 0.44696, 0.44734, 0.44628, and 0.44710 m; actual-delay medians were 24.18, 50.58, 100.65, and 150.66 ms. Every formal run recorded a maximum of four traffic actors. This validates the non-blocking delay delivery only for the declared fixed low-density synthetic-traffic contract, not traffic interaction behavior.

The traffic scenario now declares `min_traffic_vehicle_count: 1` as a validity contract. A run with no measured actor present is classified `invalid/not_evaluated: traffic_actor_coverage`, rather than being reported as a traffic-present pass. A fresh contract run recorded 3.343 mean and 4 maximum actors and remained `valid/pass`.

Active-actor proximity telemetry then showed why this must not be treated as an interaction test: the 0 ms probe had at most one active actor, 0.656 mean active actors, and a 239.57 m minimum ego-to-active-actor distance. The actor-presence contract is working, but this route/spawn layout provides no meaningful encounter, following, yielding, braking, or avoidance exposure. Any traffic-interaction evaluation requires a separately versioned spawn/route design and KPI contract.

The separate respawn-traffic probe provides the first controlled proximity exposure: fixed `traffic_density: 0.03`, `traffic_mode: respawn`, and `max_traffic_ego_nearest_distance_m: 30` produced `valid/pass` with two active actors throughout and a 28.00 m closest distance. This confirms only that the versioned route reaches the declared proximity boundary; it still contains no actor-following, braking, yielding, collision-avoidance, or traffic-policy KPI.

The follow-up closing-speed/TTC probe preserved that boundary: closest distance was 27.87 m, maximum closing speed was −2.60 m/s (separating), and no positive-TTC sample existed. The respawn layout therefore has proximity but no closing encounter. A future interaction scenario must deliberately specify relative spawn position and speed before any longitudinal-control or avoidance result is evaluated.

The new fixed static-lead fixture provides a deliberate collision encounter without feeding actor ground truth to control. The lead starts 20 m ahead on the reference lane; its first 0 ms run was `valid/fail: collision`, with a 4.47 m closest distance, 2.00 m/s maximum closing speed, and 2.29 s minimum positive TTC. It is a longitudinal-control baseline failure, not evidence of following or avoidance capability.

Camera diagnostics now join each saved RGB frame to the measured traffic actor count, nearest distance, closing speed, TTC, and collision state. The static-lead fixture captures the approach at 2, 4, and 8 s: distance/TTC fall from 18.17 m/11.61 s to 14.63 m/7.69 s and 6.76 m/3.40 s before the collision-state capture at 12 s. This is a traceable local camera-to-ground-truth alignment artifact only. Crucially, the installed MetaDrive minimal assets do not contain vehicle meshes, so the physics lead is not visible in these RGB frames. The labels remain excluded from the runtime control path; this cannot train or evaluate lead perception.

The separate static-lead dataset smoke now writes 10 run-relative RGB samples to `dataset_manifest.jsonl`; all carry traffic labels, the sampled minimum distance is 4.52 m, the minimum sampled positive TTC is 3.40 s, and two samples carry collision state. `simlab.runner audit` reports this label coverage automatically. The run remains `valid/fail: collision`, and this small fixed encounter is retained only as telemetry-to-camera alignment evidence, not lead-perception training or driving capability.

The follow-up three-seed static-lead matrix (`20260831`, `20260901`, held-out `20260902`) completed with three `valid/fail: collision` outcomes. It yielded 30 labeled images split 20 train / 10 validation; all were traffic-labeled, 13 carried collision state, and sampled minima were 3.66 m distance and 3.37 s positive TTC. This repeats the encounter and data-provenance contract, but the lead mesh is absent from the RGB frames; it is not lead-perception data, regardless of sample count.

An opt-in `lead_vehicle.visual_proxy: box` attaches the minimal asset package's `box.bam` to the non-rendered static physics lead. The first visible-obstacle smoke confirmed the black rectangle in the 2 s and 8 s RGB captures and wrote ten traffic-labeled samples. It was `valid/fail` for lane departure, collision, and lateral-error KPI. This is a synthetic box-obstacle alignment path only, not vehicle perception, obstacle avoidance, or a trained control result.

The three-seed visible-box matrix completed with three `valid/fail` outcomes for lane departure and collision. It yielded 30 RGB samples split 20 train / 10 held-out validation; all carry traffic labels, seven carry collision state, and the sampled minima are 4.52 m distance and 3.37 s positive TTC. This repeats a fixed black-box obstacle failure and its data contract only; it does not demonstrate detection or avoidance.

Distance smoke runs at 10 m and 30 m confirmed the same proxy is visible at 1 s and 2 s respectively, providing three fixed image-scale strata (10/20/30 m). Both were `valid/fail` for lane departure, collision, and lateral-error KPI. They establish only deterministic rendering and telemetry coverage across those starting gaps; no classifier, range estimator, braking, or avoidance controller has been trained.

The bbox-enabled 20 m three-seed matrix then completed with 30/30 projected-box-labeled RGB samples, a 20/10 train/held-out split, and 21,673–439,333 px² label areas. Every run remained `valid/fail: collision` (two also lane-departed). This completes the synthetic box image/geometry label contract while retaining the driving failure; no detector or avoidance model has been added.

The optional full MetaDrive 0.4.2.3 asset archive was then verified to render its Ferra vehicle mesh in road RGB. The first 20 m lead smoke produced a visible red vehicle but collided, as expected because no perception or avoidance control is connected. A subsequent full-asset attempt ended without a summary during a WSL `dxg`/unclean-restart incident. The active test environment was restored to minimal assets and the full archive was retained separately; rendered-vehicle results remain an environment smoke boundary, while the box proxy remains the reproducible visible-object path.

The runner now preserves watchdog, unexpected bridge exit, and Python-level runner exceptions as `invalid/not_evaluated` rather than allowing a simultaneous collision to mask an infrastructure failure. This is a harness integrity change; it does not alter previously collected results or convert the rendered-vehicle smoke into a formal evaluation.

The explicit 400-frame rendered-lead smoke subsequently completed with a visible Ferra vehicle, no lane departure, and `valid/fail: collision` (0.35976 m lateral RMSE). Its manifest records full asset version and mesh hash. The separate baseline rerun completed too, but remained `valid/fail: lane_departure, lateral_error_threshold`; it is retained as post-experiment recovery evidence, not a new performance result.

## Next

1. Treat a new route topology as a versioned post-v0.1 bridge/config extension: add its deterministic asset, spawn/pose validation, manifest identity, and tests before using it for held-out evidence. The current v0.1 contract deliberately supports only `openpilot_default_loop_v1` with size/direction variants.
2. Keep the pretrained baseline frozen; do not tune simulator-only controllers as an openpilot claim.
3. Maintain the sample results, reproducibility commands, limitations, and CI evidence for the portfolio release.
4. Keep any traffic experiment opt-in and versioned, with actor-count telemetry and separate interaction KPIs before making an avoidance-related claim.
