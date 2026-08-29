import json
import numpy as np
from PIL import Image

from simlab.specialist import predict_specialist, train_specialist, train_temporal_specialist


def test_specialist_trains_and_predicts_from_saved_rgb_samples(tmp_path):
  run = tmp_path / "run"; debug = run / "debug"; debug.mkdir(parents=True)
  rows = []
  for index in range(40):
    value = index * 6
    name = f"frame-{index}.png"
    Image.fromarray(np.full((8, 8, 3), value, dtype=np.uint8)).save(debug / name)
    rows.append({"image": f"debug/{name}", "split": "validation" if index >= 32 else "train",
                 "target_normalized_steer": value / 2550.0})
  (run / "specialist_manifest.jsonl").write_text("\n".join(json.dumps(row) for row in rows))

  artifact = tmp_path / "specialist.npz"
  metrics = train_specialist(tmp_path, artifact)

  assert metrics["train_samples"] == 32 and metrics["validation_samples"] == 8
  assert predict_specialist(artifact, np.full((8, 8, 3), 240, dtype=np.uint8)) > 0.08


def test_temporal_specialist_requires_adjacent_frames_and_trains(tmp_path):
  run = tmp_path / "run"; debug = run / "debug"; debug.mkdir(parents=True)
  rows = []
  for index in range(42):
    value = index * 5
    name = f"frame-{index}.png"
    Image.fromarray(np.full((8, 8, 3), value, dtype=np.uint8)).save(debug / name)
    rows.append({"image": f"debug/{name}", "simulation_frame": index * 20,
                 "split": "validation" if index >= 34 else "train", "target_normalized_steer": value / 2550.0})
  (run / "specialist_manifest.jsonl").write_text("\n".join(json.dumps(row) for row in rows))

  metrics = train_temporal_specialist(tmp_path, tmp_path / "temporal.npz")

  assert metrics["train_pairs"] == 33 and metrics["validation_pairs"] == 7
