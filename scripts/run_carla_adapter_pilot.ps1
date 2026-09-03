param(
  [string]$CarlaExe = "$env:USERPROFILE\CARLA_0.9.16\CarlaUE4.exe",
  [string]$WslDistro = "Ubuntu-24.04",
  [string]$OpenpilotRoot = "/home/hyunsung/src/openpilot",
  [string]$SimlabRoot = "/home/hyunsung/src/openpilot-sim-lab",
  [string]$HostIp = "",
  [int]$Attempts = 10,
  [int]$MeasurementSeconds = 60,
  [int]$CaptureEveryNFrames = 0,
  [int]$Port = 2000,
  [string]$OutputRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) "outputs\carla-adapter-pilot")
)

$ErrorActionPreference = "Stop"
if ($Attempts -lt 1 -or $CaptureEveryNFrames -lt 0) { throw "attempt and capture values must be non-negative" }
if (-not (Test-Path -LiteralPath $CarlaExe -PathType Leaf)) { throw "CARLA executable is missing: $CarlaExe" }
if ([string]::IsNullOrWhiteSpace($HostIp)) {
  $route = & wsl.exe -d $WslDistro -- ip route show default
  $match = [regex]::Match(($route -join " "), "default via (?<host>[^ ]+)")
  if (-not $match.Success) { throw "cannot determine WSL gateway; pass -HostIp" }
  $HostIp = $match.Groups["host"].Value
}
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$anyFailure = $false
for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
  $attemptRoot = Join-Path $OutputRoot ((Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ") + "-attempt" + $attempt.ToString("00"))
  New-Item -ItemType Directory -Force -Path $attemptRoot | Out-Null
  $server = Start-Process -FilePath $CarlaExe -ArgumentList @("-RenderOffScreen", "-nosound", "-quality-level=Low") -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $attemptRoot "server.stdout.log") -RedirectStandardError (Join-Path $attemptRoot "server.stderr.log")
  $failure = $null
  $pilotRun = $null
  try {
    $deadline = (Get-Date).AddSeconds(120)
    do {
      & wsl.exe -d $WslDistro -- "$OpenpilotRoot/.venv/bin/python" "$SimlabRoot/scripts/carla_smoke_preflight.py" --connect --host $HostIp --port $Port --timeout-s 5 | Out-File (Join-Path $attemptRoot "connect.log") -Append
      if ($LASTEXITCODE -eq 0) { break }
      Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    if ($LASTEXITCODE -ne 0) { throw "CARLA server did not become ready within 120 seconds" }
    $asset = "$SimlabRoot/outputs/carla-adapter-pilot/routes/Town04-city-mixed-$attempt.json"
    & wsl.exe -d $WslDistro -- "$OpenpilotRoot/.venv/bin/python" "$SimlabRoot/scripts/build_carla_city_route_asset.py" --host $HostIp --port $Port --output $asset | Tee-Object -FilePath (Join-Path $attemptRoot "route-build.log")
    if ($LASTEXITCODE -ne 0) { throw "route asset build failed" }
    $pilotArgs = @("$OpenpilotRoot/.venv/bin/python", "$SimlabRoot/scripts/run_carla_adapter_pilot.py", "--openpilot-root", $OpenpilotRoot, "--route-asset", $asset, "--host", $HostIp, "--port", $Port, "--measurement-s", $MeasurementSeconds, "--output-root", "$SimlabRoot/outputs/carla-adapter-pilot")
    if ($CaptureEveryNFrames -gt 0) { $pilotArgs += @("--capture-every-n-frames", $CaptureEveryNFrames) }
    $pilotRun = & wsl.exe -d $WslDistro -- @pilotArgs | Tee-Object -FilePath (Join-Path $attemptRoot "pilot.log")
    if ($LASTEXITCODE -ne 0) { throw "adapter pilot failed" }
  } catch {
    $failure = $_.Exception.Message
  } finally {
    # CarlaUE4.exe launches the rendering process as a child.  Killing only
    # the launcher leaves GPU-consuming CarlaUE4-Win64-Shipping children alive.
    & taskkill.exe /PID $server.Id /T /F *> $null
    Start-Sleep -Seconds 2
    [ordered]@{
      schema_version = 1
      scope = "carla_v02_adapter_pilot_not_road_qualification"
      attempt = $attempt
      status = if ($null -eq $failure) { "completed" } else { "invalid" }
      failure = $failure
      pilot_run = $pilotRun
      server_pid = $server.Id
      server_stopped = $null -eq (Get-Process -Id $server.Id -ErrorAction SilentlyContinue)
      host = $HostIp
      port = $Port
      dynamic_traffic_count = 0
      capture_every_n_frames = $CaptureEveryNFrames
      logs = @{ connect = "connect.log"; server_stdout = "server.stdout.log"; server_stderr = "server.stderr.log" }
    } | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $attemptRoot "attempt.json") -Encoding utf8
  }
  if ($null -ne $failure) { $anyFailure = $true; Write-Error "attempt $attempt invalid: $failure" }
}
if ($anyFailure) { exit 1 }
