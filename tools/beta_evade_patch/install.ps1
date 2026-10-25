param(
    [ValidateSet('Validate','Install','Restore')][string]$Mode = 'Validate',
    [string]$BetaRoot = 'D:/games/Freelancer Beta'
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/beta_evade_patch'
$root = (Resolve-Path -LiteralPath $BetaRoot).Path.TrimEnd('\','/')
$exe = (Resolve-Path -LiteralPath (Join-Path $root 'exe')).Path
if (-not $exe.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Beta exe escapes root' }
$originals = @{
    'FreeLancer.exe'='CE31304CF0E3353E72926281B612697A1815CC94042DFC80BE6C252C9FB5C920'
    'Common.dll'='7D358C16D2285D9E0D1EF0248A7ACB8F26F6828C4A9F300320A11DA77AFF1D0C'
}
function Hash([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function AssertClosed {
    $running = @(Get-CimInstance Win32_Process -Filter "Name='Freelancer.exe'" | Where-Object {
        $_.ExecutablePath -and $_.ExecutablePath.StartsWith($root + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)
    })
    if ($running.Count) { throw 'Freelancer Beta is running. Close Beta before installation/restore.' }
}
foreach ($name in $originals.Keys) { if ((Hash (Join-Path $exe $name)) -ne $originals[$name]) { throw "Unsupported original: $name" } }
$manifestPath = Join-Path $exe 'beta_evade_install.json'
$allowed = @('beta_evade_patch.dll','beta_evade_launcher.exe','beta_evade_README.txt')
if ($Mode -eq 'Restore') {
    AssertClosed
    $m = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($m.root -ne $root -or $m.format -ne 1) { throw 'Wrong restore manifest' }
    foreach ($p in $m.installed.PSObject.Properties) {
        if ($p.Name -notin $allowed) { throw 'Unexpected managed filename' }
        $target = Join-Path $exe $p.Name
        if ((Hash $target) -ne $p.Value) { throw "Managed file changed; refusing to remove: $target" }
    }
    foreach ($p in $m.installed.PSObject.Properties) { Remove-Item -LiteralPath (Join-Path $exe $p.Name) }
    # Original game files were never overwritten. Backup and audit manifest stay.
    Remove-Item -LiteralPath $manifestPath
    Write-Host 'Patch files removed. Original Beta binaries remain unchanged.'
    exit 0
}
$meta = Get-Content -LiteralPath (Join-Path $out 'payload.json') -Raw | ConvertFrom-Json
foreach ($p in $meta.sources.PSObject.Properties) {
    if ($p.Name -notmatch '^[A-Za-z0-9_.]+$') { throw 'Invalid source filename' }
    if ((Hash (Join-Path $PSScriptRoot $p.Name)) -ne $p.Value) { throw "Source changed since build: $($p.Name)" }
}
$stage = Join-Path $out 'stage'
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$installed = @{}
foreach ($p in $meta.payload.PSObject.Properties) {
    if ($p.Name -notin $allowed) { throw 'Unexpected payload filename' }
    $source=Join-Path $out $p.Name
    if ((Hash $source) -ne $p.Value) { throw 'Payload hash mismatch' }
    Copy-Item -LiteralPath $source -Destination (Join-Path $stage $p.Name) -Force
    if ((Hash (Join-Path $stage $p.Name)) -ne $p.Value) { throw 'Stage hash mismatch' }
    $installed[$p.Name]=$p.Value
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'README.txt') -Destination (Join-Path $stage 'beta_evade_README.txt') -Force
$installed['beta_evade_README.txt']=Hash (Join-Path $stage 'beta_evade_README.txt')
& python (Join-Path $PSScriptRoot 'verify.py') --beta-root $root --payload $out
if ($LASTEXITCODE -ne 0) { throw 'Static ABI verification failed' }
if ($Mode -eq 'Validate') { Write-Host 'Sources, staged payload and Beta ABI validated. No installation performed.'; exit 0 }
AssertClosed
if (Test-Path -LiteralPath $manifestPath) { throw 'Already installed: restore before reinstalling.' }
foreach ($name in $installed.Keys) { if (Test-Path -LiteralPath (Join-Path $exe $name)) { throw "Existing unmanaged file: $name" } }
$backup = Join-Path $root ('beta_evade_backup/' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
foreach ($name in $originals.Keys) {
    Copy-Item -LiteralPath (Join-Path $exe $name) -Destination (Join-Path $backup $name)
    if ((Hash (Join-Path $backup $name)) -ne $originals[$name]) { throw 'Backup verification failed' }
}
$manifest = @{ format=1; root=$root; createdUtc=[DateTime]::UtcNow.ToString('o'); originals=$originals; installed=$installed; sources=$meta.sources; backup=$backup }
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $backup 'manifest.json') -Encoding UTF8
$written = @()
try {
    AssertClosed
    foreach ($name in $installed.Keys) {
        $target = Join-Path $exe $name
        $written += $target
        Copy-Item -LiteralPath (Join-Path $stage $name) -Destination $target
        if ((Hash $target) -ne $installed[$name]) { throw 'Installed hash mismatch' }
    }
    $manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    & (Join-Path $exe 'beta_evade_launcher.exe') --verify
    if ($LASTEXITCODE -ne 0) { throw 'Installed launcher validation failed' }
    foreach ($name in $originals.Keys) { if ((Hash (Join-Path $exe $name)) -ne $originals[$name]) { throw 'Original changed during install' } }
} catch {
    foreach ($p in $written) { if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p } }
    if (Test-Path -LiteralPath $manifestPath) { Remove-Item -LiteralPath $manifestPath }
    throw
}
Write-Host "Installed. Launch: $(Join-Path $exe 'beta_evade_launcher.exe')"
Write-Host "Verified backup/manifest: $backup"
