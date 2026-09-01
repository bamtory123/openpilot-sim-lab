# Traceability

| Requirement | Test Case | Scenario | KPI / artifact | Status |
|---|---|---|---|---|
| REQ-ENV-001 | TC-PREFLIGHT-001 | all | `manifest.json` | implemented |
| REQ-ENV-002 | TC-COMP-001 | host-confirmation probe | approved baseline audit and two-run current-host confirmation | implemented |
| REQ-DATA-001 | TC-DATA-001 | all | telemetry and road-camera coverage | implemented |
| REQ-DATA-002 | TC-DATA-001 | all | camera timestamps and frame ordering | implemented |
| REQ-TIM-001 | TC-DELAY-* | `md_default_loop_lane0_v1` | `camera.csv`, actual delay | implemented |
| REQ-TIM-002 | TC-QUEUE-OVERFLOW-001 | unit fixture | invalid verdict | implemented |
| REQ-FUNC-001 | TC-BASE-001 | `md_default_loop_lane0_v1` | telemetry/events/summary | implemented |
| REQ-REG-001 | TC-REG-001 | same scenario/delay | regression-review JSON: KPI delta and new collision/disengagement | implemented |
| REQ-REG-002 | TC-REG-001 | same scenario/delay | regression-review hard/provenance gate and review-required policy | implemented |
| REQ-REL-001 | TC-RELEASE-001 | release candidate | CI requirement/test/traceability consistency check | implemented |
| REQ-REL-002 | TC-RELEASE-001 | release candidate | CI qualification-package boundary check | implemented |
