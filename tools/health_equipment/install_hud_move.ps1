$ErrorActionPreference = 'Stop'
$game = 'D:\games\FL_MOD'
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
$allowed = @ALLOWED@
if ([IO.Path]::GetFullPath($manifest.game) -ne $game) { throw 'Unexpected game root' }
$entries = @($manifest.files) + @($manifest.removals)
if ($entries.Count -ne $allowed.Count -or @($entries.relative | Sort-Object -Unique).Count -ne $allowed.Count) { throw 'Unexpected payload count' }
foreach ($process in (Get-CimInstance Win32_Process -Filter "Name='freelancer.exe' OR Name='freelancer_window.exe' OR Name='freelancer_en.exe' OR Name='freelancer_window_en.exe' OR Name='flserver.exe'")) {
    if (-not $process.ExecutablePath -or $process.ExecutablePath.StartsWith($game + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Close FL_MOD before installation' }
}
function Test-Original($entry) {
    $path = Join-Path $game $entry.relative
    if ($null -eq $entry.original) {
        if (Test-Path -LiteralPath $path) { throw "New file already exists: $path" }
    } elseif (-not (Test-Path -LiteralPath $path) -or (Get-FileHash -LiteralPath $path).Hash -ne $entry.original) { throw "Installed file changed: $path" }
}
foreach ($entry in $entries) {
    if ($entry.relative -notin $allowed) { throw 'Unexpected path' }
    $full = [IO.Path]::GetFullPath((Join-Path $game $entry.relative))
    if (-not $full.StartsWith($game + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside game root' }
    Test-Original $entry
}
foreach ($entry in $manifest.files) {
    if ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $entry.relative)).Hash -ne $entry.prepared) { throw 'Payload changed' }
}
$backup = Join-Path $game ('BACKUP\codex_hud_assets_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path $backup | Out-Null
foreach ($entry in $entries) {
    if ($null -eq $entry.original) { continue }
    $saved = Join-Path $backup $entry.relative
    New-Item -ItemType Directory -Path (Split-Path $saved) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $game $entry.relative) -Destination $saved
    if ((Get-FileHash -LiteralPath $saved).Hash -ne $entry.original) { throw 'Backup mismatch' }
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Destination $backup
$touched = @()
try {
    foreach ($entry in $manifest.files) {
        Test-Original $entry
        $destination = Join-Path $game $entry.relative
        New-Item -ItemType Directory -Path (Split-Path $destination) -Force | Out-Null
        $touched += $entry
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $entry.relative) -Destination $destination -Force
        if ((Get-FileHash -LiteralPath $destination).Hash -ne $entry.prepared) { throw 'Installation verification failed' }
    }
    foreach ($entry in $manifest.removals) {
        Test-Original $entry
        $touched += $entry
        Remove-Item -LiteralPath (Join-Path $game $entry.relative)
    }
} catch {
    foreach ($entry in $touched) {
        $destination = Join-Path $game $entry.relative
        if ($null -ne $entry.original) { Copy-Item -LiteralPath (Join-Path $backup $entry.relative) -Destination $destination -Force }
        elseif (Test-Path -LiteralPath $destination) { Remove-Item -LiteralPath $destination }
    }
    throw
}
Write-Output "HUD assets relocated; client paths and file hashes verified. Backup: $backup"
