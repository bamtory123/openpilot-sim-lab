from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path


def _svg(points: list[tuple[int, float]], title: str, unit: str) -> str:
  width, height, margin = 720, 360, 48
  values = [point[1] for point in points] or [0.0]
  lower, upper = min(values), max(values)
  if lower == upper:
    lower, upper = lower - 1, upper + 1
  path = " ".join(f"{margin + index * (width - 2 * margin) / max(1, len(points)-1):.1f},{height-margin-(value-lower)*(height-2*margin)/(upper-lower):.1f}" for index, value in points)
  return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><style>text{{font-family:sans-serif}}.axis{{stroke:#555}}.line{{fill:none;stroke:#0b6;stroke-width:2}}</style><text x="{margin}" y="24">{title} ({unit})</text><line class="axis" x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}"/><line class="axis" x1="{margin}" y1="{margin}" x2="{margin}" y2="{height-margin}"/><polyline class="line" points="{path}"/></svg>'''


def generate_report(results_root: Path, output: Path) -> Path:
  summaries = []
  manifests = []
  for path in sorted(results_root.rglob("summary.json")):
    summaries.append(json.loads(path.read_text(encoding="utf-8")))
    manifest = path.with_name("manifest.json")
    if manifest.is_file():
      manifests.append(json.loads(manifest.read_text(encoding="utf-8")))
  grouped = defaultdict(list)
  for summary in summaries:
    grouped[summary["target_delay_ms"]].append(summary)
  lines = ["# MetaDrive Repeatability Study", "", "This report compares deterministic camera transport-delay conditions on one fixed two-lane loop map. It is not a statistical validation or real-vehicle result.", "", "| Delay (ms) | Valid runs | Valid failures | Invalid runs | Valid-failure reasons | Invalid reasons | Median active time (s) | Median lateral RMSE (m) |", "|---:|---:|---:|---:|---|---|---:|---:|"]
  graph_points = []
  for delay in sorted(grouped):
    runs = grouped[delay]
    valid = [run for run in runs if run["validity"] == "valid"]
    failures = sum(run["outcome"] == "fail" for run in valid)
    invalid = len(runs) - len(valid)
    failure_counts = Counter(reason for run in valid for reason in run.get("reasons", []))
    invalid_counts = Counter(reason for run in runs if run["validity"] != "valid" for reason in run.get("reasons", []))
    failures_text = ", ".join(f"{reason}:{count}" for reason, count in sorted(failure_counts.items())) or "-"
    invalid_text = ", ".join(f"{reason}:{count}" for reason, count in sorted(invalid_counts.items())) or "-"
    rms = sorted(run["metrics"].get("lateral_rmse_m") for run in valid if run["metrics"].get("lateral_rmse_m") is not None)
    median = rms[len(rms)//2] if rms else None
    active_times = sorted(run["metrics"].get("active_time_s") for run in runs if run["metrics"].get("active_time_s") is not None)
    active_median = active_times[len(active_times)//2] if active_times else None
    lines.append(f"| {delay} | {len(valid)} | {failures} | {invalid} | {failures_text} | {invalid_text} | {active_median if active_median is not None else 'n/a'} | {median if median is not None else 'n/a'} |")
    if median is not None:
      graph_points.append((delay, median))
  diagnostics = [run["metrics"] for runs in grouped.values() for run in runs if run["metrics"].get("model_valid_coverage_ratio") is not None]
  if diagnostics:
    lines.extend(["", "## Model inference diagnostics", "",
                  "| Metric | Median across recorded runs |", "|---|---:|",
                  f"| model valid coverage | {sorted(metric['model_valid_coverage_ratio'] for metric in diagnostics)[len(diagnostics)//2]:.3f} |",
                  f"| model path horizon (m) | {sorted(metric['model_path_horizon_median_m'] for metric in diagnostics)[len(diagnostics)//2]:.3f} |",
                  f"| model terminal speed (m/s) | {sorted(metric['model_path_terminal_speed_median_mps'] for metric in diagnostics)[len(diagnostics)//2]:.3f} |"])
  coverage = [run["metrics"] for runs in grouped.values() for run in runs
              if run["metrics"].get("telemetry_coverage_ratio") is not None and run["metrics"].get("road_camera_coverage_ratio") is not None]
  if coverage:
    lines.extend(["", "## Measurement coverage", "", "| Metric | Median across recorded runs |", "|---|---:|",
                  f"| telemetry coverage | {sorted(metric['telemetry_coverage_ratio'] for metric in coverage)[len(coverage)//2]:.3f} |",
                  f"| road-camera coverage | {sorted(metric['road_camera_coverage_ratio'] for metric in coverage)[len(coverage)//2]:.3f} |"])
  if manifests:
    values = lambda key: sorted({str(manifest[key]) for manifest in manifests if manifest.get(key) is not None})
    temperatures = sorted(int(manifest["gpu_runtime_snapshot"]["temperature_c"]) for manifest in manifests
                          if manifest.get("gpu_runtime_snapshot", {}).get("temperature_c", "").isdigit())
    lines.extend(["", "## Host provenance", "",
                  f"- GPU: {', '.join(values('gpu')) or 'not recorded'}",
                  f"- Driver: {', '.join(values('driver')) or 'not recorded'}",
                  f"- Distinct WSL boot IDs: {len(values('wsl_boot_id'))}",
                  f"- GPU start temperature range: {f'{temperatures[0]}–{temperatures[-1]} °C' if temperatures else 'not recorded'}"])
  output.parent.mkdir(parents=True, exist_ok=True)
  output.write_text("\n".join(lines) + "\n", encoding="utf-8")
  output.with_suffix(".svg").write_text(_svg(graph_points, "Median lateral RMSE", "m"), encoding="utf-8")
  return output
