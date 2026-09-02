import py_compile
from pathlib import Path
import re
import stat
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_shell_scripts_have_valid_bash_syntax():
  for path in sorted((ROOT / "scripts").glob("*.sh")):
    subprocess.run(["bash", "-n", str(path)], check=True)


def test_shell_scripts_are_executable():
  for path in sorted((ROOT / "scripts").glob("*.sh")):
    assert path.stat().st_mode & stat.S_IXUSR, path


def test_python_scripts_compile_without_runtime_dependencies():
  for path in sorted((ROOT / "scripts").glob("*.py")):
    py_compile.compile(str(path), doraise=True)


def test_local_documentation_links_exist():
  documents = sorted([ROOT / "README.md", *ROOT.glob("docs/**/*.md"), *ROOT.glob("examples/**/*.md")])
  for document in documents:
    for target in re.findall(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", document.read_text(encoding="utf-8")):
      if "://" not in target and not target.startswith("mailto:"):
        assert (document.parent / target).resolve().exists(), f"{document}: {target}"


def test_readme_uses_uv_for_openpilot_runtime_editable_install():
  readme = (ROOT / "README.md").read_text(encoding="utf-8")
  assert 'uv pip install --python "$OPENPILOT_PYTHON" --no-deps -e .' in readme
  assert "$OPENPILOT_PYTHON -m pip install --no-deps -e ." not in readme
  assert 'OPENPILOT_PYTHON="$OPENPILOT_ROOT/.venv/bin/python"' in readme
  assert "$OPENPILOT_PYTHON -m simlab.runner batch --allow-dirty --outputs outputs" in readme


def test_host_stack_supports_structured_success_evidence():
  script = (ROOT / "scripts/check_host_stack.sh").read_text(encoding="utf-8")
  host_stability = (ROOT / "docs/host-stability.md").read_text(encoding="utf-8")
  assert "HOST_STACK_OUTPUT" in script
  assert '"schema_version": 1' in script
  assert '"failed_stage": None if status == "pass" else stage' in script
  assert "HOST_STACK_OUTPUT=outputs/host-stack/host-stack.json" in host_stability
