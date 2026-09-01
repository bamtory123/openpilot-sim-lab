[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$OutputPath,
  [datetime]$Since = (Get-Date).AddHours(-1),
  [datetime]$Until = (Get-Date)
)

$providers = @(
  'Microsoft-Windows-Hyper-V-VmSwitch',
  'Display',
  'nvlddmkm',
  'LxssManager'
)

$systemEvents = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; StartTime = $Since; EndTime = $Until } -ErrorAction SilentlyContinue |
  Where-Object {
    $providers -contains $_.ProviderName -or
    $_.Message -match 'WSL|NVIDIA|display driver|GPU'
  })

$vmSwitchEvents = @(Get-WinEvent -FilterHashtable @{ LogName = 'Microsoft-Windows-Hyper-V-VmSwitch-Operational'; StartTime = $Since; EndTime = $Until } -ErrorAction SilentlyContinue |
  Where-Object {
    $_.Message -match 'WSL|NVIDIA|display driver|GPU' -and
    -not ($_.Id -eq 285 -and $_.Message -match 'OID_GEN_STATISTICS')
  })

$events = @($systemEvents + $vmSwitchEvents | Sort-Object TimeCreated | Select-Object TimeCreated,
  @{ Name = 'LogName'; Expression = { $_.LogName } }, ProviderName, Id, LevelDisplayName, Message)

$payload = [ordered]@{
  schema_version = 1
  collected_at = (Get-Date).ToUniversalTime().ToString('o')
  since = $Since.ToUniversalTime().ToString('o')
  until = $Until.ToUniversalTime().ToString('o')
  events = @($events)
}

$parent = Split-Path -Parent $OutputPath
if ($parent) {
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
}
$payload | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 -Path $OutputPath
Write-Output "Wrote $($payload.events.Count) Windows WSL/GPU events to $OutputPath"
