# Windows/WSL host-stability boundary

## Observed on 2026-08-31

Two long-running openpilot + MetaDrive bridge attempts coincided with WSL instance restart evidence. The WSL kernel log recorded `dxgkio_query_adapter_info` failures followed by `dxgkio_escape` failures and an unclean system journal replacement. Windows System events recorded deletion and recreation of the WSL Hyper-V virtual NIC at 16:28 and 16:49 local time.

Windows did not record an NVIDIA Display/TDR error in the inspected interval. Therefore this repository does not attribute the event to a particular NVIDIA driver defect. It records only the observed boundary: CUDA-backed long bridge processes can interrupt the WSL guest on this host.

`dxgkio_escape: Ioctl failed: -22` also appeared during a later successful bounded CUDA-plus-renderer check that retained the same WSL boot ID and passed preflight. Treat this message alone as diagnostic noise, not restart evidence. A host interruption requires a boot-ID change, an unclean-journal boundary, or correlated Windows Hyper-V WSL recreation evidence.

At the time of inspection the host exposed WSL `2.7.12.0`, kernel `6.18.33.2-microsoft-standard-WSL2`, RTX 4080 driver `616.56`, 16,376 MiB GPU memory, about 14 GiB WSL memory available, and 4 GiB swap. No user `.wslconfig` was present. This does not prove the failure is unrelated to memory, but it rules out a configured low-memory cap as the immediate explanation. New manifests also record the GPU temperature, utilization, used/total memory, and P-state at run start for later comparison.

A standalone 20-second tinygrad CUDA soak (4,096-element reduction) completed 14,962 iterations with the expected result; GPU temperature remained 52°C afterward. This does not isolate a root cause or prove the longer combined simulator/bridge workload stable.

The renderer-only probe completed 20 MetaDrive steps with four 1928×1208 offscreen road-camera captures and clean shutdown. Together with the CUDA soak, this excludes neither the combined openpilot manager/modeld plus bridge workload nor other host factors; it is only a short successful probe, not evidence of long-duration renderer stability.

A separate end-to-end openpilot-manager/bridge smoke also completed a 23.94-second measured interval on the same recorded boot ID before normal simulator termination. It validates the new summary/coverage path through the real bridge, but remains too short and too diagnostically scoped to clear the long-run host-stability gate.

On 2026-08-31, a background 1,200-frame specialist probe left only an empty launcher log; no runner manifest or summary was created, and the next inspection observed a new WSL boot ID plus a fresh system journal. The selected Windows event window contained Hyper-V WSL-switch creation records but no NVIDIA/TDR record. Because that attempt predated the pre-launch wrapper and has no durable start timestamp, the repository records it as an infrastructure interruption observation, not a causal attribution to the scenario or driver.

The same fixed 1,200-frame specialist contract then completed twice through the foreground pre-launch wrapper. Each had 59.99 s active time, 1,200 published road frames, zero drops, 1.0 telemetry/road-camera coverage, unchanged WSL boot ID, and no selected WSL/GPU event in its exact UTC window. Actual delay median/P95/max were 25.06/33.38/44.09 ms and 23.58/31.93/46.62 ms on the common 0 ms scheduler path. These are two successful end-to-end stability probes, not long-run clearance or new formal performance replicates.

On 2026-09-02 KST, a separately retained 200-frame host-confirmation probe completed in 44 seconds with a 9.99-second measured interval, 1.0 telemetry/road-camera coverage, zero drop/departure/collision, runner exit code 0, and unchanged WSL boot ID. The bounded Windows collector recorded zero selected WSL/GPU System events after the probe start. This is a short host/engagement/transport confirmation only; it does not clear the long CUDA-backed bridge boundary or alter a driving qualification.

The immediately following bounded host-stack check completed a 5-second CUDA soak, two offscreen renderer steps, and preflight with that same boot ID. It confirms only the short CUDA/renderer/configuration path; the long CUDA-backed bridge boundary remains open.

## Harness behavior

- A completed run retains its normal `valid/pass` or `valid/fail` outcome.
- A watchdog, unexpected bridge exit, or Python-level runner exception is recorded as `invalid/not_evaluated`.
- Every manifest records its UTC creation time and the WSL boot ID. Use `created_at_utc` to choose the Windows event-collector time window. If a host restart prevents the runner from writing `summary.json`, run `simlab.runner recover --run-dir <run-dir>` after WSL recovers. It writes an explicit `invalid/not_evaluated: host_interrupted` summary, carries that recorded creation time forward with the pre-run and recovery boot IDs, and refuses to overwrite an existing result.
- Do not treat a missing summary as a failed driving result or silently omit it from a report.
- Generated reports list valid-failure reasons and invalid-infrastructure reasons in separate columns, so `host_interrupted` cannot be mistaken for a collision or lane-control outcome.
- New reports also summarize available manifest host provenance (GPU, driver, distinct WSL boot count, and GPU start-temperature range). Older artifacts without these fields remain readable and are shown as not recorded.

## Operating rule

Until the host problem is independently reproduced and isolated, avoid starting new long CUDA-backed formal matrices merely to collect more data. Use local unit tests, preflight, short MetaDrive reset/close checks, and already-completed artifacts for routine verification. Any future long run must preserve its manifest, Windows/WSL log timestamps, and outcome classification.

For a small independent CUDA check, run `SIM_TINYGRAD_DEVICE=CUDA $OPENPILOT_PYTHON scripts/check_cuda_runtime.py`. It verifies tinygrad's CUDA default device and one 1,024-element arithmetic result. Add `--duration-s 20` for the repeatable 20-second, 4,096-element soak used here. Neither mode is a simulator, modeld, or long-duration bridge stability test.

For an offscreen MetaDrive renderer-only check, run `PYTHONPATH="$OPENPILOT_ROOT" $OPENPILOT_PYTHON scripts/check_metadrive_renderer.py`. It uses the bridge's 1928×1208 road camera with host-memory images but does not start modeld, CAN, or the openpilot manager. Add `--steps` only for a bounded renderer probe.

For the complete bounded host-stack sequence, run `SIMLAB_ALLOW_DIRTY=1 scripts/check_host_stack.sh`. Its defaults are a 20-second CUDA soak and a 20-step renderer probe before preflight; override `CUDA_SOAK_SECONDS` or `METADRIVE_RENDER_STEPS` only for a shorter diagnostic check. It compares WSL boot IDs before and after a normally completed sequence.

For one deliberately bounded end-to-end bridge probe, use `scripts/run_host_stability_probe.sh <scenario> <output-root>`. It writes `attempt.json` before launching the runner, so a WSL restart before the runner creates its own manifest still leaves a UTC timestamp, scenario path, and pre-run boot ID. On normal return it also records exit code, completion time, and the post-run boot-ID comparison. This wrapper is diagnostic-only and runs exactly one scenario; do not substitute it for the formal batch command.

`simlab.runner report --outputs <output-root>` recursively finds run summaries below a host-probe output root, so the same report includes successful probe results and any recovered nested run artifact. The outer `attempt.json` is infrastructure provenance, not a driving result, and is not counted as a run.

For a long-run investigation, collect Windows-side evidence immediately after the run (or after WSL recovers) and retain it beside the run artifact:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '\\wsl.localhost\Ubuntu-24.04\home\hyunsung\src\openpilot-sim-lab\scripts\collect_windows_wsl_events.ps1' `
  -Since '2026-08-31T16:00:00+09:00' `
  -OutputPath 'C:\path\to\run\windows-host-events.json'
```

The collector records only matching System-log records in the selected time window (Hyper-V WSL switch, display/NVIDIA providers, or messages mentioning WSL/NVIDIA/display/GPU). It is evidence for temporal correlation; an event record by itself does not assign a driver root cause.
