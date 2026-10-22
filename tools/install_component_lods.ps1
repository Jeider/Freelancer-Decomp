$ErrorActionPreference='Stop'
if(Get-Process Freelancer -ErrorAction SilentlyContinue){throw 'Freelancer is running; installation stopped'}
$bundle=Join-Path (Get-Location) 'bin/component_lods'
$manifest=Get-Content (Join-Path $bundle 'manifest.json') -Raw | ConvertFrom-Json
$runtimeRoot=[IO.Path]::GetFullPath('D:/games/FL_MOD/DATA/')
$jobs=@()
foreach($model in @($manifest.models)+@($manifest.fixes)){
    $jobs+=@{Relative=$model.file;Source=(Join-Path $bundle $model.file);Before=$model.source_sha256;After=$model.output_sha256}
}
foreach($config in $manifest.configs){
    $jobs+=@{Relative=$config.file;Source=(Join-Path (Get-Location) $config.staged);Before=$config.source_sha256;After=$config.output_sha256}
}
if($manifest.models.Count -ne 10 -or $manifest.fixes.Count -ne 2 -or $jobs.Count -ne 14){throw 'Unexpected installation scope'}
foreach($job in $jobs){
    $target=[IO.Path]::GetFullPath((Join-Path $runtimeRoot $job.Relative))
    if(-not $target.StartsWith($runtimeRoot,[StringComparison]::OrdinalIgnoreCase)){throw 'Target escaped runtime DATA directory'}
    $job.Target=$target
    if((Get-FileHash -LiteralPath $target).Hash -ne $job.Before){throw "Runtime file changed since generation: $target"}
    if((Get-FileHash -LiteralPath $job.Source).Hash -ne $job.After){throw "Staged file hash mismatch: $($job.Source)"}
}
$backup=Join-Path $runtimeRoot ('.before_component_lods_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $backup | Out-Null
foreach($job in $jobs){
    $saved=Join-Path $backup $job.Relative
    New-Item -ItemType Directory -Force -Path (Split-Path $saved) | Out-Null
    Copy-Item -LiteralPath $job.Target -Destination $saved
    if((Get-FileHash -LiteralPath $saved).Hash -ne $job.Before){throw 'Backup hash mismatch'}
}
Copy-Item -LiteralPath (Join-Path $bundle 'manifest.json') -Destination (Join-Path $backup 'manifest.json')
try {
    foreach($job in $jobs){Copy-Item -LiteralPath $job.Source -Destination $job.Target}
    foreach($job in $jobs){
        if((Get-FileHash -LiteralPath $job.Target).Hash -ne $job.After){throw "Installed hash mismatch: $($job.Target)"}
    }
} catch {
    foreach($job in $jobs){Copy-Item -LiteralPath (Join-Path $backup $job.Relative) -Destination $job.Target}
    throw
}
$receipt=@{Backup=$backup;LodModels=10;StandaloneRepairs=2;Configs=2;Installed=(Get-Date -Format o)}
$receipt | ConvertTo-Json | Set-Content (Join-Path $bundle 'installation.json')
Write-Output "Installed 10 LOD models + 2 repaired models + 2 configs; hashes verified. Backup: $backup"
