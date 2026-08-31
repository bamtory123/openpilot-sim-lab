# v0.2 static-lead dataset-matrix sample

This sample records a three-seed MetaDrive collection of one fixed synthetic encounter: a stationary lead vehicle starts 20 m ahead on the reference lane while the local camera-only specialist targets 2.0 m/s. Seeds `20260831` and `20260901` are train; `20260902` is held out for dataset provenance.

All three runs completed their measurement window as `valid/fail: collision`. The retained dataset contains 30 RGB-to-simulator-ground-truth joins: 20 train, 10 held-out validation, 30 traffic-labeled, and 13 collision-state samples. It is deliberately a repeatability/data-contract result, not a trained model result.

Raw RGB, telemetry, logs, local artifacts, and generated report remain untracked. Ground-truth actor labels are analysis-only and are never sent to the camera stream, planner, or controller. This sample does not demonstrate lead detection, braking, following, collision avoidance, pretrained openpilot behavior, vehicle performance, or real-road capability.
