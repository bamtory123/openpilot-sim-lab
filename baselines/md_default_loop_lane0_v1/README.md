# `md_default_loop_lane0_v1` baseline contract

The selected v0.1 baseline is the frozen historical `md_default_loop_lane0_v1` artifact: pretrained OpenPilot SUT, 0 ms target transport delay, and three formal runs after an excluded warm-up. It is a comparison reference, not a claim that the SUT passes the driving outcome.

A current-environment run is a separate compatibility check. It confirms that the documented configuration can still execute on the current host, but never replaces the historical baseline or moves its reference point. Before approval, an integrity audit must confirm every required per-run artifact and its provenance. If one is missing, the baseline remains `evidence_gap`; it is not reconstructed or silently replaced. A replacement requires explicit approval of a new baseline version. Project-defined performance gates remain pending the [release process](../../docs/release-process.md).
