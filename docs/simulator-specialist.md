# Simulator-specialist replay

This is an opt-in MetaDrive-only perception/replay experiment. It does not replace openpilot's pretrained model, modify openpilot steering gains, or make a real-road claim.

## Data and target

`md_default_loop_lane0_dataset_collection_v1` captures the road RGB frames and records a reference-lane pure-pursuit teacher steering value. The teacher uses MetaDrive ground truth **only to create labels**. A run-relative `specialist_manifest.jsonl` joins each image to its teacher target and train/validation split.

The initial collection contains 114 images: 75 train, 39 validation, 38 curved samples, and both positive and negative reference curvature. Two replay data-aggregation runs add 42 specialist-induced train-state images. The v2 artifact therefore trains on 117 train and 39 fixed validation images. This is a fixed-simulator repeatability set, not independent route or road generalization.

## Artifact and inference boundary

`simlab train-specialist --dataset-root outputs --artifact models/<name>.npz` trains a deterministic ridge regressor over a 24×32 grayscale sample of the RGB road image. The local `models/` directory is ignored by Git because artifacts are generated from local run data.

At replay time, `SpecialistReplay` loads only that artifact and the latest road RGB frame. It predicts a clipped normalized steering value and uses the declared speed target. It has no reference-lane, lateral-error, heading-error, route-progress, or teacher input. Telemetry marks this path as `simulator_control_mode: specialist_replay` and records the predicted normalized steering command.

## Reproduce

```bash
cd /home/hyunsung/src/openpilot-sim-lab
export OPENPILOT_ROOT=/home/hyunsung/src/openpilot

# Collect and rebuild image/teacher joins when needed.
$OPENPILOT_ROOT/.venv/bin/python3 -m simlab.runner collect \
  --scenario configs/scenarios/md_default_loop_lane0_dataset_collection_v1.yaml \
  --outputs outputs/specialist-dataset
uv run simlab rebuild-specialist-manifests --outputs outputs/specialist-dataset

# Train a local artifact, then evaluate it through the normal harness.
uv run simlab train-specialist --dataset-root outputs --artifact models/specialist.npz
$OPENPILOT_ROOT/.venv/bin/python3 -m simlab.runner run \
  --scenario configs/scenarios/md_default_loop_lane0_specialist_replay_dagger_v2_diagnostic_v1.yaml \
  --outputs outputs/specialist-evaluation
```

The evaluation scenario references the local artifact name in `specialist_replay.artifact_path`; change it only after retraining. Preflight rejects a missing artifact.

## Initial results

All comparisons use the fixed 0 ms loop scenario and the existing validity/KPI contract.

| Controller path | Lateral RMSE | Validity/outcome |
|---|---:|---|
| Pretrained openpilot baseline | 0.585 m | `valid/fail` |
| Initial RGB ridge replay | 1.340 m | `valid/fail` |
| After first replay aggregation | 0.675 m | `valid/fail` |
| After second replay aggregation | 0.549 m | `valid/fail` |

The v2 validation steering RMSE is 0.00715 normalized steer. Closed-loop v2 is still a lane-departure and lateral-error failure, despite its modest RMSE improvement. That failure is retained as the result: no specialist path is promoted as a driving success.

## Next evidence needed

The initial expert-only curve artifact reached a held-out lane departure after 219 camera frames (lateral RMSE 1.182 m). Adding fixed-route straight and curve expert samples improved this to 404 frames and 1.029 m, but remained `valid/fail`. A subsequent DAgger collection added 64 learner-visited straight-state samples to the 108 mixed expert samples. Its held-out replay reached 594 frames with 0.995 m lateral RMSE and 0.0301 rad heading RMSE, but also remained `valid/fail` because of lane departure.

These are controlled improvements, not a driving success or a real-road claim. The next evidence should be temporally contextual camera input and more varied held-out route/appearance conditions; increasing model capacity or changing a controller before that evidence would only risk fitting this fixed synthetic loop. Any future specialist result must retain the same manifest, camera, validity, and outcome contracts used here.

## Temporal follow-up

The temporal experiment uses the current RGB image and its 0.2-second image difference only. Runtime history advances only when a new 20 Hz camera frame arrives; it does not use route, teacher, vehicle-state, or ground-truth inputs. The fixed temporal expert set contains 120/120 train/held-out samples and 116 curved samples. A first temporal replay failed after 196 frames (1.085 m lateral RMSE). Adding 62/62 learner-visited temporal DAgger samples improved the same held-out run to 883 frames and 0.491 m. A further 122/122 curve-state DAgger collection produced 809 frames and 0.505 m, so it is not adopted as an improvement.

Every temporal result remains `valid/fail` for lane departure and lateral error. The evidence supports time-aligned data and the first DAgger correction, but does not support claiming reliable curve driving. The next useful experiment is held-out appearance/route variation, not another fixed-loop tuning round.

## Held-out appearance check

The retained temporal+DAgger artifact was evaluated without retraining on the same held-out seed/direction under gamma 0.8 and 1.2 camera rendering. Both are valid failures: gamma 0.8 reached 682 frames with 1.344 m lateral RMSE, while gamma 1.2 reached 139 frames with 1.174 m. The gamma 1.0 fixed-rendering result (883 frames, 0.491 m) remains the best local result, but these appearance failures show that it does not generalize across even small synthetic rendering changes. It must remain a simulator-only fixed-condition experiment.

Training-only gamma augmentation (0.8/1.0/1.2) was then applied to temporal pairs while leaving held-out validation unaugmented. It trades nominal error for appearance robustness: gamma 1.0 reached 858 frames with 0.685 m RMSE, gamma 0.8 reached 867 frames with 0.704 m, and gamma 1.2 reached 873 frames with 0.668 m. All three are still `valid/fail`; this is evidence of a robustness trade-off, not a passing controller or a general driving claim.

## Held-out route geometry check

`md_tight_loop_lane0_temporal_dagger_heldout_v1` keeps the same lane count, lane width, seed, direction, camera, and KPI contract, but changes the deterministic loop track size from 60 m to 45 m. This produces tighter curves without changing the official `md_default_loop_lane0_v1` baseline. The retained unaugmented temporal+DAgger artifact reached 747 frames with 0.528 m RMSE and remained `valid/fail`. This is route-geometry evidence only; it does not establish route generalization.

Stable temporal expert data was then collected at 45 m (124/124 train/held-out samples; 54 curved samples) and combined with the retained 60 m temporal DAgger set. The resulting multi-geometry artifact was evaluated at an unseen 52 m track size: it reached 311 frames with 0.980 m RMSE and remained `valid/fail`. The result is retained as negative interpolation evidence; the multi-geometry artifact is not adopted.

## Fixed-condition repeatability check

Three fresh process-to-collection repeats of the retained temporal+DAgger artifact used the unchanged 60 m held-out scenario, seed, camera contract, 0 ms transport-delay path, and artifact. All three completed as `valid/fail` for the same lane-departure and lateral-error criteria, with no collisions, no camera drops, and valid timestamps. Lateral RMSE was 0.48694, 0.48731, and 0.49146 m (mean 0.48857 m; sample standard deviation 0.00251 m); heading RMSE was 0.06336, 0.06336, and 0.06371 rad. Published camera-frame counts were 882, 883, and 883, and delay P95 ranged from 30.70 to 31.07 ms.

The repeat roots are `outputs/v0.5-temporal-dagger-repeat-{1,2,3}-20260830`. This establishes repeatability of the fixed-condition **failure** and its measured telemetry, not a passing controller, route generalization, or real-road capability.

## Held-out speed check

The speed scenarios change only the simulator-specialist target speed; the map, seed, camera, fault path, and retained artifact are unchanged. The artifact was collected at 3.0 m/s.

| Target speed | Repeats | Result | Lateral RMSE | Camera frames | Interpretation |
|---:|---:|---|---:|---:|---|
| 2.0 m/s | 3 | 3 × `valid/pass` | 0.33269–0.33285 m (mean 0.33274 m) | 1,200 each | A repeatable pass only for this exact simulator contract. |
| 3.0 m/s | 3 | 3 × `valid/fail` | 0.48694–0.49146 m | 882–883 | Fixed-condition failure baseline. |
| 4.0 m/s | 1 | `valid/fail` | 0.49527 m | 653 | Higher-speed sensitivity evidence; a single run. |

The 2.0 m/s repeats have a lateral-RMSE sample standard deviation of 0.000095 m, no lane departures, collisions, or camera drops, and valid timestamps. This does not modify openpilot or establish a usable road controller: it is a camera-only simulator artifact satisfying this particular 60 m loop, 2.0 m/s, 0 ms condition. The 4.0 m/s failure and existing appearance/geometry failures show that the artifact is still speed/dynamics- and domain-sensitive; it is not promoted beyond the documented contract.

## 2.0 m/s transport-delay matrix

The retained artifact was also run through the standard excluded-warm-up, interleaved 12-run delay matrix at 2.0 m/s. All formal runs were `valid/pass`, completed all 1,200 camera frames, and had no lane departure, collision, or camera drop. The generated report is local at `outputs/v0.5-temporal-dagger-speed2-delay-matrix-20260830/report.md`.

| Target delay | Formal repeats | Median lateral RMSE | Actual-delay median across repeats |
|---:|---:|---:|---:|
| 0 ms | 3 × `valid/pass` | 0.33304 m | 23.48 ms |
| 50 ms | 3 × `valid/pass` | 0.33290 m | 50.57 ms |
| 100 ms | 3 × `valid/pass` | 0.33316 m | 100.66 ms |
| 150 ms | 3 × `valid/pass` | 0.33276 m | 150.63 ms |

This confirms the non-blocking injector's recorded delay under the limited 2.0 m/s contract. It does not overturn the model-driven baseline, 3.0/4.0 m/s specialist failures, route/appearance limits, or any real-road limitation.
