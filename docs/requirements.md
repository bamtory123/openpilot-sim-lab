# Verification requirements

| ID | Requirement | Status |
|---|---|---|
| REQ-ENV-001 | Formal run records full SUT/sim-lab commit, dirty state, runtime and command. | implemented |
| REQ-ENV-002 | A frozen historical baseline is integrity-audited separately from two consecutive current-host confirmation runs; any required-artifact gap remains an evidence gap and confirmation cannot replace the baseline. | implemented |
| REQ-DATA-001 | Measurement telemetry and road-camera coverage meet scenario minimum. | implemented |
| REQ-DATA-002 | Timestamp regression, frame ordering and unexpected drops are detected. | implemented |
| REQ-TIM-001 | Target and actual camera delay are recorded through one non-blocking queue path. | implemented |
| REQ-TIM-002 | Queue overflow or unexpected frame drop is invalid. | implemented |
| REQ-FUNC-001 | Reference-lane departure, collision, disengagement and termination are recorded. | implemented |
| REQ-REG-001 | Approved baseline KPI deltas, new collision and new disengagement are evaluated independently of known baseline lane departure. | implemented |
| REQ-REG-002 | Hard regression gates are automatic; baseline-relative performance changes are review-required until project-defined thresholds are approved. | implemented |
| REQ-REL-001 | Requirement–test–scenario–artifact traceability is retained. | implemented |
| REQ-REL-002 | Qualification report and limitations are packaged for release. | implemented |

All numerical acceptance limits are project-defined only; no OEM or production-vehicle threshold is implied.
