# v0.6 simulator-specialist tight-DAgger sample

This release-friendly subset records the three-repeat aggregate for the local `outputs/v0.6-temporal-gamma-tight-dagger-tight-loop-speed2-*-20260830` evaluation. Raw telemetry, camera frames, logs, and generated local artifact remain untracked.

All three fixed 45 m-loop, 2.0 m/s repeats completed 1,200 frames as `valid/pass` with no lane departure, collision, or camera drop. Lateral RMSE was 0.411064, 0.407980, and 0.417673 m (mean 0.412239 m; population standard deviation 0.004043 m).

This applies only to the local camera-only artifact and this fixed MetaDrive contract. It is not a pretrained-openpilot, vehicle, road, or geometry-generalization result. The same artifact's 60 m/gamma-0.8 regression run had materially higher RMSE, so it is not the gamma-0.8 reference artifact.
