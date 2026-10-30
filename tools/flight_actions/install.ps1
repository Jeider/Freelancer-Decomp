$ErrorActionPreference = 'Stop'
$stage = $PSScriptRoot
$game = 'D:\games\FL_MOD'
$manifest = Get-Content -LiteralPath (Join-Path $stage 'manifest.json') -Raw | ConvertFrom-Json
if ([IO.Path]::GetFullPath($manifest.game) -ne $game) { throw 'Unexpected game root' }
$allowed = @('bin/freelancer.exe', 'bin/freelancer.pdb', 'bin/port.ini',
    'DATA/INTERFACE/HUD/EXTRA/HUD_drasticevade.3db',
    'DATA/INTERFACE/HUD/EXTRA/HUD_turntoface.3db',
    'DATA/INTERFACE/HUD/EXTRA/hud_mnvrstrafe.3db',
    'DATA/INTERFACE/HUD/EXTRA/hud_mnvrevade.3db')
foreach ($process in (Get-CimInstance Win32_Process -Filter "Name='freelancer.exe' OR Name='freelancer_window.exe' OR Name='freelancer_en.exe' OR Name='freelancer_window_en.exe' OR Name='flserver.exe'")) {
    if (-not $process.ExecutablePath -or $process.ExecutablePath.StartsWith($game + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Close FL_MOD before installation'
    }
}
if ($manifest.files.Count -ne $allowed.Count -or ($manifest.files.relative | Sort-Object -Unique).Count -ne $allowed.Count) {
    throw 'Unexpected payload count'
}
function Test-Original($entry) {
    $path = Join-Path $game $entry.relative
    if ($null -eq $entry.original) {
        if (Test-Path -LiteralPath $path) { throw "New file already exists: $path" }
    } elseif (-not (Test-Path -LiteralPath $path) -or (Get-FileHash -LiteralPath $path).Hash -ne $entry.original) {
        throw "Installed file changed: $path"
    }
}
foreach ($entry in $manifest.files) {
    if ($entry.relative -notin $allowed) { throw 'Unexpected payload path' }
    Test-Original $entry
    if ((Get-FileHash -LiteralPath (Join-Path $stage $entry.relative)).Hash -ne $entry.prepared) { throw 'Payload changed' }
}
foreach ($entry in $manifest.dependencies) {
    if ($entry.relative -notmatch '^bin/[A-Za-z0-9_.-]+\.dll$') { throw 'Unexpected dependency path' }
    if ((Get-FileHash -LiteralPath (Join-Path $game $entry.relative)).Hash -ne $entry.sha256) { throw 'Dependency changed' }
}
$backup = Join-Path $game ('BACKUP\codex_flight_actions_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path $backup | Out-Null
foreach ($entry in $manifest.files) {
    if ($null -eq $entry.original) { continue }
    $saved = Join-Path $backup $entry.relative
    New-Item -ItemType Directory -Path (Split-Path $saved) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $game $entry.relative) -Destination $saved
    if ((Get-FileHash -LiteralPath $saved).Hash -ne $entry.original) { throw 'Backup mismatch' }
}
Copy-Item -LiteralPath (Join-Path $stage 'manifest.json') -Destination $backup
$touched = @()
try {
    foreach ($entry in $manifest.files) {
        Test-Original $entry
        $destination = Join-Path $game $entry.relative
        New-Item -ItemType Directory -Path (Split-Path $destination) -Force | Out-Null
        $touched += $entry
        Copy-Item -LiteralPath (Join-Path $stage $entry.relative) -Destination $destination -Force
        if ((Get-FileHash -LiteralPath $destination).Hash -ne $entry.prepared) { throw 'Installation verification failed' }
    }
} catch {
    foreach ($entry in $touched) {
        $destination = Join-Path $game $entry.relative
        if ($null -ne $entry.original) {
            Copy-Item -LiteralPath (Join-Path $backup $entry.relative) -Destination $destination -Force
        } elseif (Test-Path -LiteralPath $destination) {
            Remove-Item -LiteralPath $destination
        }
    }
    throw
}
Write-Output "Installed flight actions client, action config and four icons; all SHA256 verified. Backup: $backup"
