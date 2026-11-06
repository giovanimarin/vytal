#requires -Version 5.1
# Dependency-free tests: run on Windows PowerShell 5.1 and pwsh 7.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = Split-Path $PSScriptRoot -Parent
Import-Module (Join-Path $root 'scripts/windows/Vytal.Local.psm1') -Force -DisableNameChecking
$script:count = 0
function Check([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "FAIL: $Message" }
    $script:count++
}
function Fails([scriptblock]$Action, [string]$Pattern) {
    $caught = $null
    try { & $Action | Out-Null } catch { $caught = $_.Exception.Message }
    Check ($null -ne $caught -and $caught -match $Pattern) "expected error: $Pattern; actual: $caught"
}
function Network([string]$IP, [string]$Profile='Private', [bool]$Physical=$true, [bool]$Up=$true, [bool]$Gateway=$true) {
    return [pscustomobject]@{Address=$IP;Profile=$Profile;Physical=$Physical;Up=$Up;Gateway=$Gateway;Alias='synthetic'}
}
foreach ($ip in @('10.0.0.1','172.16.0.1','172.31.255.254','192.168.1.10')) { Check (Test-PrivateIPv4 $ip) "private IPv4 $ip" }
foreach ($ip in @('127.0.0.1','0.0.0.0','169.254.1.2','172.32.0.1','172.15.0.1','8.8.8.8','::1','192.168.1.999','invalid','')) { Check (-not (Test-PrivateIPv4 $ip)) "reject IPv4 $ip" }
$one = @(Network '192.168.1.20')
Check ((Select-VytalAddress $one '') -eq '192.168.1.20') 'single private interface'
Check ((Select-VytalAddress $one '192.168.1.20') -eq '192.168.1.20') 'explicit eligible interface'
$two = @((Network '192.168.1.20'), (Network '10.0.0.20'))
Check ((Select-VytalAddress $two '' {param($items) '2'}) -eq '192.168.1.20') 'multiple interfaces selection (sorted)'
foreach ($choice in @('0','3','x','')) { Fails { Select-VytalAddress $two '' {param($items) $choice}.GetNewClosure() } 'Selecao' }
Fails { Select-VytalAddress $one '10.0.0.99' } 'IP indisponivel'
Fails { Select-VytalAddress @() '' } 'Nenhuma rede'
foreach ($bad in @((Network '192.168.1.20' 'Public'),(Network '192.168.1.20' 'Private' $false),(Network '192.168.1.20' 'Private' $true $false),(Network '192.168.1.20' 'Private' $true $true $false),(Network '169.254.1.20'))) {
    Fails { Select-VytalAddress @($bad) '' } 'Nenhuma rede'
}
Check ((Select-VytalAddress @((Network '10.1.2.3' 'DomainAuthenticated')) '') -eq '10.1.2.3') 'domain trusted interface'
foreach ($value in @('production','staging','test','unknown')) {
    $before=$env:ENVIRONMENT
    try { $env:ENVIRONMENT=$value; Fails { Assert-VytalLocalEnvironment } 'exclusivo' } finally { $env:ENVIRONMENT=$before }
}
$before=$env:K_SERVICE
try { $env:K_SERVICE='synthetic'; Fails { Assert-VytalLocalEnvironment } 'exclusivo' } finally { $env:K_SERVICE=$before }
Check ((Get-VytalPortAction $true $false $false) -eq 'start') 'free port starts'
Check ((Get-VytalPortAction $false $true $true) -eq 'reuse') 'owned healthy process reuses'
Fails { Get-VytalPortAction $false $false $true } 'Porta ocupada'
Fails { Get-VytalPortAction $false $true $false } 'Porta ocupada'
Check (-not (Test-VytalOwned $null '192.168.1.2')) 'missing PID state'
$self = Get-Process -Id $PID
$state = [pscustomobject]@{Pid=$PID;Address='192.168.1.2';StartTicks=$self.StartTime.ToUniversalTime().Ticks.ToString()}
Check (Test-VytalOwned $state '192.168.1.2') 'live worker ownership'
Check (-not (Test-VytalOwned $state '192.168.1.3')) 'different IP not reused'
$state.StartTicks='0'
Check (-not (Test-VytalOwned $state '192.168.1.2')) 'reused OS PID not trusted'
Check ((Select-VytalDevice @('List of devices attached','synthetic device') '') -eq 'synthetic') 'authorized ADB'
Check ($null -eq (Select-VytalDevice @('List of devices attached') '')) 'no phone -> manual installation'
Fails { Select-VytalDevice @('synthetic unauthorized') '' } 'RSA'
Fails { Select-VytalDevice @('synthetic offline') '' } 'offline'
Fails { Select-VytalDevice @('one device','two device') '' } 'Mais de um'
Check ((Select-VytalDevice @('one device','two device') 'two') -eq 'two') 'explicit device'
Fails { Select-VytalDevice @('one device') 'missing' } 'Serial ADB'

$temporary = Join-Path ([IO.Path]::GetTempPath()) ('vytal-launcher-test-' + [Guid]::NewGuid())
[IO.Directory]::CreateDirectory($temporary) | Out-Null
try {
    $fixture = Join-Path $temporary 'repo with spaces'
    [IO.Directory]::CreateDirectory((Join-Path $fixture 'backend/data')) | Out-Null
    $db = Join-Path $fixture 'backend/data/vytal.db'
    [IO.File]::WriteAllText($db,'synthetic-existing-data')
    Check ((Resolve-VytalDatabase $fixture '') -eq $db) 'backend DB preserved'
    $first = Initialize-VytalState $fixture ''
    $keyPath = Join-Path $fixture '.local-vytal/keys.json'
    $hash = (Get-FileHash $keyPath).Hash
    $second = Initialize-VytalState $fixture ''
    Check ($first.JWT_SECRET_KEY -eq $second.JWT_SECRET_KEY) 'stable JWT key after restart'
    Check ($first.SECRET_KEY -eq $second.SECRET_KEY) 'stable state key after restart'
    Check ((Get-FileHash $keyPath).Hash -eq $hash) 'keys byte-for-byte preserved'
    Check ([IO.File]::ReadAllText($db) -eq 'synthetic-existing-data') 'DB bytes unchanged'
    $config = Get-Content $first.CONFIG_PATH -Raw | ConvertFrom-Json
    Check ($config.cloud.provider -eq 'local' -and $config.local.db_path -eq $db) 'local config, absolute correct DB path'
    Check ($first.ALLOW_DEV_SEED -eq 'false') 'no synthetic seeding'
    Check ($first.ENVIRONMENT -eq 'local') 'local environment only'
    [IO.Directory]::CreateDirectory((Join-Path $fixture '.local-vytal/data')) | Out-Null
    $other = Join-Path $fixture '.local-vytal/data/vytal.db'
    [IO.File]::WriteAllText($other,'synthetic-pr24-data')
    Remove-Item (Join-Path $fixture '.local-vytal/windows-config.json')
    Fails { Resolve-VytalDatabase $fixture '' } 'Dois bancos'
    Check ((Resolve-VytalDatabase $fixture '.local-vytal/data/vytal.db') -eq $other) 'explicit DB choice without copying'
    $null = Initialize-VytalState $fixture '.local-vytal/data/vytal.db'
    Check ((Resolve-VytalDatabase $fixture '') -eq $other) 'remember DB choice'
    Check ((Get-FileHash $keyPath).Hash -eq $hash) 'PR24 keys reused'
    Check ([IO.File]::ReadAllText($db) -eq 'synthetic-existing-data' -and [IO.File]::ReadAllText($other) -eq 'synthetic-pr24-data') 'neither DB modified'
    [IO.File]::WriteAllText($keyPath,'{}')
    Fails { Initialize-VytalState $fixture '' } 'chaves invalido'
    Check ([IO.File]::ReadAllText($keyPath) -eq '{}') 'bad keys never rotated silently'
    [IO.File]::WriteAllText($keyPath,'not-json-synthetic-sensitive-marker')
    Fails { Read-VytalKeys $keyPath } '^Arquivo privado'

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $contents = Join-Path $temporary 'apk-contents'
    [IO.Directory]::CreateDirectory($contents) | Out-Null
    [IO.File]::WriteAllText((Join-Path $contents 'AndroidManifest.xml'),'synthetic-apk-not-installable')
    $apk = Join-Path $temporary 'source.apk'
    [IO.Compression.ZipFile]::CreateFromDirectory($contents, $apk)
    $target = Join-Path $temporary 'copied.apk'
    Copy-VytalApk $apk $target
    Check ((Get-FileHash $apk).Hash -eq (Get-FileHash $target).Hash) 'APK copied without modification'
    Copy-VytalApk $target $target
    Check (Test-Path $target) 'cached APK self-validation'
    $archive = Join-Path $temporary 'artifact.zip'
    $zip = [IO.Compression.ZipFile]::Open($archive, [IO.Compression.ZipArchiveMode]::Create)
    try { [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,$apk,'app-debug.apk') | Out-Null } finally { $zip.Dispose() }
    Copy-VytalApk $archive $target
    Check ((Get-FileHash $apk).Hash -eq (Get-FileHash $target).Hash) 'CI ZIP extraction'
    $badZip = Join-Path $temporary 'unsafe.zip'
    $zip = [IO.Compression.ZipFile]::Open($badZip, [IO.Compression.ZipArchiveMode]::Create)
    try { [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,$apk,'../app-debug.apk') | Out-Null } finally { $zip.Dispose() }
    Fails { Copy-VytalApk $badZip $target } 'ZIP incompat'
    Check (-not (Test-Path (Join-Path $temporary '../app-debug.apk'))) 'no archive traversal'
    Fails { Copy-VytalApk (Join-Path $temporary 'missing.apk') $target } 'nao encontrado'
    Fails { Copy-VytalApk (Join-Path $contents 'AndroidManifest.xml') $target } 'outro formato'
    [IO.File]::WriteAllText((Join-Path $temporary 'invalid.apk'), 'not-a-zip')
    Fails { Copy-VytalApk (Join-Path $temporary 'invalid.apk') $target } '.*'

    # Actual occupied TCP port, without assuming fixed ports are free on the worker.
    $listener = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback,0)
    try {
        $listener.Start()
        $port = $listener.LocalEndpoint.Port
        Check (-not (Test-VytalPort '127.0.0.1' $port)) 'occupied port detection'
    } finally { $listener.Stop() }
    Check (Test-VytalPort '127.0.0.1' $port) 'released port detection'
    Check (-not (Get-VytalHealth '127.0.0.1' $port)) 'unreachable health is not reported healthy'
} finally { Remove-Item $temporary -Recurse -Force }

# Parse entrypoint/module even on Linux. AST catches PS syntax errors before runtime.
foreach ($path in @('vytal.ps1','scripts/windows/Vytal.Local.psm1')) {
    $tokens=$null; $errors=$null
    $null=[Management.Automation.Language.Parser]::ParseFile((Join-Path $root $path),[ref]$tokens,[ref]$errors)
    Check ($errors.Count -eq 0) "PowerShell syntax: $path"
}
$tokens=$null; $errors=$null
$null=[Management.Automation.Language.Parser]::ParseFile((Join-Path $root 'scripts/windows/Vytal.Local.psm1'),[ref]$tokens,[ref]$errors)
$source=($tokens | Where-Object Kind -ne Comment | ForEach-Object Text) -join ' '
Check ($source -notmatch 'New-NetFirewallRule|Set-NetFirewall|netsh|Set-ExecutionPolicy|uninstall|gradlew|terraform|eas build') 'no firewall/policy/uninstall/build/provisioning mutations'
Write-Host "PASS: $script:count Windows launcher checks. Synthetic data only; no physical Samsung/Garmin validation."
