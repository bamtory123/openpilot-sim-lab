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


def test_carla_windows_wrapper_preserves_logs_and_cleanup_contract():
  script = (ROOT / "scripts/run_carla_camera_smoke.ps1").read_text(encoding="utf-8")

  assert "server.stdout.log" in script and "server.stderr.log" in script
  assert '"connect.log"' in script and '"client.log"' in script
  assert "result.json" in script
  assert "--camera-state-control-smoke" in script
  assert "finally" in script and "taskkill.exe /PID $server.Id /T /F" in script
  assert "ip route show default" in script and "pass -HostIp explicitly" in script
  assert "carla_client_or_connectivity_smoke_only" in script


def test_carla_pilot_verifier_requires_analysis_only_capture_contract(tmp_path):
  run = tmp_path / "run"; run.mkdir()
  for name in ("events.jsonl", "telemetry.csv", "camera.csv", "run.log"):
    (run / name).touch()
  (run / "captures").mkdir()
  (run / "captures/road.png").write_bytes(b"png")
  sample = {"split": "analysis_only", "image": "captures/road.png", "labels": {}}
  (run / "dataset_manifest.jsonl").write_text(json.dumps(sample) + "\n")
  dataset = {"scope": "carla_analysis_only_not_control_training", "joined_samples": 1, "dropped_frames": 0, "valid": True}
  (run / "dataset_summary.json").write_text(json.dumps(dataset))
  (run / "manifest.json").write_text(json.dumps({"scope": "carla_v02_adapter_pilot_not_road_qualification",
                                                     "capture": {"enabled": True}}))
  (run / "summary.json").write_text(json.dumps({"schema_version": 1, "pilot_status": "integrated-but-not-stable",
                                                   "dataset_summary": dataset}))

  result = subprocess.run([sys.executable, str(ROOT / "scripts/verify_carla_adapter_pilot.py"), str(run)],
                          check=True, capture_output=True, text=True)

  assert json.loads(result.stdout)["dataset"] == {"valid": True, "joined_samples": 1, "dropped_frames": 0}


def test_carla_smoke_artifact_verifier_rejects_missing_log(tmp_path):
  result = {
    "schema_version": 1, "scope": "carla_client_or_connectivity_smoke_only", "status": "pass",
    "connect_exit_code": 0, "client_exit_code": 0, "server_stopped": True, "failure": None,
    "logs": {"server_stdout": "server.stdout.log", "server_stderr": "server.stderr.log",
             "connect": "connect.log", "client": "client.log"},
  }
  result_path = tmp_path / "result.json"
  result_path.write_text(json.dumps(result), encoding="utf-8")
  for name in result["logs"].values():
    (tmp_path / name).touch()
  subprocess.run([sys.executable, str(ROOT / "scripts/verify_carla_smoke_artifact.py"), str(result_path)], check=True)
  (tmp_path / "client.log").unlink()
  failed = subprocess.run([sys.executable, str(ROOT / "scripts/verify_carla_smoke_artifact.py"), str(result_path)],
                          capture_output=True, text=True)
  assert failed.returncode != 0 and "client log" in failed.stderr


def test_carla_smoke_artifact_verifier_requires_schema_2_observation(tmp_path):
  result = {
    "schema_version": 2, "scope": "carla_client_or_connectivity_smoke_only", "status": "pass",
    "connect_exit_code": 0, "client_exit_code": 0, "server_stopped": True, "failure": None,
    "logs": {"server_stdout": "server.stdout.log", "server_stderr": "server.stderr.log",
             "connect": "connect.log", "client": "client.log"},
  }
  result_path = tmp_path / "result.json"
  result_path.write_text(json.dumps(result), encoding="utf-8")
  for name in result["logs"].values():
    (tmp_path / name).touch()
  failed = subprocess.run([sys.executable, str(ROOT / "scripts/verify_carla_smoke_artifact.py"), str(result_path)],
                          capture_output=True, text=True)
  assert failed.returncode != 0 and "client/server observation" in failed.stderr


def test_carla_smoke_artifact_summary_reports_latest_verified_run(tmp_path):
  run = tmp_path / "20260902T000000Z"
  run.mkdir()
  result = {
    "schema_version": 2, "scope": "carla_client_or_connectivity_smoke_only", "status": "pass",
    "host": "172.28.112.1", "port": 2000, "connect_exit_code": 0, "client_exit_code": 0,
    "server_stopped": True, "failure": None,
    "client_observation": {"client_version": "0.9.16", "server_version": "0.9.16",
                           "camera": {"width": 320, "height": 180}, "vehicle_control": {},
                           "actors_destroyed": True},
    "logs": {"server_stdout": "server.stdout.log", "server_stderr": "server.stderr.log",
             "connect": "connect.log", "client": "client.log"},
  }
  (run / "result.json").write_text(json.dumps(result), encoding="utf-8")
  for name in result["logs"].values():
    (run / name).touch()
  output = subprocess.run([sys.executable, str(ROOT / "scripts/summarize_carla_smoke_artifacts.py"), str(tmp_path)],
                          check=True, capture_output=True, text=True)
  summary = json.loads(output.stdout)
  assert summary["scope"] == "carla_client_smoke_artifact_summary_only"
  assert summary["artifact_count"] == summary["verified_count"] == 1
  assert summary["latest"]["run_id"] == run.name


def test_carla_smoke_artifact_summary_preserves_malformed_result_as_failed(tmp_path):
  run = tmp_path / "broken"
  run.mkdir()
  (run / "result.json").write_text("not-json", encoding="utf-8")
  output = subprocess.run([sys.executable, str(ROOT / "scripts/summarize_carla_smoke_artifacts.py"), str(tmp_path)],
                          check=True, capture_output=True, text=True)
  summary = json.loads(output.stdout)
  assert summary["artifact_count"] == 1 and summary["verified_count"] == 0
  assert summary["latest"]["run_id"] == "broken"
  assert summary["latest"]["verification"] == "fail"


def test_carla_public_evidence_excludes_local_paths_and_logs(tmp_path):
  run = tmp_path / "run"
  run.mkdir()
  result = {
    "schema_version": 2, "scope": "carla_client_or_connectivity_smoke_only", "status": "pass",
    "carla_exe": "C:/private/CarlaUE4.exe", "host": "172.28.112.1", "port": 2000,
    "connect_exit_code": 0, "client_exit_code": 0, "server_stopped": True, "failure": None,
    "client_observation": {"client_version": "0.9.16", "server_version": "0.9.16",
                           "camera": {"width": 320, "height": 180},
                           "vehicle_control": {"throttle": 0, "steer": 0, "brake": 1},
                           "vehicle_speed_mps": 1.47, "actors_destroyed": True,
                           "world_settings_restored": True},
    "logs": {"server_stdout": "server.stdout.log", "server_stderr": "server.stderr.log",
             "connect": "connect.log", "client": "client.log"},
  }
  result_path = run / "result.json"
  result_path.write_text(json.dumps(result), encoding="utf-8")
  for name in result["logs"].values():
    (run / name).touch()
  output_dir = tmp_path / "public"
  subprocess.run([sys.executable, str(ROOT / "scripts/build_carla_smoke_public_evidence.py"), str(result_path),
                  "--output-dir", str(output_dir)], check=True)
  public = (output_dir / "evidence.json").read_text(encoding="utf-8")
  assert "private" not in public and "server.stdout.log" not in public and "172.28.112.1" not in public
  subprocess.run([sys.executable, str(ROOT / "scripts/verify_carla_smoke_public_evidence.py"), str(result_path),
                  "--output-dir", str(output_dir)], check=True)
  (output_dir / "README.md").write_text("drift", encoding="utf-8")
  failed = subprocess.run([sys.executable, str(ROOT / "scripts/verify_carla_smoke_public_evidence.py"), str(result_path),
                          "--output-dir", str(output_dir)], capture_output=True, text=True)
  assert failed.returncode != 0 and "summary differs" in failed.stderr


def test_committed_carla_public_sample_is_sanitized_and_scoped():
  sample_dir = ROOT / "examples/v0.2-carla-client-smoke"
  evidence = json.loads((sample_dir / "evidence.json").read_text(encoding="utf-8"))
  readme = (sample_dir / "README.md").read_text(encoding="utf-8")
  serialized = json.dumps(evidence)

  assert evidence["scope"] == "carla_client_smoke_public_sample_only"
  assert len(evidence["source_sha256"]) == 64
  assert all(token not in serialized for token in ("172.28.", "C:\\", "server.stdout.log", "client.log"))
  assert "outside the v0.1 MetaDrive release gate" in readme
  assert "does not demonstrate an OpenPilot bridge, closed loop" in readme
