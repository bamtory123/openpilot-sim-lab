# Traceability

| Requirement | Test Case | Scenario | KPI / artifact | Status |
|---|---|---|---|---|
| REQ-ENV-001 | TC-PREFLIGHT-001 | all | `manifest.json` | implemented |
| REQ-DATA-001/002 | TC-DATA-001 | all | coverage, camera timestamps | implemented |
| REQ-TIM-001 | TC-DELAY-* | `md_default_loop_lane0_v1` | `camera.csv`, actual delay | implemented |
| REQ-TIM-002 | TC-QUEUE-OVERFLOW-001 | unit fixture | invalid verdict | implemented |
| REQ-FUNC-001 | TC-BASE-001 | `md_default_loop_lane0_v1` | telemetry/events/summary | implemented |
| REQ-REG-001/002 | TC-REG-001 | approved baseline | KPI delta, new collision/disengagement, gate artifact | planned |
| REQ-REL-001/002 | TC-RELEASE-001 | release candidate | qualification package | in progress |
