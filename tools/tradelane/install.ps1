$ErrorActionPreference = 'Stop'
$stage = $PSScriptRoot
$game = 'D:\games\FL_MOD'
$manifest = Get-Content -LiteralPath (Join-Path $stage 'manifest.json') -Raw | ConvertFrom-Json
if ($manifest.game -ne $game) { throw 'Unexpected game root' }
$allowed = @('bin/Common.dll', 'bin/Common.pdb', 'bin/freelancer.exe', 'bin/freelancer.pdb', 'DATA/SOLAR/solararch.ini', 'DATA/SOLAR/loadouts.ini', 'DATA/SOLAR/DOCKABLE/tlr_root.3db', 'DATA/SOLAR/DOCKABLE/tlr_legal_lod5.cmp')
foreach ($process in (Get-CimInstance Win32_Process -Filter "Name='freelancer.exe' OR Name='freelancer_window.exe' OR Name='freelancer_en.exe' OR Name='freelancer_window_en.exe' OR Name='flserver.exe'")) {
    if (-not $process.ExecutablePath -or $process.ExecutablePath.StartsWith($game + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Close FL_MOD before installation'
    }
}
if ($manifest.files.Count -ne $allowed.Count -or ($manifest.files.relative | Sort-Object -Unique).Count -ne $allowed.Count) { throw 'Unexpected payload count' }
foreach ($entry in $manifest.files) {
    if ($entry.relative -notin $allowed -or -not $entry.original) { throw 'Unexpected payload path or missing original' }
    if ((Get-FileHash -LiteralPath (Join-Path $game $entry.relative)).Hash -ne $entry.original) { throw 'Installed file changed since preparation' }
    if ((Get-FileHash -LiteralPath (Join-Path $stage $entry.relative)).Hash -ne $entry.prepared) { throw 'Prepared file changed' }
}
foreach ($entry in $manifest.dependencies) {
    if ($entry.relative -notin @('bin/Common.dll', 'bin/freelancer.exe', 'DATA/SOLAR/solararch.ini', 'bin/DALib.dll', 'bin/EngBase.dll', 'bin/dacom.dll', 'bin/zlib.dll', 'bin/imeui.dll', 'bin/alchemy.dll', 'bin/RP9.dll', 'DATA/UNIVERSE/SYSTEMS_MOD/SIGMA8/sig8.ini')) { throw 'Unexpected dependency path' }
    if ((Get-FileHash -LiteralPath (Join-Path $game $entry.relative)).Hash -ne $entry.sha256) { throw 'Installed dependency changed' }
}
$backup = Join-Path $game ('BACKUP\codex_tradelane_anim_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path (Join-Path $backup 'bin') -Force | Out-Null
foreach ($entry in $manifest.files) {
    $saved = Join-Path $backup $entry.relative
    New-Item -ItemType Directory -Path (Split-Path $saved) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $game $entry.relative) -Destination $saved
    if ((Get-FileHash -LiteralPath $saved).Hash -ne $entry.original) { throw 'Backup verification failed' }
}
Copy-Item -LiteralPath (Join-Path $stage 'manifest.json') -Destination $backup
$touched = @()
try {
    foreach ($entry in $manifest.files) {
        $destination = Join-Path $game $entry.relative
        if ((Get-FileHash -LiteralPath $destination).Hash -ne $entry.original) { throw 'Installed file changed before copy' }
        $touched += $entry
        Copy-Item -LiteralPath (Join-Path $stage $entry.relative) -Destination $destination -Force
        if ((Get-FileHash -LiteralPath $destination).Hash -ne $entry.prepared) { throw 'Installation hash mismatch' }
    }
} catch {
    foreach ($entry in $touched) {
        Copy-Item -LiteralPath (Join-Path $backup $entry.relative) -Destination (Join-Path $game $entry.relative) -Force
        if ((Get-FileHash -LiteralPath (Join-Path $game $entry.relative)).Hash -ne $entry.original) { throw "Rollback verification failed. Backup: $backup" }
    }
    throw
}
Write-Output "Payload installed and SHA256 verified. Backup: $backup"

