$ErrorActionPreference = 'Stop'
$stage = $PSScriptRoot
$game = 'D:\games\FL_MOD'
$manifest = Get-Content -LiteralPath (Join-Path $stage 'manifest.json') -Raw | ConvertFrom-Json
if ($manifest.game -ne $game) { throw 'Unexpected game root' }
$allowed = @('bin/freelancer.exe','bin/freelancer.pdb','bin/RP9.dll','bin/RP9.pdb','DATA_EXTRA/SHADERS/hud_tilt.hlsl','bin/port.ini')
foreach ($process in (Get-CimInstance Win32_Process -Filter "Name='freelancer.exe' OR Name='freelancer_window.exe' OR Name='freelancer_en.exe' OR Name='freelancer_window_en.exe' OR Name='flserver.exe'")) {
    if (-not $process.ExecutablePath -or $process.ExecutablePath.StartsWith($game + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Close FL_MOD before installation'
    }
}
function Hash($path) {
    if (Test-Path -LiteralPath $path) { return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
    return $null
}
if ($manifest.files.Count -notin @(2,3,6) -or ($manifest.files.relative | Sort-Object -Unique).Count -ne $manifest.files.Count) { throw 'Unexpected payload count' }
if ($manifest.files.Count -eq 2 -and (($manifest.files.relative | Sort-Object) -join ',') -ne 'bin/freelancer.exe,bin/freelancer.pdb') { throw 'Unexpected client-only payload' }
if ($manifest.files.Count -eq 3 -and (($manifest.files.relative | Sort-Object) -join ',') -ne 'bin/freelancer.exe,bin/freelancer.pdb,bin/port.ini') { throw 'Unexpected settings payload' }
foreach ($entry in $manifest.files) {
    if ($entry.relative -notin $allowed -or -not $entry.prepared) { throw 'Unexpected payload' }
    if ((Hash (Join-Path $game $entry.relative)) -ne $entry.original) { throw 'Installed file changed since preparation' }
    if ((Hash (Join-Path $stage $entry.relative)) -ne $entry.prepared) { throw 'Prepared file changed' }
    if ($entry.original) {
        # Also detects a differently named executable/host holding this image open.
        $probe = $null
        try {
            $probe = [System.IO.File]::Open((Join-Path $game $entry.relative), [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
        } finally {
            if ($probe) { $probe.Dispose() }
        }
    }
}
foreach ($entry in $manifest.dependencies) {
    if ($entry.relative -notin @('bin/Common.dll','bin/DALib.dll','bin/dacom.dll','bin/zlib.dll','bin/imeui.dll','bin/alchemy.dll','bin/RP9.dll','DATA_EXTRA/SHADERS/common.hlsli','DATA_EXTRA/SHADERS/hud_tilt.hlsl')) { throw 'Unexpected dependency' }
    if ((Hash (Join-Path $game $entry.relative)) -ne $entry.sha256) { throw 'Installed dependency changed' }
}
$backup = Join-Path $game ('BACKUP\codex_hud_tilt_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path $backup | Out-Null
foreach ($entry in $manifest.files) {
    if (-not $entry.original) { continue }
    $saved = Join-Path $backup $entry.relative
    New-Item -ItemType Directory -Path (Split-Path $saved) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $game $entry.relative) -Destination $saved
    if ((Hash $saved) -ne $entry.original) { throw 'Backup verification failed' }
}
Copy-Item -LiteralPath (Join-Path $stage 'manifest.json') -Destination $backup
$touched = @()
try {
    foreach ($entry in $manifest.files) {
        $destination = Join-Path $game $entry.relative
        if ((Hash $destination) -ne $entry.original) { throw 'Installed file changed before copy' }
        $touched += $entry
        Copy-Item -LiteralPath (Join-Path $stage $entry.relative) -Destination $destination -Force
        if ((Hash $destination) -ne $entry.prepared) { throw 'Installation hash mismatch' }
    }
} catch {
    foreach ($entry in $touched) {
        $destination = Join-Path $game $entry.relative
        if ((Hash $destination) -eq $entry.original) { continue }
        if ($entry.original) {
            Copy-Item -LiteralPath (Join-Path $backup $entry.relative) -Destination $destination -Force
        } elseif (Test-Path -LiteralPath $destination) {
            Remove-Item -LiteralPath $destination
        }
        if ((Hash $destination) -ne $entry.original) { throw "Rollback verification failed. Backup: $backup" }
    }
    throw
}
Write-Output "HUD tilt update installed; SHA256 verified. Backup: $backup"
