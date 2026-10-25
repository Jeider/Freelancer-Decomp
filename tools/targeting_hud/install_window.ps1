$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$stage = Join-Path $repo 'src/obj/targeting_window_install'
$game = 'D:\games\FL_MOD'
$manifest = Get-Content -LiteralPath (Join-Path $stage 'manifest.json') -Raw | ConvertFrom-Json
$allowed = @('bin/freelancer.exe', 'bin/freelancer.pdb', 'DATA/INTERFACE/HUD/HUD_target_window_lock.3db')
if ($manifest.game -ne $game -or $manifest.files.Count -ne 3 -or
    ($manifest.files.relative | Sort-Object -Unique).Count -ne 3) { throw 'Unexpected payload' }
foreach ($process in (Get-CimInstance Win32_Process -Filter "Name='freelancer.exe' OR Name='flserver.exe'")) {
    if (-not $process.ExecutablePath -or $process.ExecutablePath.StartsWith($game + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Close FL_MOD before installation'
    }
}
foreach ($entry in $manifest.files) {
    if ($entry.relative -notin $allowed) { throw 'Unexpected path' }
    $destination = Join-Path $game $entry.relative
    if ($entry.original) {
        if ((Get-FileHash -LiteralPath $destination).Hash -ne $entry.original) { throw "Original changed: $($entry.relative)" }
    } elseif (Test-Path -LiteralPath $destination) { throw "New asset already exists: $destination" }
    if ((Get-FileHash -LiteralPath (Join-Path $stage $entry.relative)).Hash -ne $entry.prepared) { throw 'Payload changed' }
}
$backup = Join-Path $game ('BACKUP\codex_targeting_window_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path $backup | Out-Null
foreach ($entry in $manifest.files) {
    if (-not $entry.original) { continue }
    $saved = Join-Path $backup $entry.relative
    New-Item -ItemType Directory -Path (Split-Path $saved) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $game $entry.relative) -Destination $saved
    if ((Get-FileHash -LiteralPath $saved).Hash -ne $entry.original) { throw 'Backup verification failed' }
}
Copy-Item -LiteralPath (Join-Path $stage 'manifest.json') -Destination $backup
Copy-Item -LiteralPath (Join-Path $stage 'lock_icon.json') -Destination $backup
$installed = @()
try {
    foreach ($entry in $manifest.files) {
        $destination = Join-Path $game $entry.relative
        $installed += $entry
        Copy-Item -LiteralPath (Join-Path $stage $entry.relative) -Destination $destination -Force
        if ((Get-FileHash -LiteralPath $destination).Hash -ne $entry.prepared) { throw 'Install verification failed' }
    }
} catch {
    foreach ($entry in $installed) {
        $destination = Join-Path $game $entry.relative
        if ($entry.original) {
            Copy-Item -LiteralPath (Join-Path $backup $entry.relative) -Destination $destination -Force
        } elseif (Test-Path -LiteralPath $destination) {
            Remove-Item -LiteralPath $destination
        }
    }
    throw
}
Write-Output "Installed and verified client, symbols and standalone lock icon. Backup: $backup"
