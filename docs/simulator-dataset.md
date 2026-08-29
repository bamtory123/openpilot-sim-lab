# Simulator dataset collection

The dataset collector is an opt-in diagnostic, separate from the formal delay study. Each sample records a run-relative road-camera PNG plus its capture metadata and route/model labels in `dataset_manifest.jsonl`.

Run one fixed collection:

```bash
cd /home/hyunsung/src/openpilot-sim-lab
OPENPILOT_ROOT=/home/hyunsung/src/openpilot \
  /home/hyunsung/src/openpilot/.venv/bin/python3 -m simlab.runner run \
  --scenario configs/scenarios/md_default_loop_lane0_dataset_collection_v1.yaml \
  --outputs outputs/dataset-collection
```

Current labels are route-relative diagnostic targets: lateral/heading error, reference curvature, and model output state. They are not pixel-space lane labels and are therefore suitable for dataset audit and path-target experimentation, not for claiming production lane-detection training.

The first collection has 18 images and is a smoke set only. A training dataset requires a predeclared multi-seed coverage matrix, train/validation split, and pixel or vehicle-frame path-label definition.
