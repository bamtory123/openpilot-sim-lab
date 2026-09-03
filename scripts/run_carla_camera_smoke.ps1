param(
  [string]$CarlaExe = "$env:USERPROFILE\CARLA_0.9.16\CarlaUE4.exe",
  [string]$WslDistro = "Ubuntu-24.04",
  [string]$OpenpilotPython = "/home/hyunsung/src/openpilot/.venv/bin/python",
  [string]$SimlabRoot = "/home/hyunsung/src/openpilot-sim-lab",
  [string]$HostIp = "",
  [int]$Port = 2000,
  [int]$StartupTimeoutSeconds = 60,
  [string]$OutputRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) "outputs\carla-smoke")
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $CarlaExe -PathType Leaf)) { throw "CARLA executable is missing: $CarlaExe" }
if ([string]::IsNullOrWhiteSpace($HostIp)) {
  $defaultRoute = & wsl.exe -d $WslDistro -- ip route show default
  if ($LASTEXITCODE -ne 0) { throw "cannot read the WSL default route; pass -HostIp explicitly" }
  $routeMatch = [regex]::Match(($defaultRoute -join " "), "default via (?<host>[^ ]+)")
  if (-not $routeMatch.Success) { throw "cannot find the WSL gateway; pass -HostIp explicitly" }
  $HostIp = $routeMatch.Groups["host"].Value
}

$runDirectory = Join-Path $OutputRoot ((Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ"))
New-Item -ItemType Directory -Force -Path $runDirectory | Out-Null
$serverOut = Join-Path $runDirectory "server.stdout.log"
$serverErr = Join-Path $runDirectory "server.stderr.log"
$connectLog = Join-Path $runDirectory "connect.log"
$clientLog = Join-Path $runDirectory "client.log"
$resultPath = Join-Path $runDirectory "result.json"
$startedAt = (Get-Date).ToUniversalTime().ToString("o")
$server = $null
$connectExit = $null
$clientExit = $null
$clientObservation = $null
$failure = $null

try {
  $server = Start-Process -FilePath $CarlaExe -ArgumentList @("-RenderOffScreen", "-nosound", "-quality-level=Low") `
    -WindowStyle Hidden -RedirectStandardOutput $serverOut -RedirectStandardError $serverErr -PassThru
  $connectArgs = @("-d", $WslDistro, "--", $OpenpilotPython, "$SimlabRoot/scripts/carla_smoke_preflight.py", "--connect",
    "--host", $HostIp, "--port", "$Port", "--timeout-s", "5")
  $deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
  do {
    & wsl.exe @connectArgs 2>&1 | Tee-Object -FilePath $connectLog -Append
    $connectExit = $LASTEXITCODE
    if ($connectExit -eq 0) { break }
    Start-Sleep -Seconds 2
  } while ((Get-Date) -lt $deadline)
  if ($connectExit -ne 0) { throw "CARLA did not accept a WSL client connection within $StartupTimeoutSeconds seconds" }

  $cameraArgs = @($connectArgs + "--camera-state-control-smoke")
  & wsl.exe @cameraArgs 2>&1 | Tee-Object -FilePath $clientLog
  $clientExit = $LASTEXITCODE
  if ($clientExit -ne 0) { throw "CARLA camera/state/control smoke failed" }
  $clientResult = Get-Content -Raw -LiteralPath $clientLog | ConvertFrom-Json
  $clientObservation = [ordered]@{
    client_version = $clientResult.client_version
    server_version = $clientResult.server_version
    camera = $clientResult.camera
    vehicle_control = $clientResult.vehicle_control
    vehicle_speed_mps = $clientResult.vehicle_speed_mps
    actors_destroyed = $clientResult.actors_destroyed
    world_settings_restored = $clientResult.world_settings_restored
  }
} catch {
  $failure = $_.Exception.Message
} finally {
  if ($null -ne $server) {
    # The Unreal renderer is a child of CarlaUE4.exe; terminate the process
    # tree so an interrupted smoke cannot retain GPU memory.
    & taskkill.exe /PID $server.Id /T /F *> $null
    Start-Sleep -Seconds 2
  }
  $serverStopped = $null -eq (Get-Process -Id $server.Id -ErrorAction SilentlyContinue)
  [ordered]@{
    schema_version = 2
    scope = "carla_client_or_connectivity_smoke_only"
    status = if ($null -eq $failure) { "pass" } else { "fail" }
    started_at_utc = $startedAt
    completed_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    carla_exe = $CarlaExe
    host = $HostIp
    port = $Port
    server_pid = if ($null -eq $server) { $null } else { $server.Id }
    server_stopped = if ($null -eq $server) { $null } else { $serverStopped }
    connect_exit_code = $connectExit
    client_exit_code = $clientExit
    client_observation = $clientObservation
    failure = $failure
    logs = @{ server_stdout = "server.stdout.log"; server_stderr = "server.stderr.log"; connect = "connect.log"; client = "client.log" }
  } | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $resultPath -Encoding utf8
}

Write-Host "CARLA smoke evidence: $runDirectory"
if ($null -ne $failure) { throw $failure }
