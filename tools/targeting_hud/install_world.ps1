$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$stage = Join-Path $repo 'src/obj/targeting_world_install'
$game = 'D:\games\FL_MOD'
$manifest = Get-Content -LiteralPath (Join-Path $stage 'manifest.json') -Raw | ConvertFrom-Json
if ([IO.Path]::GetFullPath($manifest.game) -ne $game) { throw 'Unexpected game root' }
$allowed = @('bin/freelancer.exe', 'bin/freelancer.pdb', 'bin/Common.dll', 'bin/Common.pdb',
    'DATA/ships/shiparch.ini', 'DATA/ships/shiparch2.ini', 'Assets/Pythonlancer/world/capital.py')
$processes = Get-CimInstance Win32_Process -Filter "Name='freelancer.exe' OR Name='flserver.exe'"
foreach ($process in $processes) {
    if (-not $process.ExecutablePath -or $process.ExecutablePath.StartsWith($game + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Close FL_MOD before installation'
    }
}
if ($manifest.files.Count -ne $allowed.Count -or ($manifest.files.relative | Sort-Object -Unique).Count -ne $allowed.Count) {
    throw 'Unexpected payload count'
}
foreach ($entry in $manifest.files) {
    if ($entry.relative -notin $allowed) { throw "Unexpected path: $($entry.relative)" }
    if ((Get-FileHash -LiteralPath (Join-Path $game $entry.relative)).Hash -ne $entry.original) { throw "Original changed: $($entry.relative)" }
    if ((Get-FileHash -LiteralPath (Join-Path $stage $entry.relative)).Hash -ne $entry.prepared) { throw "Payload changed: $($entry.relative)" }
}
foreach ($entry in $manifest.dependencies) {
    if ((Get-FileHash -LiteralPath (Join-Path $game $entry.relative)).Hash -ne $entry.sha256) { throw "Dependency changed: $($entry.relative)" }
}
$backup = Join-Path $game ('BACKUP\codex_targeting_world_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path $backup | Out-Null
foreach ($entry in $manifest.files) {
    $saved = Join-Path $backup $entry.relative
    New-Item -ItemType Directory -Path (Split-Path $saved) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $game $entry.relative) -Destination $saved
    if ((Get-FileHash -LiteralPath $saved).Hash -ne $entry.original) { throw 'Backup verification failed' }
}
foreach ($name in @('manifest.json', 'migration.json', 'generator.json')) {
    Copy-Item -LiteralPath (Join-Path $stage $name) -Destination $backup
}
try {
    foreach ($entry in $manifest.files) {
        $destination = Join-Path $game $entry.relative
        Copy-Item -LiteralPath (Join-Path $stage $entry.relative) -Destination $destination -Force
        if ((Get-FileHash -LiteralPath $destination).Hash -ne $entry.prepared) { throw "Install verification failed: $($entry.relative)" }
    }
    foreach ($entry in $manifest.dependencies) {
        if ((Get-FileHash -LiteralPath (Join-Path $game $entry.relative)).Hash -ne $entry.sha256) { throw "Dependency changed: $($entry.relative)" }
    }
} catch {
    foreach ($entry in $manifest.files) {
        Copy-Item -LiteralPath (Join-Path $backup $entry.relative) -Destination (Join-Path $game $entry.relative) -Force
    }
    throw
}
Write-Output "Installed and verified seven files. Backup: $backup"
