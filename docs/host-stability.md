# Windows/WSL host-stability boundary

## Observed on 2026-08-31

Two long-running openpilot + MetaDrive bridge attempts coincided with WSL instance restart evidence. The WSL kernel log recorded `dxgkio_query_adapter_info` failures followed by `dxgkio_escape` failures and an unclean system journal replacement. Windows System events recorded deletion and recreation of the WSL Hyper-V virtual NIC at 16:28 and 16:49 local time.

Windows did not record an NVIDIA Display/TDR error in the inspected interval. Therefore this repository does not attribute the event to a particular NVIDIA driver defect. It records only the observed boundary: CUDA-backed long bridge processes can interrupt the WSL guest on this host.

`dxgkio_escape: Ioctl failed: -22` also appeared during a later successful bounded CUDA-plus-renderer check that retained the same WSL boot ID and passed preflight. Treat this message alone as diagnostic noise, not restart evidence. A host interruption requires a boot-ID change, an unclean-journal boundary, or correlated Windows Hyper-V WSL recreation evidence.

At the time of inspection the host exposed WSL `2.7.12.0`, kernel `6.18.33.2-microsoft-standard-WSL2`, RTX 4080 driver `616.56`, 16,376 MiB GPU memory, about 14 GiB WSL memory available, and 4 GiB swap. No user `.wslconfig` was present. This does not prove the failure is unrelated to memory, but it rules out a configured low-memory cap as the immediate explanation. New manifests also record the GPU temperature, utilization, used/total memory, and P-state at run start for later comparison.

A standalone 20-second tinygrad CUDA soak (4,096-element reduction) completed 14,962 iterations with the expected result; GPU temperature remained 52°C afterward. This does not isolate a root cause or prove the longer combined simulator/bridge workload stable.

The renderer-only probe completed 20 MetaDrive steps with four 1928×1208 offscreen road-camera captures and clean shutdown. Together with the CUDA soak, this excludes neither the combined openpilot manager/modeld plus bridge workload nor other host factors; it is only a short successful probe, not evidence of long-duration renderer stability.

## Harness behavior

- A completed run retains its normal `valid/pass` or `valid/fail` outcome.
- A watchdog, unexpected bridge exit, or Python-level runner exception is recorded as `invalid/not_evaluated`.
- Every manifest records the WSL boot ID. If a host restart prevents the runner from writing `summary.json`, run `simlab.runner recover --run-dir <run-dir>` after WSL recovers. It writes an explicit `invalid/not_evaluated: host_interrupted` summary, records the pre-run and recovery boot IDs plus whether they changed, and refuses to overwrite an existing result.
- Do not treat a missing summary as a failed driving result or silently omit it from a report.
- Generated reports list valid-failure reasons and invalid-infrastructure reasons in separate columns, so `host_interrupted` cannot be mistaken for a collision or lane-control outcome.
- New reports also summarize available manifest host provenance (GPU, driver, distinct WSL boot count, and GPU start-temperature range). Older artifacts without these fields remain readable and are shown as not recorded.

## Operating rule

Until the host problem is independently reproduced and isolated, avoid starting new long CUDA-backed formal matrices merely to collect more data. Use local unit tests, preflight, short MetaDrive reset/close checks, and already-completed artifacts for routine verification. Any future long run must preserve its manifest, Windows/WSL log timestamps, and outcome classification.

For a small independent CUDA check, run `SIM_TINYGRAD_DEVICE=CUDA $OPENPILOT_PYTHON scripts/check_cuda_runtime.py`. It verifies tinygrad's CUDA default device and one 1,024-element arithmetic result. Add `--duration-s 20` for the repeatable 20-second, 4,096-element soak used here. Neither mode is a simulator, modeld, or long-duration bridge stability test.

For an offscreen MetaDrive renderer-only check, run `PYTHONPATH="$OPENPILOT_ROOT" $OPENPILOT_PYTHON scripts/check_metadrive_renderer.py`. It uses the bridge's 1928×1208 road camera with host-memory images but does not start modeld, CAN, or the openpilot manager. Add `--steps` only for a bounded renderer probe.

For the complete bounded host-stack sequence, run `SIMLAB_ALLOW_DIRTY=1 scripts/check_host_stack.sh`. Its defaults are a 20-second CUDA soak and a 20-step renderer probe before preflight; override `CUDA_SOAK_SECONDS` or `METADRIVE_RENDER_STEPS` only for a shorter diagnostic check. It compares WSL boot IDs before and after a normally completed sequence.
