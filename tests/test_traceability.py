import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_every_requirement_is_covered_by_test_plan_and_traceability():
  requirements = (ROOT / "docs/requirements.md").read_text(encoding="utf-8")
  test_plan = (ROOT / "docs/test-plan.md").read_text(encoding="utf-8")
  traceability = (ROOT / "docs/traceability.md").read_text(encoding="utf-8")
  identifiers = set(re.findall(r"REQ-[A-Z]+-\d{3}", requirements))

  assert identifiers
  for identifier in identifiers:
    assert identifier.replace("REQ-", "") in test_plan
    assert identifier in traceability
