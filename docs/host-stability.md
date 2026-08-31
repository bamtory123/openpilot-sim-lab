# Windows/WSL host-stability boundary

## Observed on 2026-08-31

Two long-running openpilot + MetaDrive bridge attempts coincided with WSL instance restart evidence. The WSL kernel log recorded `dxgkio_query_adapter_info` failures followed by `dxgkio_escape` failures and an unclean system journal replacement. Windows System events recorded deletion and recreation of the WSL Hyper-V virtual NIC at 16:28 and 16:49 local time.

Windows did not record an NVIDIA Display/TDR error in the inspected interval. Therefore this repository does not attribute the event to a particular NVIDIA driver defect. It records only the observed boundary: CUDA-backed long bridge processes can interrupt the WSL guest on this host.

At the time of inspection the host exposed WSL `2.7.12.0`, kernel `6.18.33.2-microsoft-standard-WSL2`, RTX 4080 driver `616.56`, 16,376 MiB GPU memory, about 14 GiB WSL memory available, and 4 GiB swap. No user `.wslconfig` was present. This does not prove the failure is unrelated to memory, but it rules out a configured low-memory cap as the immediate explanation.

## Harness behavior

- A completed run retains its normal `valid/pass` or `valid/fail` outcome.
- A watchdog, unexpected bridge exit, or Python-level runner exception is recorded as `invalid/not_evaluated`.
- If a host restart prevents the runner from writing `summary.json`, run `simlab.runner recover --run-dir <run-dir>` after WSL recovers. It writes an explicit `invalid/not_evaluated: host_interrupted` summary and refuses to overwrite an existing result.
- Do not treat a missing summary as a failed driving result or silently omit it from a report.

## Operating rule

Until the host problem is independently reproduced and isolated, avoid starting new long CUDA-backed formal matrices merely to collect more data. Use local unit tests, preflight, short MetaDrive reset/close checks, and already-completed artifacts for routine verification. Any future long run must preserve its manifest, Windows/WSL log timestamps, and outcome classification.
