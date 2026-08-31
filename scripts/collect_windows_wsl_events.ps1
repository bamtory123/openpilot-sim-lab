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

$events = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; StartTime = $Since; EndTime = $Until } -ErrorAction SilentlyContinue |
  Where-Object {
    $providers -contains $_.ProviderName -or
    $_.Message -match 'WSL|NVIDIA|display driver|GPU'
  } |
  Select-Object TimeCreated, ProviderName, Id, LevelDisplayName, Message)

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
