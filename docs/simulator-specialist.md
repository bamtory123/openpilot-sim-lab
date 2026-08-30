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
