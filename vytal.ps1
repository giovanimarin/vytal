#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Position=0, Mandatory=$true)][ValidateSet('install','start')][string]$Command,
    [string]$Address,
    [string]$DatabasePath,
    [string]$ApkPath,
    [string]$Device
)
$ErrorActionPreference = 'Stop'
try {
    if ($env:OS -ne 'Windows_NT') { throw 'Este launcher requer Windows. Consulte docs/android/HEALTH-CONNECT.md para outros sistemas.' }
    Import-Module (Join-Path $PSScriptRoot 'scripts/windows/Vytal.Local.psm1') -Force -DisableNameChecking
    Assert-VytalLocalEnvironment
    if ($Command -eq 'install') {
        Install-Vytal -Root $PSScriptRoot -ApkPath $ApkPath -Device $Device -DatabasePath $DatabasePath
    } else {
        Start-Vytal -Root $PSScriptRoot -Address $Address -DatabasePath $DatabasePath -Device $Device
    }
} catch {
    Write-Host ('Vytal: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
