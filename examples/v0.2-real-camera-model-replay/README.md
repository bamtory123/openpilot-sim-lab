# Real-camera model replay reference

This public-safe bundle adds an official OpenPilot real-camera replay reference beside the MetaDrive closed-loop evidence. It isolates model input health; it is not a driving test, matched-scene accuracy study, or real-road performance claim.

| Observation | Official real-camera replay | MetaDrive 40° closed loop |
|---|---:|---:|
| Model outputs | 60 / 60 | 2870 telemetry samples |
| Left lane probability mean | 0.9231 | 0.0118 |
| Right lane probability mean | 0.9097 | 0.0241 |
| Path horizon mean | 244.45 m | 4.73 m |
| Functional status | `pass` | `valid/fail` |
| Host timing | `not_qualified` | not compared across runtimes |

The pretrained model produced full-count, fresh outputs on the upstream real-camera route, with roughly 0.9 lane probabilities and a 244 m mean path horizon. Under the retained MetaDrive camera contract, mean lane probabilities were roughly 0.01–0.02 and the path horizon was below 5 m. Because the scenes are not matched, this is a strong input-domain diagnostic contrast—not an accuracy ratio. It supports stopping ungrounded simulator camera tuning and keeping MetaDrive focused on integration, timing/fault injection, and actuator regression.

`evidence.json` binds the aggregate values to the retained real-camera summary and MetaDrive summary/telemetry with SHA-256. Raw video, decoded frames, per-frame telemetry, models, and local paths are excluded.
