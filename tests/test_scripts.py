import py_compile
import json
import hashlib
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


def test_openpilot_patch_verifier_checks_both_bundle_hashes():
  script = (ROOT / "scripts/verify_openpilot_patch_bundles.sh").read_text(encoding="utf-8")
  assert "worktree add --detach" in script and "worktree remove --force" in script
  assert "openpilot-v01-sim-instrumentation.patch" in script
  assert "openpilot-v02-carla-adapter.patch" in script


def test_portfolio_snapshot_verifier_is_public_checkout_only():
  script = (ROOT / "scripts/verify_portfolio_snapshot.sh").read_text(encoding="utf-8")
  assert "verify_portfolio_readiness.py" in script
  assert "--verify-local-v01" not in script
  assert '"$python_runner" -m pytest -q' in script


def test_python_scripts_compile_without_runtime_dependencies():
  for path in sorted((ROOT / "scripts").glob("*.py")):
    py_compile.compile(str(path), doraise=True)


def test_real_camera_replay_setup_pins_compatible_ffmpeg():
  setup = (ROOT / "scripts/setup_real_camera_replay.sh").read_text(encoding="utf-8")
  runner = (ROOT / "scripts/run_real_camera_model_replay.py").read_text(encoding="utf-8")

  assert "ffmpeg-n7.1.5-12-g1fdbca85aa-linux64-gpl-7.1.tar.xz" in setup
  assert "c1e6caf48923dd8e6bc5e54d51ba70c321175b8162ae9c414c392990e72f0e79" in setup
  assert "sha256sum -c" in setup
  assert 'ffmpeg["major"] > 7' in runner
  assert "functional_status" in runner and "timing_status" in runner


def test_local_documentation_links_exist():
  documents = sorted([ROOT / "README.md", *ROOT.glob("docs/**/*.md"), *ROOT.glob("examples/**/*.md")])
  for document in documents:
    for target in re.findall(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", document.read_text(encoding="utf-8")):
      if "://" not in target and not target.startswith("mailto:"):
        assert (document.parent / target).resolve().exists(), f"{document}: {target}"


def test_openpilot_patch_bundles_are_documented_and_hashed():
  readme = (ROOT / "patches/README.md").read_text(encoding="utf-8")
  for name in ("openpilot-v01-sim-instrumentation.patch", "openpilot-v02-carla-adapter.patch"):
    digest = hashlib.sha256((ROOT / "patches" / name).read_bytes()).hexdigest()
    assert digest in readme
  assert "084747c75d2cbd23af65ab7a9e770bbd7b98bac9" in readme
  assert 'git -C "$openpilot" apply --check "$simlab/patches/' in readme


def test_readme_uses_uv_for_openpilot_runtime_editable_install():
  readme = (ROOT / "README.md").read_text(encoding="utf-8")
  assert 'uv pip install --python "$OPENPILOT_PYTHON" --no-deps -e .' in readme
  assert "$OPENPILOT_PYTHON -m pip install --no-deps -e ." not in readme
  assert 'OPENPILOT_PYTHON="$OPENPILOT_ROOT/.venv/bin/python"' in readme
  assert "$OPENPILOT_PYTHON -m simlab.runner batch --allow-dirty --outputs outputs" in readme
  assert "bounded v0.2 Windows–WSL adapter-pilot and smoke-test effort" in readme


def test_host_stack_supports_structured_success_evidence():
  script = (ROOT / "scripts/check_host_stack.sh").read_text(encoding="utf-8")
  host_stability = (ROOT / "docs/host-stability.md").read_text(encoding="utf-8")
  assert "HOST_STACK_OUTPUT" in script
  assert '"schema_version": 4' in script
  assert '"failed_stage": None if status == "pass" else stage' in script
  assert '"provenance": {"sim_lab": git_source(simlab_root)' in script
  assert '"metadrive_source": metadrive_source_metadata()' in script
  assert '"gpu_before": parse_gpu_snapshot(gpu_before)' in script
  assert '"gpu_after": parse_gpu_snapshot(gpu_after)' in script
  assert "HOST_STACK_OUTPUT=outputs/host-stack/host-stack.json" in host_stability


def test_host_probe_preserves_pre_manifest_host_context():
  script = (ROOT / "scripts/run_host_stability_probe.sh").read_text(encoding="utf-8")

  assert '"schema_version": 2' in script
  assert '"host_start": {"wsl_kernel": kernel, "uptime_s": float(uptime), "gpu": gpu or None}' in script
  assert '"host_end": {"wsl_kernel": kernel, "uptime_s": float(uptime), "gpu": gpu or None}' in script


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
  (run / "captures/road-frame-000001.png").write_bytes(b"png")
  sample = {"split": "analysis_only", "image": "captures/road-frame-000001.png",
            "labels": {"route_lateral_error_m": 0, "route_heading_error_deg": 0, "route_reference_curvature_1pm": 0}}
  (run / "dataset_manifest.jsonl").write_text(json.dumps(sample) + "\n")
  dataset = {"scope": "carla_analysis_only_not_control_training", "joined_samples": 1, "captured_frames": 1,
             "dropped_frames": 0, "valid": True}
  (run / "dataset_summary.json").write_text(json.dumps(dataset))
  (run / "manifest.json").write_text(json.dumps({"scope": "carla_v02_adapter_pilot_not_road_qualification",
                                                     "capture": {"enabled": True}}))
  (run / "summary.json").write_text(json.dumps({"schema_version": 1, "pilot_status": "integrated-but-not-stable",
                                                   "dataset_summary": dataset}))

  result = subprocess.run([sys.executable, str(ROOT / "scripts/verify_carla_adapter_pilot.py"), str(run)],
                          check=True, capture_output=True, text=True)

  assert json.loads(result.stdout)["dataset"] == {"valid": True, "joined_samples": 1, "dropped_frames": 0}


def test_carla_pilot_summary_tracks_dataset_and_after_filter(tmp_path):
  for timestamp, joined in (("20260903T010000Z", 2), ("20260903T020000Z", 3)):
    run = tmp_path / f"carla-city-mixed-pilot-{timestamp}-abc"; run.mkdir()
    (run / "summary.json").write_text(json.dumps({"schema_version": 1, "pilot_status": "integrated-but-not-stable",
      "reasons": ["lane_departure"], "dataset_summary": {"valid": True, "joined_samples": joined}}))

  result = subprocess.run([sys.executable, str(ROOT / "scripts/summarize_carla_adapter_pilot.py"), str(tmp_path),
                           "--after", "20260903T010000Z"], check=True, capture_output=True, text=True)

  summary = json.loads(result.stdout)
  assert summary["run_count"] == 1 and summary["dataset_valid_count"] == 1 and summary["dataset_joined_samples"] == 3


def test_carla_adapter_public_evidence_is_aggregate_and_source_bound(tmp_path):
  source = tmp_path / "summary.json"
  source.write_text(json.dumps({"schema_version": 1, "scope": "carla_v02_adapter_pilot_not_road_qualification",
                                "run_count": 2, "status_counts": {"integrated-but-not-stable": 2},
                                "reason_counts": {"lane_departure": 2}, "runs": [{"host": "private"}]}))
  output = tmp_path / "public"

  subprocess.run([sys.executable, str(ROOT / "scripts/build_carla_adapter_public_evidence.py"), str(source),
                  "--output-dir", str(output), "--departure-contract",
                  "historical_lane_sensor_event_pre_route_ground_truth_threshold"], check=True)
  subprocess.run([sys.executable, str(ROOT / "scripts/verify_carla_adapter_public_evidence.py"), str(source),
                  "--output-dir", str(output), "--departure-contract",
                  "historical_lane_sensor_event_pre_route_ground_truth_threshold"], check=True)

  serialized = (output / "evidence.json").read_text(encoding="utf-8")
  assert "private" not in serialized and '"run_count": 2' in serialized


def test_performance_case_study_is_source_bound_and_public_safe(tmp_path):
  def summary(path, *, outcome, rmse, delay=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"scenario_id": "synthetic", "target_delay_ms": delay, "validity": "valid",
                                "outcome": outcome, "reasons": [], "metrics": {"lateral_rmse_m": rmse,
                                "camera_frames_published": 1200, "lane_departure_occurred": outcome == "fail",
                                "collision_occurred": False}}), encoding="utf-8")
    return path

  gamma_baseline = summary(tmp_path / "gamma-baseline.json", outcome="fail", rmse=1.0)
  gamma_candidates = [summary(tmp_path / f"gamma-{index}.json", outcome="pass", rmse=0.2 + index / 100)
                      for index in range(3)]
  delay_root = tmp_path / "matrix"
  for delay in (0, 50, 100, 150):
    for index in range(3):
      summary(delay_root / f"{delay}-{index}" / "summary.json", outcome="pass", rmse=0.25, delay=delay)
  tight_baseline = summary(tmp_path / "tight-baseline.json", outcome="fail", rmse=0.8)
  tight_fixed = [summary(tmp_path / f"tight-fixed-{index}.json", outcome="pass", rmse=0.4) for index in range(3)]
  tight_heldout = [summary(tmp_path / f"tight-heldout-{index}.json", outcome="pass", rmse=0.5) for index in range(3)]
  tuning = tmp_path / "tuning.json"
  tuning.write_text(json.dumps({"status": "selected", "selected_steer_ratio": 8.0, "changed_candidate_selected": False,
                                "candidates": [{"summary": "/private/summary.json", "steer_ratio": 8.0,
                                "validity": "valid", "outcome": "fail", "reasons": [], "lateral_rmse_m": 1.0,
                                "eligible": True}]}), encoding="utf-8")
  evaluation = tmp_path / "evaluation.json"
  evaluation.write_text(json.dumps({"candidate_success": False, "next_step": "retain_negative_result_no_changed_candidate",
                                    "reason": "baseline_ratio_selected_no_actuation_change"}), encoding="utf-8")
  output = tmp_path / "public"
  command = [sys.executable, str(ROOT / "scripts/build_performance_case_study.py"), "--pretrained-tuning", str(tuning),
             "--pretrained-evaluation", str(evaluation), "--gamma-baseline", str(gamma_baseline),
             "--gamma-candidate", *(str(path) for path in gamma_candidates), "--gamma-delay-root", str(delay_root),
             "--tight-baseline", str(tight_baseline), "--tight-fixed", *(str(path) for path in tight_fixed),
             "--tight-heldout", *(str(path) for path in tight_heldout), "--output-dir", str(output)]
  subprocess.run(command, check=True)
  subprocess.run([sys.executable, str(ROOT / "scripts/verify_performance_case_study.py"), *command[2:]], check=True)
  evidence = (output / "evidence.json").read_text(encoding="utf-8")
  assert "simulator_specialist_improvement_case_study" in evidence
  assert str(tmp_path) not in evidence and "telemetry.csv" not in evidence


def test_camera_color_evaluation_retains_identity_audit_without_launching_runs(tmp_path):
  audit = tmp_path / "audit.json"
  audit.write_text(json.dumps({"scope": "camera_domain_moment_match_diagnostic_not_perception_or_road_performance",
                                "recommended_environment_overlay": {"camera_color_affine": {
                                  "gain_rgb": [1.0, 1.0, 1.0], "bias_rgb": [0.0, 0.0, 0.0]}}}), encoding="utf-8")
  output = tmp_path / "evaluation"
  subprocess.run([sys.executable, str(ROOT / "scripts/run_pretrained_camera_color_evaluation.py"), "--audit", str(audit),
                  "--fixed-scenario", "unused.yaml", "--heldout-scenario", "unused.yaml", "--output-root", str(output)], check=True)
  result = json.loads((output / "evaluation.json").read_text(encoding="utf-8"))
  assert result["candidate_success"] is False and result["reason"] == "identity_color_affine"


def test_camera_structure_audit_is_hash_bound_and_non_semantic(tmp_path):
  from PIL import Image
  import numpy as np

  simulator = tmp_path / "simulator.png"
  reference = tmp_path / "reference.png"
  Image.fromarray(np.zeros((20, 30, 3), dtype=np.uint8)).save(simulator)
  Image.fromarray(np.full((20, 30, 3), 100, dtype=np.uint8)).save(reference)
  output = tmp_path / "audit.json"

  subprocess.run([sys.executable, str(ROOT / "scripts/audit_camera_structure.py"),
                  "--sim-frame", str(simulator), "--reference-frame", str(reference), "--output", str(output)],
                 check=True)
  audit = json.loads(output.read_text(encoding="utf-8"))

  assert audit["scope"] == "unmatched_scene_structure_diagnostic_not_segmentation_accuracy_or_driving_performance"
  assert len(audit["simulator"]["frames"][0]["sha256"]) == 64
  assert audit["limitations"] == ["frame_sets_are_not_scene_matched", "fixed_vertical_bands_are_not_semantic_masks",
                                  "ratios_identify_domain_shift_but_not_model_causality"]


def test_portfolio_readiness_exposes_optional_carla_adapter_source_check():
  script = (ROOT / "scripts/verify_portfolio_readiness.py").read_text(encoding="utf-8")
  assert 'parser.add_argument("--carla-adapter-summary", type=Path)' in script
  assert 'checks["carla_adapter_retained_source"] = "pass"' in script


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


def test_committed_carla_adapter_public_sample_is_sanitized_and_scoped():
  sample_dir = ROOT / "examples/v0.2-carla-adapter-pilot"
  evidence = json.loads((sample_dir / "evidence.json").read_text(encoding="utf-8"))
  readme = (sample_dir / "README.md").read_text(encoding="utf-8")

  assert evidence["scope"] == "carla_adapter_pilot_public_summary_only"
  assert evidence["departure_contract"] == "historical_lane_sensor_event_pre_route_ground_truth_threshold"
  assert evidence["formal"] == {"run_count": 10, "status_counts": {"integrated-but-not-stable": 10},
                                 "reason_counts": {"lane_departure": 10}}
  assert all(token not in json.dumps(evidence) for token in ("172.28.", "C:\\", "run_id", "telemetry"))
  assert "does not demonstrate successful OpenPilot driving" in readme
