# `md_default_loop_lane0_v1` baseline contract

The selected v0.1 baseline is the frozen historical `md_default_loop_lane0_v1` artifact: pretrained OpenPilot SUT, 0 ms target transport delay, and three formal runs after an excluded warm-up. It is a comparison reference, not a claim that the SUT passes the driving outcome.

A current-environment confirmation is two consecutive runs of the documented configuration. Each must be non-`invalid`, record engagement, camera transport and the required artifact bundle. An infrastructure `invalid` leaves compatibility `not_confirmed`; the known SUT lane departure is reported separately and does not block confirmation. These runs never replace the historical baseline or move its reference point. Before approval, an integrity audit must confirm every required per-run artifact and its provenance. If one is missing, the baseline remains `evidence_gap`; it is not reconstructed or silently replaced. A replacement requires explicit approval of a new baseline version. Project-defined performance gates remain pending the [release process](../../docs/release-process.md).

The selected artifact set passed this audit on 2026-09-01. Re-run it with `uv run simlab baseline-audit --audit-output baselines/md_default_loop_lane0_v1/historical-audit.json`; the checked report includes artifact sizes and SHA-256 digests.
