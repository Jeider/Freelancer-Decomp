$ErrorActionPreference='Stop'
$stage=$PSScriptRoot
$game='D:\games\FL_MOD'
$manifest=Get-Content -LiteralPath (Join-Path $stage 'manifest.json') -Raw | ConvertFrom-Json
if ($manifest.game -ne $game) {throw 'Unexpected game root'}
$allowed=@('bin/Common.dll','bin/Common.pdb','bin/Content.dll','bin/Content.pdb','bin/freelancer.exe','bin/freelancer.pdb','DATA/INTERFACE/NEURONET/INVENTORY/boosters.3db','DATA/INTERFACE/NEURONET/INVENTORY/keys.3db')
function Hash($path) {
    if (Test-Path -LiteralPath $path) {return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
    return $null
}
foreach ($process in (Get-CimInstance Win32_Process -Filter "Name='freelancer.exe' OR Name='freelancer_window.exe' OR Name='freelancer_en.exe' OR Name='freelancer_window_en.exe' OR Name='flserver.exe'")) {
    if (-not $process.ExecutablePath -or $process.ExecutablePath.StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)) {throw 'Close FL_MOD before installation'}
}
if ($manifest.files.Count -ne 8 -or ($manifest.files.relative | Sort-Object -Unique).Count -ne 8) {throw 'Unexpected payload count'}
foreach ($entry in $manifest.files) {
    if ($entry.relative -notin $allowed) {throw 'Unexpected payload'}
    if (-not $entry.prepared) {throw 'Missing payload hash'}
    if ((Hash (Join-Path $game $entry.relative)) -ne $entry.original) {throw 'Installed file changed since preparation'}
    if ((Hash (Join-Path $stage $entry.relative)) -ne $entry.prepared) {throw 'Prepared file changed'}
    if ($entry.original) {
        $probe=$null
        try {$probe=[IO.File]::Open((Join-Path $game $entry.relative),[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}
        finally {if ($probe) {$probe.Dispose()}}
    }
}
$backup=Join-Path $game ('BACKUP\codex_inventory_categories_'+(Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path $backup | Out-Null
foreach ($entry in $manifest.files) {
    if (-not $entry.original) {continue}
    $saved=Join-Path $backup $entry.relative
    New-Item -ItemType Directory -Path (Split-Path $saved) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $game $entry.relative) -Destination $saved
    if ((Hash $saved) -ne $entry.original) {throw 'Backup verification failed'}
}
Copy-Item -LiteralPath (Join-Path $stage 'manifest.json') -Destination $backup
$touched=@()
try {
    foreach ($entry in $manifest.files) {
        $destination=Join-Path $game $entry.relative
        if ((Hash $destination) -ne $entry.original) {throw 'Installed file changed before copy'}
        New-Item -ItemType Directory -Path (Split-Path $destination) -Force | Out-Null
        $touched+=$entry
        Copy-Item -LiteralPath (Join-Path $stage $entry.relative) -Destination $destination -Force
        if ((Hash $destination) -ne $entry.prepared) {throw 'Installation hash mismatch'}
    }
} catch {
    foreach ($entry in $touched) {
        $destination=Join-Path $game $entry.relative
        if ((Hash $destination) -eq $entry.original) {continue}
        if ($entry.original) {Copy-Item -LiteralPath (Join-Path $backup $entry.relative) -Destination $destination -Force}
        elseif (Test-Path -LiteralPath $destination) {Remove-Item -LiteralPath $destination}
        if ((Hash $destination) -ne $entry.original) {throw "Rollback verification failed. Backup: $backup"}
    }
    throw
}
Write-Output "Inventory categories installed; all 8 SHA256 hashes verified. Backup: $backup"
