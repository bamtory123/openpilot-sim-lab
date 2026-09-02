from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "examples/v0.1-portfolio-evidence/evidence.json"


def source_records(evidence: dict) -> list[dict]:
  return [evidence["formal_matrix"]["source"], evidence["baseline_audit"]["source"],
          evidence["regression_review"]["source"], *evidence["host_confirmation"]["sources"]]


def sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
  evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
  errors: list[str] = []
  for record in source_records(evidence):
    relative_path = Path(record["path"])
    if relative_path.is_absolute() or ".." in relative_path.parts:
      errors.append(f"unsafe source path: {record['path']}")
      continue
    path = ROOT / relative_path
    if not path.is_file():
      errors.append(f"missing source: {record['path']}")
    elif sha256(path) != record["sha256"]:
      errors.append(f"source digest mismatch: {record['path']}")
  forbidden_names = {"telemetry.csv", "camera.csv", "raw_frames", "process_logs"}
  exposed = [path.relative_to(EVIDENCE_PATH.parent) for path in EVIDENCE_PATH.parent.rglob("*")
             if path.name in forbidden_names]
  if exposed:
    errors.append(f"public bundle exposes excluded artifacts: {', '.join(map(str, exposed))}")
  if errors:
    raise SystemExit("\n".join(errors))
  print(json.dumps({"schema_version": 1, "status": "pass", "source_count": len(source_records(evidence))},
                   sort_keys=True))


if __name__ == "__main__":
  main()
