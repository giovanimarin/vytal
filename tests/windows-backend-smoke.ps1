#requires -Version 5.1
# Actual HTTP + SQLite using launcher's environment, temporary synthetic data only.
[CmdletBinding()]
param([string]$Python = 'python')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root=Split-Path $PSScriptRoot -Parent
Import-Module (Join-Path $root 'scripts/windows/Vytal.Local.psm1') -Force -DisableNameChecking
$temporary=Join-Path ([IO.Path]::GetTempPath()) ('vytal-windows-api-' + [Guid]::NewGuid())
[IO.Directory]::CreateDirectory($temporary) | Out-Null
$script:process=$null
$script:checks=0
function Check([bool]$Condition,[string]$Message) {
    if (-not $Condition) { throw $Message }
    $script:checks++
}
function Boot {
    $environment=Initialize-VytalState $temporary ''
    $listener=New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback,0)
    try { $listener.Start(); $script:port=$listener.LocalEndpoint.Port } finally { $listener.Stop() }
    $info=New-Object Diagnostics.ProcessStartInfo
    $info.FileName=$Python
    $info.Arguments="-m uvicorn app.main:app --host 127.0.0.1 --port $script:port"
    $info.WorkingDirectory=Join-Path $root 'backend'
    $info.UseShellExecute=$false
    $info.RedirectStandardError=$true
    $info.RedirectStandardOutput=$true
    foreach ($key in $environment.Keys) { $info.EnvironmentVariables[$key]=[string]$environment[$key] }
    $script:process=[Diagnostics.Process]::Start($info)
    $script:stderr=$script:process.StandardError.ReadToEndAsync()
    $script:stdout=$script:process.StandardOutput.ReadToEndAsync()
    $script:base="http://127.0.0.1:$script:port"
    for ($i=0;$i -lt 100;$i++) {
        if ($script:process.HasExited) { throw ('Backend failed with synthetic config: ' + $script:stderr.Result) }
        try { $health=Invoke-RestMethod "$script:base/health" -TimeoutSec 2; if ($health.status -eq 'ok') { return } } catch { }
        Start-Sleep -Milliseconds 100
    }
    throw 'Backend did not become healthy'
}
function Halt {
    if ($script:process) {
        if (-not $script:process.HasExited) { $script:process.Kill(); $script:process.WaitForExit() }
        $script:process.Dispose(); $script:process=$null
    }
}
function Request([string]$Method,[string]$Path,$Body=$null,[string]$Token='') {
    $options=@{Method=$Method;Uri=($script:base+$Path);ContentType='application/json';TimeoutSec=10}
    if ($null -ne $Body) { $options.Body=$Body | ConvertTo-Json -Depth 12 -Compress }
    if ($Token) { $options.Headers=@{Authorization="Bearer $Token"} }
    return Invoke-RestMethod @options
}
try {
    Boot
    $a=Request 'POST' '/api/v1/auth/register' @{email='windows-A@example.invalid';password='synthetic-password-123';name='Synthetic A'}
    $b=Request 'POST' '/api/v1/auth/register' @{email='windows-B@example.invalid';password='synthetic-password-123';name='Synthetic B'}
    $login=Request 'POST' '/api/v1/auth/login' @{email='windows-A@example.invalid';password='synthetic-password-123'}
    Check ([bool]$login.access_token) 'Login failed'
    $profile=Request 'GET' '/api/v1/users/me' $null $login.access_token
    Check ($profile.email -eq 'windows-A@example.invalid') 'Wrong authenticated profile'
    $record=@{category='Steps';id='synthetic-windows-id';origin='com.garmin.android.apps.connectmobile';start='2026-01-15T12:00:00Z';end='2026-01-15T13:00:00Z';values=@{count=123;unit='steps'};metadata=@{id='synthetic-windows-id'};native=@{synthetic=$true}}
    foreach ($retry in 1..2) { $null=Request 'POST' '/api/v1/health-connect/records' @{installation_id='synthetic-windows';records=@($record)} $login.access_token }
    $imported=Request 'GET' '/api/v1/health-connect/records' $null $login.access_token
    Check ($imported.retained_raw -eq 1 -and $imported.records[0].values.count -eq 123) 'Idempotent HC import failed'
    $other=Request 'GET' '/api/v1/health-connect/records' $null $b.access_token
    Check ($other.records.Count -eq 0) 'Cross-account data leak'
    $oldToken=$login.access_token
    Halt
    Boot
    $profile=Request 'GET' '/api/v1/users/me' $null $oldToken
    Check ($profile.email -eq 'windows-A@example.invalid') 'Session did not survive backend restart'
    $imported=Request 'GET' '/api/v1/health-connect/records' $null $oldToken
    Check ($imported.retained_raw -eq 1) 'SQLite data did not survive backend restart'
    $login=Request 'POST' '/api/v1/auth/login' @{email='windows-A@example.invalid';password='synthetic-password-123'}
    Check ([bool]$login.access_token) 'Login after restart failed'
    Write-Host "PASS: $script:checks real HTTP/SQLite Windows-launcher smoke checks; synthetic Garmin-shaped record, no device/real Garmin evidence."
} finally { Halt; Remove-Item $temporary -Recurse -Force }
