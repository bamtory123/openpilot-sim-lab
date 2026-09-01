# Decision log

## D-001: frozen historical baseline

The v0.1 comparison reference is the three 0 ms formal runs in `outputs/v0.2-formal-delay-matrix-20260828`. It is immutable and only becomes approved after the artifact audit. A missing required artifact is an `evidence_gap`, never reconstructed evidence.

## D-002: SUT outcome is separate from framework qualification

The pretrained OpenPilot baseline's lane departure remains `valid/fail` where coverage is complete. It is not a SUT pass and does not by itself make the framework release fail. Data integrity, newly observed collision, and newly observed disengagement remain regression concerns.

## D-003: three-phase regression policy

Phase 1 hard-gates invalid data and new functional events. Phase 2 makes same-provenance KPI changes `review_required`. Phase 3 performance thresholds require an explicit project-defined rationale and approval; no such thresholds are currently approved.

## D-004: scoped host confirmation

Current-host compatibility is a separately versioned nominal-10-second/200-frame probe, not the 55-second formal-driving scenario. It preserves the SUT, map, seed, engagement, and 0 ms transport path, and requires two consecutive non-invalid runs. It cannot replace the historical baseline or make a driving-performance claim.

## D-005: current qualification disposition

The current same-provenance candidate set is a Phase 1 hard-gate failure because every run becomes invalid after the known early departure prevents formal coverage. The v0.1 release remains `not_qualified_yet`. Future work must not weaken or relabel this evidence without an explicit policy decision.
