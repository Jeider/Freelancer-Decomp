# Read-only GPU/process counters. Does not start, stop, suspend or alter any game.
param([int]$Samples=12,[string]$OutputPath="out/graphics_settings/nebula_asteroid_mesh/lod/live/gpu.json")
$ErrorActionPreference="Stop"
$names=@{}
Get-Process | ForEach-Object {$names[$_.Id]=$_.ProcessName}
$rows=@()
for($sample=0;$sample -lt $Samples;$sample++){
    $gpu=(& nvidia-smi --query-gpu=timestamp,utilization.gpu,utilization.memory,memory.used,power.draw,clocks.gr,temperature.gpu --format=csv,noheader,nounits | Select-Object -First 1).Split(',').Trim()
    $engines=@(Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine | Where-Object UtilizationPercentage -gt 0 | ForEach-Object {
        $instance=$_.Name
        if($instance -match '^pid_(\d+)_.*_eng_\d+_engtype_(.+)$'){
            $processId=[int]$Matches[1]
            [pscustomobject]@{pid=$processId;process=$names[$processId];engine=$Matches[2];percent=[int]$_.UtilizationPercentage;instance=$instance}
        }
    })
    $rows += [pscustomobject]@{time=$gpu[0];gpu_percent=[double]$gpu[1];memory_percent=[double]$gpu[2];memory_mib=[double]$gpu[3];power_w=[double]$gpu[4];clock_mhz=[double]$gpu[5];temperature_c=[double]$gpu[6];engines=$engines}
    if($sample+1 -lt $Samples){Start-Sleep -Seconds 1}
}
$target=[System.IO.Path]::GetFullPath($OutputPath)
$workspace=[System.IO.Path]::GetFullPath((Get-Location).Path)+[System.IO.Path]::DirectorySeparatorChar
if(-not $target.StartsWith($workspace,[System.StringComparison]::OrdinalIgnoreCase)){throw "Output must stay in workspace"}
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($target)) | Out-Null
$rows | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $target -Encoding UTF8
$rows | Measure-Object gpu_percent,power_w,temperature_c -Average -Minimum -Maximum | Select-Object Property,Average,Minimum,Maximum
$rows.engines | Group-Object process,engine | ForEach-Object {
    [pscustomobject]@{process_engine=$_.Name;mean_percent_over_interval=($_.Group | Measure-Object percent -Sum).Sum/$Samples;maximum=($_.Group | Measure-Object percent -Maximum).Maximum}
} | Sort-Object mean_percent_over_interval -Descending | Select-Object -First 8
