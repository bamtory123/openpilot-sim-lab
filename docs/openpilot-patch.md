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
| MetaDrive camera | scenario-selected diagnostic FOV and opt-in frame capture | supports camera-domain diagnosis without changing the formal baseline |

The instrumented branch also retains WSL CUDA/runtime fixes needed by this workstation. No CARLA adapter or specialist model code is part of the v0.1 branch.

## Diagnostic boundary

The formal `md_default_loop_lane0_v1` scenario remains a 40-degree-FOV, model-driven baseline. `md_default_loop_lane0_fov60_diagnostic_v1` is a one-off diagnostic only and must not be mixed into the formal delay matrix. A capture is written only when `SIMLAB_CAMERA_DEBUG_PATH` is explicitly set; `SIMLAB_CAMERA_DEBUG_AFTER_FRAME` optionally selects a later simulation frame.

In the current model-driven 0 ms baseline, a measured lane departure is correctly classified as `valid/fail`. The added telemetry showed near-zero model/control curvature while the vehicle's reference-lane lateral error grew. Changing FOV from 40 to 60 degrees did not materially change that signal. This is evidence of a simulator-camera/model domain gap, not a justification to tune the simulator steering gain or a claim about real-road openpilot performance.

The optional `reference_lane_assist` mode is explicitly simulator-only. It uses MetaDrive reference-lane position/heading and a target-speed controller after openpilot engagement, while preserving model/control telemetry for comparison. The first three deterministic gain trials reduced the model-driven lateral RMSE in one case but all ended in valid lane-departure failures. Future controller work must replace the simple proportional law with a separately specified path-following controller; it must not be presented as openpilot model improvement.
