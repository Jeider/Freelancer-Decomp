$ErrorActionPreference = 'Stop'
$stage = $PSScriptRoot
$game = 'D:\games\FL_MOD'
$manifest = Get-Content -LiteralPath (Join-Path $stage 'manifest.json') -Raw | ConvertFrom-Json
if ($manifest.game -ne $game) { throw 'Unexpected game root' }
$allowed = @('bin/freelancer.exe', 'bin/freelancer.pdb', 'Assets/Pythonlancer/text/static.py', 'EXE/NameResources.dll', 'RESOURCES_ENG/NameResources.dll')
foreach ($process in (Get-CimInstance Win32_Process -Filter "Name='freelancer.exe' OR Name='flserver.exe'")) {
    if (-not $process.ExecutablePath -or $process.ExecutablePath.StartsWith($game + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Close FL_MOD before installation'
    }
}
if ($manifest.files.Count -ne 5 -or ($manifest.files.relative | Sort-Object -Unique).Count -ne 5) { throw 'Unexpected payload count' }
foreach ($entry in $manifest.files) {
    if ($entry.relative -notin $allowed -or -not $entry.original) { throw 'Unexpected payload path or missing original' }
    if ((Get-FileHash -LiteralPath (Join-Path $game $entry.relative)).Hash -ne $entry.original) { throw 'Installed file changed since preparation' }
    if ((Get-FileHash -LiteralPath (Join-Path $stage $entry.relative)).Hash -ne $entry.prepared) { throw 'Prepared file changed' }
}
foreach ($entry in $manifest.dependencies) {
    if ($entry.relative -notin @('bin/Common.dll', 'bin/DALib.dll', 'bin/dacom.dll', 'bin/zlib.dll', 'bin/imeui.dll', 'DATA/INTERFACE/HUD/HUD_contactlist.3db', 'bin/freelancer.ini')) { throw 'Unexpected dependency path' }
    if ((Get-FileHash -LiteralPath (Join-Path $game $entry.relative)).Hash -ne $entry.sha256) { throw 'Installed dependency changed' }
}
$backup = Join-Path $game ('BACKUP\codex_cutscene_skip_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path (Join-Path $backup 'bin') -Force | Out-Null
foreach ($entry in $manifest.files) {
    $saved = Join-Path $backup $entry.relative
    New-Item -ItemType Directory -Path (Split-Path $saved) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $game $entry.relative) -Destination $saved
    if ((Get-FileHash -LiteralPath $saved).Hash -ne $entry.original) { throw 'Backup verification failed' }
}
Copy-Item -LiteralPath (Join-Path $stage 'manifest.json') -Destination $backup
try {
    foreach ($entry in $manifest.files) {
        $destination = Join-Path $game $entry.relative
        Copy-Item -LiteralPath (Join-Path $stage $entry.relative) -Destination $destination -Force
        if ((Get-FileHash -LiteralPath $destination).Hash -ne $entry.prepared) { throw 'Installation hash mismatch' }
    }
} catch {
    foreach ($entry in $manifest.files) {
        Copy-Item -LiteralPath (Join-Path $backup $entry.relative) -Destination (Join-Path $game $entry.relative) -Force
        if ((Get-FileHash -LiteralPath (Join-Path $game $entry.relative)).Hash -ne $entry.original) { throw "Rollback verification failed. Backup: $backup" }
    }
    throw
}
Write-Output "Cutscene skip confirmation installed and SHA256 verified (client, RU/EN resources, Pythonlancer). Backup: $backup"

