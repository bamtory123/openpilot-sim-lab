# openpilot instrumentation summary

Base: `commaai/openpilot@084747c75d2cbd23af65ab7a9e770bbd7b98bac9`

The project fork keeps these changes on `project/sim-instrumentation`; the experiment framework remains in this repository.

| Area | Added interface | Effect on upstream simulation |
|---|---|---|
| MetaDrive process | fixed seed/reference-lane ground truth | emits route-relative lateral/heading/lane telemetry |
| Simulator bridge | `simlab_config`, telemetry queue, lifecycle events | enables configuration only when a scenario is supplied |
| Camera path | non-blocking `CameraTransportDelay` | always uses the queue; delay is zero until normal engagement |
| Camerad | source frame/capture timestamp arguments | preserves the original camera timestamp for delayed delivery |

The instrumented branch also retains WSL CUDA/runtime fixes needed by this workstation. No CARLA adapter or specialist model code is part of the v0.1 branch.
