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

The next iteration should add genuinely diverse, stable expert demonstrations and held-out route/appearance conditions before increasing model capacity. A CNN or a controller change without that evidence would only risk fitting this one synthetic loop. Any future specialist result must retain the same manifest, camera, validity, and outcome contracts used here.
