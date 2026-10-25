$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$stage = Join-Path $repo 'src/obj/health_hud/install'
$game = 'D:\games\FL_MOD'
$manifest = Get-Content -LiteralPath (Join-Path $stage 'manifest.json') -Raw | ConvertFrom-Json
if ([IO.Path]::GetFullPath($manifest.game) -ne $game) { throw 'Unexpected game root' }
$allowed = @('bin/freelancer.exe', 'bin/freelancer.pdb', 'DATA/INTERFACE/HUD/HUD_health.3db', 'DATA/INTERFACE/hud.ini')
foreach ($process in (Get-CimInstance Win32_Process -Filter "Name='freelancer.exe' OR Name='flserver.exe'")) {
    if (-not $process.ExecutablePath -or $process.ExecutablePath.StartsWith($game + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Close FL_MOD before installation'
    }
}
if ($manifest.files.Count -ne $allowed.Count -or ($manifest.files.relative | Sort-Object -Unique).Count -ne $allowed.Count) {
    throw 'Unexpected payload count'
}
foreach ($entry in $manifest.files) {
    if ($entry.relative -notin $allowed) { throw "Unexpected path: $($entry.relative)" }
    $original = Join-Path $game $entry.relative
    if ($null -eq $entry.original) {
        if ($entry.relative -ne 'DATA/INTERFACE/HUD/HUD_health.3db' -or (Test-Path -LiteralPath $original)) {
            throw 'New icon already exists or unexpected new file'
        }
    } elseif ((Get-FileHash -LiteralPath $original).Hash -ne $entry.original) {
        throw "Original changed: $($entry.relative)"
    }
    if ((Get-FileHash -LiteralPath (Join-Path $stage $entry.relative)).Hash -ne $entry.prepared) {
        throw "Payload changed: $($entry.relative)"
    }
}
foreach ($entry in $manifest.dependencies) {
    if ((Get-FileHash -LiteralPath (Join-Path $game $entry.relative)).Hash -ne $entry.sha256) {
        throw "Dependency changed: $($entry.relative)"
    }
}
$backup = Join-Path $game ('BACKUP\codex_health_hud_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path $backup | Out-Null
foreach ($entry in $manifest.files) {
    if ($null -eq $entry.original) { continue }
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
        if ((Get-FileHash -LiteralPath $destination).Hash -ne $entry.prepared) { throw 'Install verification failed' }
    }
} catch {
    foreach ($entry in $manifest.files) {
        $destination = Join-Path $game $entry.relative
        if ($null -ne $entry.original) {
            Copy-Item -LiteralPath (Join-Path $backup $entry.relative) -Destination $destination -Force
        } elseif (Test-Path -LiteralPath $destination) {
            Remove-Item -LiteralPath $destination
        }
    }
    throw
}
Write-Output "Installed and verified Health HUD (four files). Backup: $backup"
