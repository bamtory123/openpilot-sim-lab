[CmdletBinding()]
param(
  [string]$WslDistro = "Ubuntu-24.04",
  [string]$OpenpilotRoot = "/home/hyunsung/src/openpilot",
  [string]$SimlabRoot = "/home/hyunsung/src/openpilot-sim-lab",
  [string]$Scenario = "/home/hyunsung/src/openpilot-sim-lab/configs/scenarios/md_default_loop_lane0_host_confirmation_v1.yaml",
  [string]$OutputRoot = "/home/hyunsung/src/openpilot-sim-lab/outputs/host-probe"
)

$ErrorActionPreference = "Stop"
$startedAt = (Get-Date).ToUniversalTime()
$shareRoot = "\\wsl.localhost\$WslDistro" + ($OutputRoot -replace "/", "\")
$eventPath = Join-Path $shareRoot ("windows-host-events-" + $startedAt.ToString("yyyyMMddTHHmmssZ") + ".json")
$wrapperPath = Join-Path $shareRoot ("windows-host-probe-" + $startedAt.ToString("yyyyMMddTHHmmssZ") + ".json")
$runnerExit = $null
$failure = $null

try {
  $command = "cd '$SimlabRoot' && OPENPILOT_ROOT='$OpenpilotRoot' OPENPILOT_PYTHON='$OpenpilotRoot/.venv/bin/python' scripts/run_host_stability_probe.sh '$Scenario' '$OutputRoot'"
  & wsl.exe -d $WslDistro -- bash -lc $command
  $runnerExit = $LASTEXITCODE
  if ($runnerExit -ne 0) { throw "host probe exited with code $runnerExit" }
} catch {
  $failure = $_.Exception.Message
} finally {
  & (Join-Path $PSScriptRoot "collect_windows_wsl_events.ps1") -Since $startedAt -Until (Get-Date).ToUniversalTime() -OutputPath $eventPath
  $payload = [ordered]@{
    schema_version = 1
    scope = "bounded_host_probe_windows_event_correlation_only"
    started_at_utc = $startedAt.ToString("o")
    completed_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    wsl_distro = $WslDistro
    scenario = $Scenario
    output_root = $OutputRoot
    runner_exit_code = $runnerExit
    windows_event_artifact = $eventPath
    status = if ($null -eq $failure) { "pass" } else { "fail" }
    failure = $failure
  } | ConvertTo-Json -Depth 3
  [System.IO.File]::WriteAllText($wrapperPath, $payload + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
}

Write-Host "Host probe/event evidence: $wrapperPath"
if ($null -ne $failure) { throw $failure }
