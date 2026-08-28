# openpilot instrumentation summary

Base: `commaai/openpilot@084747c75d2cbd23af65ab7a9e770bbd7b98bac9`

The project fork keeps these changes on `project/sim-instrumentation`; the experiment framework remains in this repository.

| Area | Added interface | Effect on upstream simulation |
|---|---|---|
| MetaDrive process | fixed seed/reference-lane ground truth | emits route-relative lateral/heading/lane telemetry |
| Simulator bridge | `simlab_config`, telemetry queue, lifecycle events | enables configuration only when a scenario is supplied |
| Camera path | non-blocking `CameraTransportDelay` | always uses the queue; delay is zero until normal engagement |
| Camerad | source frame/capture timestamp arguments | preserves the original camera timestamp for delayed delivery |
| Control telemetry | model/planner/control curvature, openpilot steering command, normalized simulator steer, vehicle yaw-rate/curvature | separates perception/planning output from simulator actuation response |
| Path-following diagnostics | reference tangent, velocity direction, and lookahead dot/cross products | keeps pure-pursuit geometry and measured yaw-rate in MetaDrive world coordinates |
| MetaDrive camera | scenario-selected diagnostic FOV and opt-in frame capture | supports camera-domain diagnosis without changing the formal baseline |

The instrumented branch also retains WSL CUDA/runtime fixes needed by this workstation. No CARLA adapter or specialist model code is part of the v0.1 branch.

## Diagnostic boundary

The formal `md_default_loop_lane0_v1` scenario remains a 40-degree-FOV, model-driven baseline. `md_default_loop_lane0_fov60_diagnostic_v1` is a one-off diagnostic only and must not be mixed into the formal delay matrix. A capture is written only when `SIMLAB_CAMERA_DEBUG_PATH` is explicitly set; `SIMLAB_CAMERA_DEBUG_AFTER_FRAME` optionally selects a later simulation frame. The capture now writes a companion JSON (`SIMLAB_CAMERA_DEBUG_METADATA_PATH`, or `<image>.json`) containing simulation frame/time, FOV, and camera pose, so it can be joined exactly to `telemetry.csv`.

In the current model-driven 0 ms baseline, a measured lane departure is correctly classified as `valid/fail`. The added telemetry showed near-zero model/control curvature while the vehicle's reference-lane lateral error grew. Changing FOV from 40 to 60 degrees did not materially change that signal. This is evidence of a simulator-camera/model domain gap, not a justification to tune the simulator steering gain or a claim about real-road openpilot performance.

A post-driver alignment capture at simulation frame 2500 made the distinction concrete: the 40-degree road image visibly contains the upcoming left curve, the current reference road remains straight until frame 2600, and ground-truth curvature then becomes +0.008658 1/m. At the capture frame model/control target curvature was only about +3.5e-06 1/m while lateral error was -0.978 m. This is a diagnostic observation, not a calibrated perception metric; it motivates camera/preprocessing alignment work rather than simulator-only lateral-gain tuning.

The optional `reference_lane_assist` mode is explicitly simulator-only. It uses MetaDrive reference-lane position/heading and a target-speed controller after openpilot engagement, while preserving model/control telemetry for comparison. The first three deterministic gain trials reduced the model-driven lateral RMSE in one case but all ended in valid lane-departure failures. Future controller work must replace the simple proportional law with a separately specified path-following controller; it must not be presented as openpilot model improvement.

The optional `pure_pursuit` diagnostic is also simulator-only. Its first implementation mixed MetaDrive's `heading_theta` with world-coordinate lane positions: on a curved segment its recorded heading error was near zero even though the world-coordinate lookahead cross product was positive. It now computes the lookahead angle from the vehicle velocity direction and records yaw-rate from the same world frame. The corrected 0 ms trial still ended in a valid lane-departure failure, so this establishes instrumentation consistency rather than a passing controller.

With the corrected telemetry, reducing the pure-pursuit curvature-to-steer factor from 0.70 to 0.25 at 5 m/s reduced lateral RMSE from 0.580 m to 0.492 m and P95 absolute lateral error from 1.683 m to 1.402 m. Both runs remained `valid/fail` due to lane departure, and their maximum error was still about 2.3 m. The low-gain scenario is retained as `md_default_loop_lane0_pure_pursuit_low_gain_diagnostic_v1`; these single diagnostic trials are not part of the formal delay matrix.

At the same low gain, reducing target speed from 5 to 3 m/s further reduced RMSE to 0.471 m and P95 absolute error to 1.350 m, while mean speed was 2.994 m/s. It still ended in a valid lane-departure failure. Subsequent controller work should separate reference-curvature feed-forward from lateral-error feedback instead of treating either gain or target speed as a success path.

The initial `reference_curvature_follow` diagnostic keeps that separation explicit, using 3 m/s, a 0.70 curvature-to-steer factor, 0.01 lateral gain, and 0.25 heading gain. Its first corrected run produced 0.503 m RMSE and 1.442 m P95 error, worse than the low-speed pure-pursuit run, and also ended `valid/fail`. It is therefore retained as a negative result; feedback sign and frame conventions need fixture-level verification before further parameter tuning.
