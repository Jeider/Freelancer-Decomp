param(
    [string]$GameRoot = 'D:\games\FL_MOD',
    [switch]$Apply,
    [string]$RestoreBackup
)
$ErrorActionPreference = 'Stop'
$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$GameRoot = (Resolve-Path -LiteralPath $GameRoot).Path.TrimEnd('\')
$StageRoot = Join-Path $RepoRoot 'src\obj\br_cam_debris_install'
$ManifestPath = Join-Path $StageRoot 'manifest.json'
$RelativePaths = @('bin\freelancer.exe', 'bin\freelancer.pdb',
    'DATA_EXTRA\SHADERS\far_rocks.hlsl', 'DATA_EXTRA\SHADERS\field_dust.hlsl')
1..4 | ForEach-Object { $RelativePaths += "DATA\SOLAR\ASTEROIDS_MOD\GENERATED\br_cam_deb${_}_debris.ini" }
$RelativePaths += @('bin\RP9.dll', 'bin\RP9.pdb')

function SafePath([string]$Root, [string]$Relative) {
    $Full = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    $Prefix = [IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    if (!$Full.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Path escapes root: $Full" }
    return $Full
}
function Hash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }
function CopyFile([string]$Source, [string]$Destination) {
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Destination)) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}
function CheckStopped {
    if (Get-Process -Name freelancer -ErrorAction SilentlyContinue) { throw 'Exit Freelancer before installing or restoring.' }
}
function CheckManifest($Manifest) {
    # Eight-file manifests belong to the earlier billboard trial and can still be restored.
    if ($Manifest.GameRoot -ne $GameRoot -or $Manifest.Files.Count -notin @(8, 10)) { throw 'Manifest root/count mismatch.' }
    for ($I = 0; $I -lt $Manifest.Files.Count; ++$I) {
        if ($Manifest.Files[$I].Relative -ne $RelativePaths[$I]) { throw 'Unexpected manifest target.' }
    }
}

if ($RestoreBackup) {
    if ($Apply) { throw 'Use either -Apply or -RestoreBackup.' }
    CheckStopped
    $RestoreRoot = (Resolve-Path -LiteralPath $RestoreBackup).Path
    $Manifest = Get-Content -LiteralPath (Join-Path $RestoreRoot 'manifest.json') -Raw | ConvertFrom-Json
    CheckManifest $Manifest
    foreach ($File in $Manifest.Files) {
        if ((Hash (SafePath $RestoreRoot $File.Relative)) -ne $File.OriginalHash) { throw "Invalid backup: $($File.Relative)" }
        if ((Hash (SafePath $GameRoot $File.Relative)) -ne $File.PreparedHash) { throw "Changed since installation: $($File.Relative). Restore manually to preserve newer edits." }
    }
    foreach ($File in $Manifest.Files) { CopyFile (SafePath $RestoreRoot $File.Relative) (SafePath $GameRoot $File.Relative) }
    Write-Output "Restored $($Manifest.Files.Count) files from $RestoreRoot"
    return
}

if (!$Apply) {
    [IO.Directory]::CreateDirectory($StageRoot) | Out-Null
    $Profile = [IO.File]::ReadAllText((Join-Path $RepoRoot 'DATA_EXTRA\ASTEROIDS\br_cam_debris.ini')).Trim()
    $Begin = '; BEGIN br_cam debris prototype'
    $End = '; END br_cam debris prototype'
    $Encoding = [Text.Encoding]::GetEncoding(28591) # byte-preserving round trip for existing INIs
    $Files = @()
    foreach ($Relative in $RelativePaths) {
        $Destination = SafePath $GameRoot $Relative
        $Stage = SafePath $StageRoot $Relative
        $OriginalHash = Hash $Destination
        if ($Relative.EndsWith('.ini')) {
            $Original = $Encoding.GetString([IO.File]::ReadAllBytes($Destination))
            $Pattern = '(?s)\r?\n; BEGIN br_cam debris prototype\r?\n.*?; END br_cam debris prototype\r?\n?'
            $Original = [regex]::Replace($Original, $Pattern, '')
            if ($Original.Contains($Begin) -or $Original.Contains($End) -or
                $Original -match '(?im)^\s*\[(FarRocks|FieldDust)\]') { throw "Existing unmanaged profile in $Relative" }
            $Prepared = $Original + "`r`n$Begin`r`n" + ($Profile -replace '\r?\n', "`r`n") + "`r`n$End`r`n"
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Stage)) | Out-Null
            [IO.File]::WriteAllBytes($Stage, $Encoding.GetBytes($Prepared))
        } else { CopyFile (SafePath $RepoRoot $Relative) $Stage }
        $Files += [pscustomobject]@{ Relative = $Relative; OriginalHash = $OriginalHash; PreparedHash = (Hash $Stage) }
    }
    [pscustomobject]@{ GameRoot = $GameRoot; Files = $Files } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
    Write-Output "Prepared $($Files.Count) files in $StageRoot. Game files have not changed."
    $Files | Format-Table Relative, PreparedHash -AutoSize
    return
}

CheckStopped
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
CheckManifest $Manifest
if ($Manifest.Files.Count -ne $RelativePaths.Count) { throw 'Prepare again: mesh rendering requires the matching RP9 build.' }
foreach ($File in $Manifest.Files) {
    if ((Hash (SafePath $GameRoot $File.Relative)) -ne $File.OriginalHash) { throw "Game file changed since preparation: $($File.Relative)" }
    if ((Hash (SafePath $StageRoot $File.Relative)) -ne $File.PreparedHash) { throw "Staged file changed: $($File.Relative)" }
}
$BackupRoot = SafePath $GameRoot ('BACKUP\codex_br_cam_debris_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
foreach ($File in $Manifest.Files) {
    $Backup = SafePath $BackupRoot $File.Relative
    CopyFile (SafePath $GameRoot $File.Relative) $Backup
    if ((Hash $Backup) -ne $File.OriginalHash) { throw "Backup verification failed: $($File.Relative)" }
}
CopyFile $ManifestPath (Join-Path $BackupRoot 'manifest.json')
try {
    foreach ($File in $Manifest.Files) {
        $Destination = SafePath $GameRoot $File.Relative
        CopyFile (SafePath $StageRoot $File.Relative) $Destination
        if ((Hash $Destination) -ne $File.PreparedHash) { throw "Installed hash mismatch: $($File.Relative)" }
    }
} catch {
    foreach ($File in $Manifest.Files) { CopyFile (SafePath $BackupRoot $File.Relative) (SafePath $GameRoot $File.Relative) }
    throw
}
Write-Output "Installed and verified $($Manifest.Files.Count) files. Backup: $BackupRoot"
