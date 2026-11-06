#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Known successful HC development APK; no Android compilation on the user's PC.
$script:ApkRun = '42129619190'
$script:ApkRunUrl = 'https://github.com/giovanimarin/vytal/actions/runs/' + $script:ApkRun

function Assert-VytalLocalEnvironment {
    if ($env:K_SERVICE -or ($env:ENVIRONMENT -and $env:ENVIRONMENT -notin @('local','dev','development'))) {
        throw 'Launcher exclusivo de desenvolvimento local; ambiente gerenciado/producao/teste recusado.'
    }
}
function Test-PrivateIPv4([string]$Address) {
    $ip = $null
    if (-not [Net.IPAddress]::TryParse($Address, [ref]$ip) -or $ip.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork) { return $false }
    $bytes = $ip.GetAddressBytes()
    return ($bytes[0] -eq 10 -or ($bytes[0] -eq 172 -and $bytes[1] -ge 16 -and $bytes[1] -le 31) -or ($bytes[0] -eq 192 -and $bytes[1] -eq 168))
}
function Select-VytalAddress {
    param([object[]]$Candidates, [string]$Address, [scriptblock]$Choose = { param($items) Read-Host 'Escolha o numero da rede Wi-Fi/Ethernet do celular' })
    $eligible = @($Candidates | Where-Object { $_.Up -and $_.Gateway -and $_.Physical -and $_.Profile -in @('Private','DomainAuthenticated') -and (Test-PrivateIPv4 $_.Address) } | Sort-Object Address -Unique)
    if ($Address) {
        if ($Address -notin @($eligible | ForEach-Object { $_.Address })) { throw 'IP indisponivel ou rede nao privada. Use um IPv4 da interface Wi-Fi/Ethernet privada deste PC.' }
        return $Address
    }
    if (-not $eligible.Count) { throw 'Nenhuma rede fisica privada com IPv4/gateway. Conecte ao Wi-Fi do celular; em Configuracoes do Windows marque Privada somente se a rede for confiavel.' }
    if ($eligible.Count -eq 1) { return $eligible[0].Address }
    for ($i = 0; $i -lt $eligible.Count; $i++) { Write-Host ("{0}: {1} - {2}" -f ($i + 1), $eligible[$i].Alias, $eligible[$i].Address) }
    $selection = 0
    if (-not [int]::TryParse([string](& $Choose $eligible), [ref]$selection) -or $selection -lt 1 -or $selection -gt $eligible.Count) { throw 'Selecao de rede invalida; execute novamente ou use -Address 192.168.x.x.' }
    return $eligible[$selection - 1].Address
}
function Get-VytalNetwork {
    $adapters = @(Get-NetAdapter)
    $profiles = @(Get-NetConnectionProfile)
    return @(Get-NetIPConfiguration | ForEach-Object {
        $config = $_
        $adapter = @($adapters | Where-Object InterfaceIndex -eq $config.InterfaceIndex | Select-Object -First 1)
        $profile = @($profiles | Where-Object InterfaceIndex -eq $config.InterfaceIndex | Select-Object -First 1)
        if ($adapter.Count -and $profile.Count) {
            $addresses = @($config.IPv4Address | Where-Object { $null -ne $_ })
            if (-not $addresses.Count) { $addresses = @([pscustomobject]@{IPAddress=''}) }
            foreach ($ip in $addresses) {
                [pscustomobject]@{ Address=$ip.IPAddress; Alias=$config.InterfaceAlias; Up=($adapter[0].Status -eq 'Up'); Physical=$adapter[0].HardwareInterface; Profile=[string]$profile[0].NetworkCategory; Gateway=($null -ne $config.IPv4DefaultGateway) }
            }
        }
    })
}
function Resolve-VytalDatabase([string]$Root, [string]$DatabasePath) {
    $saved = Join-Path $Root '.local-vytal/windows-config.json'
    if (-not $DatabasePath -and (Test-Path $saved)) { $DatabasePath = (Get-Content $saved -Raw | ConvertFrom-Json).local.db_path }
    if (-not $DatabasePath) {
        $existing = @('backend/data/vytal.db', '.local-vytal/data/vytal.db' | ForEach-Object { Join-Path $Root $_ } | Where-Object { Test-Path $_ })
        if ($existing.Count -gt 1) { throw 'Dois bancos SQLite encontrados (backend/data e .local-vytal/data). Nenhum foi alterado. Escolha com -DatabasePath CAMINHO.' }
        $DatabasePath = if ($existing.Count) { $existing[0] } else { Join-Path $Root 'backend/data/vytal.db' }
    }
    if (-not [IO.Path]::IsPathRooted($DatabasePath)) { $DatabasePath = Join-Path $Root $DatabasePath }
    return [IO.Path]::GetFullPath($DatabasePath)
}
function Protect-VytalDirectory([string]$Path) {
    # No elevation, machine policy or firewall changes. Only private local files.
    if ($env:OS -eq 'Windows_NT') {
        $acl = New-Object Security.AccessControl.DirectorySecurity
        $acl.SetAccessRuleProtection($true, $false)
        $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
        $rule = New-Object Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
        $acl.AddAccessRule($rule)
        Set-Acl -LiteralPath $Path -AclObject $acl
    }
}
function Initialize-VytalState([string]$Root, [string]$DatabasePath) {
    $db = Resolve-VytalDatabase $Root $DatabasePath
    $directory = Join-Path $Root '.local-vytal'
    [IO.Directory]::CreateDirectory($directory) | Out-Null
    Protect-VytalDirectory $directory
    $keyPath = Join-Path $directory 'keys.json'
    if (-not (Test-Path $keyPath)) {
        $keys = @{}
        $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
        try {
            foreach ($name in @('SECRET_KEY','JWT_SECRET_KEY')) { $bytes = New-Object byte[] 48; $rng.GetBytes($bytes); $keys[$name] = [Convert]::ToBase64String($bytes) }
        } finally { $rng.Dispose() }
        # Exclusive creation: never rotate keys, including those from PR #24.
        $stream = [IO.File]::Open($keyPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        try { $bytes = [Text.Encoding]::UTF8.GetBytes(($keys | ConvertTo-Json)); $stream.Write($bytes,0,$bytes.Length) } finally { $stream.Dispose() }
    }
    $stored = Read-VytalKeys $keyPath
    foreach ($name in @('SECRET_KEY','JWT_SECRET_KEY')) {
        if (-not $stored.PSObject.Properties[$name] -or [string]::IsNullOrWhiteSpace($stored.$name)) { throw 'Arquivo local de chaves invalido. Nao foi sobrescrito; restaure sua copia privada.' }
    }
    $config = @{ cloud=@{provider='local'}; local=@{db_path=$db; data_dir=[IO.Path]::GetDirectoryName($db)} }
    $path = Join-Path $directory 'windows-config.json'
    [IO.File]::WriteAllText($path, ($config | ConvertTo-Json -Depth 4), (New-Object Text.UTF8Encoding($false)))
    return Get-VytalEnvironment $Root
}
function Get-VytalEnvironment([string]$Root) {
    $stored = Read-VytalKeys (Join-Path $Root '.local-vytal/keys.json')
    $path = Join-Path $Root '.local-vytal/windows-config.json'
    if ((Get-Content $path -Raw | ConvertFrom-Json).cloud.provider -ne 'local') { throw 'Configuracao SQLite local obrigatoria.' }
    foreach ($name in @('SECRET_KEY','JWT_SECRET_KEY')) {
        if (-not $stored.PSObject.Properties[$name] -or [string]::IsNullOrWhiteSpace($stored.$name)) { throw 'Chaves locais ausentes/invalidas; nao foram substituidas.' }
    }
    return @{ ENVIRONMENT='local'; CONFIG_PATH=$path; SECRET_KEY=$stored.SECRET_KEY; JWT_SECRET_KEY=$stored.JWT_SECRET_KEY; GOOGLE_CLIENT_ID='local-health-connect-only'; GOOGLE_CLIENT_SECRET='local-health-connect-only'; GOOGLE_REDIRECT_URI='http://localhost:8000/api/v1/connect/google_fit/callback'; ALLOW_DEV_SEED='false'; CORS_ORIGINS='[]' }
}
function Read-VytalKeys([string]$Path) {
    try { return Get-Content $Path -Raw | ConvertFrom-Json }
    catch { throw 'Arquivo privado de chaves ilegivel/invalido; seu conteudo nao sera exibido nem substituido.' }
}
function Invoke-VytalExternal([string]$File, [string[]]$Arguments) {
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Falha ao executar $([IO.Path]::GetFileName($File)). Leia a mensagem acima; nenhuma ferramenta de compilacao Android e necessaria." }
}
function Get-VytalTools([string]$Root, [switch]$Install) {
    $node = Get-Command node.exe -ErrorAction SilentlyContinue
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $node -or -not $npm) { throw 'Instale Node.js 22 LTS (https://nodejs.org), reabra o terminal e repita. Nao precisa de Java/Android Studio.' }
    $version = [string](& $node.Source --version)
    if ($version -notmatch '^v(\d+)\.') { throw 'Nao foi possivel identificar a versao Node.' }
    $major = [int]$Matches[1]
    if ($major -ne 22) { throw 'Use Node.js 22 LTS para o bundle compativel com o APK do CI.' }
    $python = Join-Path $Root '.venv/Scripts/python.exe'
    if (-not (Test-Path $python) -and $Install) {
        $py = Get-Command py.exe -ErrorAction SilentlyContinue
        $exe = Get-Command python.exe -ErrorAction SilentlyContinue
        if (-not $py -and -not $exe) { throw 'Instale Python 3.12 (https://www.python.org/downloads/windows/) com Python Launcher/PATH; reabra o terminal.' }
        if ($py) { Invoke-VytalExternal $py.Source @('-3.12','-m','venv',(Join-Path $Root '.venv')) }
        else { Invoke-VytalExternal $exe.Source @('-m','venv',(Join-Path $Root '.venv')) }
    }
    if (-not (Test-Path $python)) { throw 'Preparacao ausente. Execute .\vytal.ps1 install primeiro.' }
    Invoke-VytalExternal $python @('-c','import sys; assert (3,11) <= sys.version_info[:2] < (3,14)')
    return @{python=$python; npm=$npm.Source}
}
function Get-VytalApk([string]$Root, [string]$ApkPath) {
    $folder = Join-Path $Root '.local-vytal/apk'
    [IO.Directory]::CreateDirectory($folder) | Out-Null
    $target = Join-Path $folder 'app-debug.apk'
    if (-not $ApkPath -and (Test-Path $target)) { return $target }
    if (-not $ApkPath) {
        $gh = Get-Command gh.exe -ErrorAction SilentlyContinue
        if ($gh) {
            & $gh.Source run download $script:ApkRun --repo giovanimarin/vytal --name android-health-connect-debug-apk --dir $folder
            if ($LASTEXITCODE -eq 0 -and (Test-Path $target)) { return $target }
            Write-Warning 'Download automatico indisponivel. Nao e necessario autenticar o CLI; use o navegador.'
        }
        Write-Host "Abra $script:ApkRunUrl e baixe Artifacts > android-health-connect-debug-apk (pode exigir login GitHub)."
        Write-Host 'Selecione o ZIP/APK baixado. Nao use APK de origem desconhecida; nenhum build local sera executado.'
        Start-Process $script:ApkRunUrl
        Add-Type -AssemblyName System.Windows.Forms
        $dialog = New-Object Windows.Forms.OpenFileDialog
        $dialog.Title = 'Selecione o artefato Health Connect do CI (ZIP ou APK)'
        $dialog.Filter = 'Vytal Android|*.zip;*.apk'
        try {
            if ($dialog.ShowDialog() -ne 'OK') { throw 'Download cancelado. Baixe o artefato e repita install -ApkPath CAMINHO. Se expirou, um mantenedor deve regenerar o mesmo build no CI.' }
            $ApkPath = $dialog.FileName
        } finally { $dialog.Dispose() }
    }
    Copy-VytalApk $ApkPath $target
    return $target
}
function Copy-VytalApk([string]$Source, [string]$Target) {
    $sourcePath = [IO.Path]::GetFullPath($Source)
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw 'APK/ZIP nao encontrado. Informe -ApkPath CAMINHO.' }
    if ([IO.Path]::GetExtension($sourcePath) -eq '.zip') {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [IO.Compression.ZipFile]::OpenRead($sourcePath)
        try {
            $entries = @($zip.Entries | Where-Object { $_.FullName -eq 'app-debug.apk' })
            if ($entries.Count -ne 1) { throw 'ZIP incompatível: deve conter apenas um app-debug.apk na raiz, como o artefato do CI.' }
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entries[0], $Target, $true)
        } finally { $zip.Dispose() }
    } elseif ([IO.Path]::GetExtension($sourcePath) -eq '.apk') {
        if ($sourcePath -ne [IO.Path]::GetFullPath($Target)) { Copy-Item -LiteralPath $sourcePath -Destination $Target -Force }
    } else { throw 'Selecione o ZIP ou APK do CI, nao outro formato.' }
    # Structural validation only, not signing/provenance attestation.
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $apk = [IO.Compression.ZipFile]::OpenRead($Target)
    try { if (-not @($apk.Entries | Where-Object FullName -eq 'AndroidManifest.xml').Count) { throw 'APK invalido: AndroidManifest.xml ausente.' } } finally { $apk.Dispose() }
}
function Find-VytalAdb([string]$Root) {
    $command = Get-Command adb.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($folder in @((Join-Path $Root '.local-vytal/platform-tools'), "$env:LOCALAPPDATA/Android/Sdk/platform-tools", "$env:ANDROID_HOME/platform-tools")) {
        $path = Join-Path $folder 'adb.exe'
        if (Test-Path $path) { return $path }
    }
    return $null
}
function Select-VytalDevice([string[]]$Lines, [string]$Device) {
    $phones = @($Lines | Where-Object { $_ -match '^\S+\s+(device|unauthorized|offline)(\s|$)' } | ForEach-Object { $parts = $_ -split '\s+'; [pscustomobject]@{Serial=$parts[0];Status=$parts[1]} })
    if ($Device) {
        $phones = @($phones | Where-Object Serial -eq $Device)
        if (-not $phones.Count) { throw 'Serial ADB nao encontrado. Confira -Device com adb devices.' }
    }
    if ($phones.Count -gt 1) { throw 'Mais de um aparelho ADB. Use -Device SERIAL (veja adb devices).' }
    if (-not $phones.Count) { return $null }
    if ($phones[0].Status -eq 'unauthorized') { throw 'USB nao autorizado. Desbloqueie o Samsung e aceite a chave RSA da depuracao USB; repita.' }
    if ($phones[0].Status -ne 'device') { throw 'Aparelho offline. Reconecte o cabo USB de dados, desbloqueie e repita.' }
    return $phones[0].Serial
}
function Install-Vytal([string]$Root, [string]$ApkPath, [string]$Device, [string]$DatabasePath) {
    Assert-VytalLocalEnvironment
    Assert-VytalStoppedForInstall $Root
    $null = Initialize-VytalState $Root $DatabasePath
    $tools = Get-VytalTools $Root -Install
    Invoke-VytalExternal $tools.python @('-m','pip','install','-r',(Join-Path $Root 'backend/requirements-prod.txt'))
    Push-Location (Join-Path $Root 'mobile/vytal-app')
    try { Invoke-VytalExternal $tools.npm @('ci','--legacy-peer-deps') } finally { Pop-Location }
    $apk = Get-VytalApk $Root $ApkPath
    Copy-VytalApk $apk $apk
    Write-Host ('APK selecionado; SHA256 local: ' + (Get-FileHash -LiteralPath $apk -Algorithm SHA256).Hash)
    $adb = Find-VytalAdb $Root
    $phone = if ($adb) { Select-VytalDevice @(& $adb devices) $Device } else { $null }
    if ($adb -and $phone) {
        # -r preserves app data. Never uninstall on a signing/version mismatch.
        try { Invoke-VytalExternal $adb @('-s',$phone,'install','-r',$apk) }
        catch { throw 'Instalacao ADB falhou. Consulte o erro acima: assinatura/versao diferente exige APK compativel; nao desinstale nem apague dados. Confirme autorizacao USB/politica Samsung.' }
        Write-Host 'APK instalado por USB sem apagar dados. Agora execute .\vytal.ps1 start.'
    } else {
        Write-Warning 'ADB/aparelho USB nao encontrado. Nao precisa de Android Studio. Opcional: platform-tools standalone em developer.android.com/tools/releases/platform-tools.'
        Write-Host "Instalacao manual: copie $apk por USB (Transferencia de arquivos) ao Samsung, abra em Meus Arquivos e autorize essa origem se confiar no APK. Nao desinstale um Vytal existente em caso de erro de assinatura."
        Write-Host 'Se o Bloqueador Automatico/uma politica Samsung impedir, revise a politica no proprio aparelho; o launcher nao a altera. Depois execute .\vytal.ps1 start.'
        Start-Process explorer.exe -ArgumentList @('/select,', ('"' + $apk + '"'))
    }
}
function Test-VytalPort([string]$Address, [int]$Port) {
    $listener = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Parse($Address), $Port)
    try { $listener.Start(); return $true } catch [Net.Sockets.SocketException] { return $false } finally { $listener.Stop() }
}
function Get-VytalHealth([string]$Address, [int]$Port) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri ("http://{0}:{1}/{2}" -f $Address,$Port, $(if ($Port -eq 8000) {'health'} else {'status'})) -TimeoutSec 2
        if ($Port -eq 8000) { $body = $response.Content | ConvertFrom-Json; return $body.status -eq 'ok' -and $body.version -eq '0.1.0' }
        return $response.Content -match '^packager-status:running'
    } catch { return $false }
}
function Get-VytalPortAction([bool]$Free, [bool]$Owned, [bool]$Healthy) {
    if ($Free) { return 'start' }
    if ($Owned -and $Healthy) { return 'reuse' }
    throw 'Porta ocupada por processo nao confirmado ou servico sem saude. Feche o processo/terminal antigo e repita; nada foi encerrado automaticamente.'
}
function Test-VytalOwned($State, [string]$Address) {
    if (-not $State -or $State.Address -ne $Address) { return $false }
    $process = Get-Process -Id $State.Pid -ErrorAction SilentlyContinue
    return $null -ne $process -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $State.StartTicks
}
function Assert-VytalStoppedForInstall([string]$Root) {
    $path = Join-Path $Root '.local-vytal/windows-processes.json'
    if (-not (Test-Path $path)) { return }
    $state = Get-Content $path -Raw | ConvertFrom-Json
    foreach ($name in @('backend','metro')) {
        if ($state.PSObject.Properties[$name] -and (Test-VytalOwned $state.$name $state.$name.Address)) {
            throw 'Feche as janelas backend/Metro antes de repetir install. Nenhuma dependencia, configuracao ou dado foi alterado.'
        }
    }
}
function Run-VytalService([string]$Root, [string]$Address, [ValidateSet('backend','metro')][string]$Name) {
    Assert-VytalLocalEnvironment
    if (-not (Test-PrivateIPv4 $Address)) { throw 'Interface privada obrigatoria.' }
    $environment = Get-VytalEnvironment $Root
    foreach ($key in $environment.Keys) { [Environment]::SetEnvironmentVariable($key, $environment[$key], 'Process') }
    $tools = Get-VytalTools $Root
    if ($Name -eq 'backend') {
        Set-Location (Join-Path $Root 'backend')
        Invoke-VytalExternal $tools.python @('-m','uvicorn','app.main:app','--host',$Address,'--port','8000')
    } else {
        $env:NODE_ENV='development'; $env:EXPO_PUBLIC_API_URL="http://${Address}:8000/api/v1"
        $env:REACT_NATIVE_PACKAGER_HOSTNAME=$Address; $env:EXPO_PACKAGER_PROXY_URL="http://${Address}:8081"
        $env:EXPO_OFFLINE='1'; $env:EXPO_NO_TELEMETRY='1'
        Set-Location (Join-Path $Root 'mobile/vytal-app')
        Invoke-VytalExternal $tools.npm @('exec','--','expo','start','--dev-client','--lan','--port','8081','--clear')
    }
}
function Start-Vytal([string]$Root, [string]$Address, [string]$DatabasePath, [string]$Device) {
    Assert-VytalLocalEnvironment
    $network = @(Get-VytalNetwork)
    $ip = Select-VytalAddress $network $Address
    # Expo LAN listens on all interfaces. Refuse physical public networks rather
    # than changing firewall rules or silently exposing Metro on those networks.
    if (@($network | Where-Object { $_.Up -and $_.Physical -and $_.Profile -notin @('Private','DomainAuthenticated') }).Count) { throw 'Outra interface fisica publica esta conectada. Desconecte-a antes de iniciar Metro; firewall nao foi alterado.' }
    $null = Get-VytalTools $Root
    $stateFile = Join-Path $Root '.local-vytal/windows-processes.json'
    $state = if (Test-Path $stateFile) { Get-Content $stateFile -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
    $oldConfig = Join-Path $Root '.local-vytal/windows-config.json'
    $nextDatabase = Resolve-VytalDatabase $Root $DatabasePath
    foreach ($name in @('backend','metro')) {
        if ($state.PSObject.Properties[$name] -and (Test-VytalOwned $state.$name $state.$name.Address)) {
            if ($state.$name.Address -ne $ip -or ((Test-Path $oldConfig) -and (Get-Content $oldConfig -Raw | ConvertFrom-Json).local.db_path -ne $nextDatabase)) {
                throw 'Feche as janelas anteriores antes de mudar IP/banco. Nenhum processo foi encerrado nem dado movido.'
            }
        }
    }
    $actions = @{}
    foreach ($name in @('backend','metro')) {
        $port = if ($name -eq 'backend') {8000} else {8081}
        $owned = $state.PSObject.Properties[$name] -and (Test-VytalOwned $state.$name $ip)
        $actions[$name] = Get-VytalPortAction (Test-VytalPort $ip $port) ([bool]$owned) (Get-VytalHealth $ip $port)
    }
    $null = Initialize-VytalState $Root $DatabasePath
    foreach ($name in @('backend','metro')) {
        if ($actions[$name] -eq 'reuse') { continue }
        $module = (Join-Path $Root 'scripts/windows/Vytal.Local.psm1').Replace("'", "''")
        $safeRoot = $Root.Replace("'", "''")
        $code = "Import-Module '$module' -Force -DisableNameChecking; try { Run-VytalService -Root '$safeRoot' -Address '$ip' -Name '$name' } catch { Write-Error `$_.Exception.Message }"
        $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($code))
        $process = Start-Process powershell.exe -ArgumentList @('-NoLogo','-NoProfile','-NoExit','-ExecutionPolicy','Bypass','-EncodedCommand',$encoded) -PassThru
        $entry = [pscustomobject]@{Pid=$process.Id; StartTicks=$process.StartTime.ToUniversalTime().Ticks.ToString(); Address=$ip}
        $state | Add-Member -NotePropertyName $name -NotePropertyValue $entry -Force
        [IO.File]::WriteAllText($stateFile, ($state | ConvertTo-Json -Depth 4))
    }
    foreach ($port in @(8000,8081)) {
        $deadline = [DateTime]::UtcNow.AddSeconds(90)
        while (-not (Get-VytalHealth $ip $port)) {
            if ([DateTime]::UtcNow -gt $deadline) { throw "Servico na porta $port nao respondeu. Consulte a janela aberta. Verifique IP, portas, Python/Node e firewall privado; nao use tunnel nem exponha o roteador." }
            Start-Sleep -Milliseconds 500
        }
    }
    Write-Host "Backend OK: http://${ip}:8000/health | API: http://${ip}:8000/api/v1 | Metro: http://${ip}:8081"
    Write-Host 'No Samsung, mesmo Wi-Fi privado (sem rede de convidados/VPN): abra /health no navegador. Isso testa o caminho celular -> PC; o teste no PC sozinho nao comprova esse caminho.'
    Write-Host 'Se falhar: confira IP, isolamento de clientes no roteador e permissoes do Firewall Windows para Python/Node SOMENTE em redes privadas/sub-rede local. Nenhuma regra foi criada. HTTP e Metro sao exclusivos de desenvolvimento confiavel.'
    $url = 'vytal://expo-development-client/?url=' + [Uri]::EscapeDataString("http://${ip}:8081")
    Write-Host "Abra Vytal > Enter URL manually: http://${ip}:8081 (ou QR do terminal Metro). Nao use Expo Go. Link: $url"
    $adb = Find-VytalAdb $Root
    if ($adb) {
        try {
            $phone = Select-VytalDevice @(& $adb devices) $Device
            if ($phone) { Invoke-VytalExternal $adb @('-s',$phone,'shell','am','start','-a','android.intent.action.VIEW','-d',$url,'com.vytal.app') }
        } catch { Write-Warning ('Servicos estao ativos; abertura por USB falhou: ' + $_.Exception.Message) }
    }
    Write-Host 'Fontes de Dados > Conexao Saude > Conectar / conceder leitura. Confirme antes que Garmin gravou dados no Health Connect. Feche as duas janelas dos servicos para parar; start reutiliza servicos saudaveis sem reinstalar.'
}
Export-ModuleMember -Function *-Vytal*,Test-PrivateIPv4
