# v0.1 public evidence bundle

This is a deliberately small, public-safe selection from four local evidence sources. It excludes raw telemetry, camera data, frames, and process logs.

Each selected source is recorded with its local path and SHA-256 in `evidence.json`, so an evaluator with the retained local artifacts can verify that the public extract was generated from the stated evidence.

- **Formal matrix:** one representative 0 ms summary plus the four-condition aggregate. Every formal result is `valid/fail: lane_departure`; it is not a driving-success claim.
- **Baseline audit:** approved historical three-run reference and its scenario provenance.
- **Regression review:** the same-provenance current candidate is a Phase 1 `hard_gate_fail`; KPI deltas are diagnostic only.
- **Host confirmation:** two 200-frame `valid/pass` compatibility probes. They validate engagement/transport/artifact integrity, not driving performance.

Regenerate `evidence.json` only from the retained local source artifacts:

```bash
uv run python scripts/build_v01_public_evidence.py
```

Verify the retained local source hashes without rewriting the bundle:

```bash
uv run python scripts/verify_v01_public_evidence.py
```
