import py_compile
import json
from pathlib import Path
import re
import stat
import subprocess
import sys


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
  assert '"schema_version": 3' in script
  assert '"failed_stage": None if status == "pass" else stage' in script
  assert '"provenance": {"sim_lab": git_source(simlab_root)' in script
  assert "HOST_STACK_OUTPUT=outputs/host-stack/host-stack.json" in host_stability


def test_host_stack_artifact_verifier_rejects_inconsistent_pass(tmp_path):
  artifact = {
    "schema_version": 3, "status": "pass", "exit_code": 0, "failed_stage": None,
    "recorded_wsl_boot_id": "a", "observed_wsl_boot_id": "b", "wsl_boot_changed": True,
    "cuda": {}, "renderer": {}, "preflight": "pass",
    "provenance": {"sim_lab": {}, "openpilot": {}, "python_version": "3.12", "wsl_kernel": "kernel",
                   "metadrive_version": "0.4.2.3", "gpu": None},
  }
  path = tmp_path / "host-stack.json"
  path.write_text(json.dumps(artifact), encoding="utf-8")
  result = subprocess.run([sys.executable, str(ROOT / "scripts/verify_host_stack_artifact.py"), str(path)],
                          capture_output=True, text=True)

  assert result.returncode != 0 and "changed boot ID" in result.stderr


def test_host_stack_comparison_is_descriptive_only(tmp_path):
  base = {
    "schema_version": 3, "status": "pass", "exit_code": 0, "failed_stage": None,
    "recorded_wsl_boot_id": "a", "observed_wsl_boot_id": "a", "wsl_boot_changed": False,
    "cuda": {"elapsed_ms": 1000, "iterations": 10}, "renderer": {"elapsed_ms": 20}, "preflight": "pass",
    "provenance": {"sim_lab": {"commit": "a"}, "openpilot": {"commit": "b"}, "python_version": "3.12",
                   "wsl_kernel": "kernel", "metadrive_version": "0.4.2.3", "gpu": "GPU"},
  }
  baseline, candidate = tmp_path / "baseline.json", tmp_path / "candidate.json"
  baseline.write_text(json.dumps(base), encoding="utf-8")
  base["cuda"]["iterations"] = 20
  candidate.write_text(json.dumps(base), encoding="utf-8")
  result = subprocess.run([sys.executable, str(ROOT / "scripts/compare_host_stack_artifacts.py"), str(baseline), str(candidate)],
                          check=True, capture_output=True, text=True)

  comparison = json.loads(result.stdout)
  assert comparison["scope"] == "descriptive_host_runtime_comparison_only"
  assert comparison["comparison_status"] == "comparable"
  assert comparison["candidate"]["cuda_iterations_per_s"] == 20


def test_windows_event_summary_keeps_high_severity_count_descriptive(tmp_path):
  events = {"since": "a", "until": "b", "events": [
    {"LevelDisplayName": "Information", "LogName": "System", "ProviderName": "VmSwitch", "Id": 1},
    {"LevelDisplayName": "Warning", "LogName": "System", "ProviderName": "Display", "Id": 2},
  ]}
  path = tmp_path / "events.json"
  path.write_text(json.dumps(events), encoding="utf-8")
  result = subprocess.run([sys.executable, str(ROOT / "scripts/summarize_windows_wsl_events.py"), str(path)],
                          check=True, capture_output=True, text=True)

  summary = json.loads(result.stdout)
  assert summary["scope"] == "descriptive_windows_wsl_gpu_event_summary_only"
  assert summary["high_severity_event_count"] == 1


def test_windows_event_summary_accepts_powershell_utf8_bom(tmp_path):
  path = tmp_path / "events.json"
  path.write_text(json.dumps({"events": []}), encoding="utf-8-sig")
  result = subprocess.run([sys.executable, str(ROOT / "scripts/summarize_windows_wsl_events.py"), str(path)],
                          check=True, capture_output=True, text=True)

  assert json.loads(result.stdout)["event_count"] == 0


def test_windows_event_summary_normalizes_windows_numeric_levels(tmp_path):
  path = tmp_path / "events.json"
  path.write_text(json.dumps({"events": [{"LevelDisplayName": 2}, {"LevelDisplayName": 4}, {"LevelDisplayName": 5}]}),
                  encoding="utf-8")
  result = subprocess.run([sys.executable, str(ROOT / "scripts/summarize_windows_wsl_events.py"), str(path)],
                          check=True, capture_output=True, text=True)

  summary = json.loads(result.stdout)
  assert summary["high_severity_event_count"] == 1
  assert summary["severity_counts"] == {"Error": 1, "Information": 1, "Verbose": 1}


def test_carla_smoke_preflight_keeps_connection_opt_in():
  script = (ROOT / "scripts/carla_smoke_preflight.py").read_text(encoding="utf-8")
  documentation = (ROOT / "docs/carla-smoke.md").read_text(encoding="utf-8")

  assert 'parser.add_argument("--connect", action="store_true")' in script
  assert 'parser.add_argument("--sync-ticks", type=int, default=0)' in script
  assert 'parser.add_argument("--camera-state-control-smoke", action="store_true")' in script
  assert "world.apply_settings(original_settings)" in script
  assert "actors_destroyed" in script
  assert "carla_client_or_connectivity_smoke_only" in script
  assert "neither starts an OpenPilot bridge nor qualifies CARLA closed-loop behavior" in documentation
