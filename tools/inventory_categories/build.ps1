param([switch]$ClientOnly)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/inventory_categories'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$shared = @('/p:Configuration=Release', '/p:Platform=Win32', '/p:PlatformToolset=v145', '/p:Dx8SdkDir=C:/DXSDK', '/p:BuildProjectReferences=false', '/p:FreelancerModPlugins=1', '/p:FreelancerAdoxa=1')
$features = @('/p:FreelancerFlsharp=1', '/p:FreelancerLanguage=1', '/p:FreelancerEquipmentSlots=1', '/p:FreelancerPlayerAutoTurrets=1', '/p:FreelancerDbgOptions=1', '/p:FreelancerFlplusplus=1', '/p:FreelancerJflp=1')
$client = @('/p:FreelancerRp9=1', '/p:Dx9SdkDir=C:/DXSDK_Jun10', '/p:FreelancerPlayerFlightActions=1', '/p:FreelancerParticleFx=1', '/p:FreelancerPreciseRender=1', '/p:FreelancerHudInventoryView=1', '/p:FreelancerHudStatusView=1', '/p:FreelancerHudTargetView=1', '/p:FreelancerWalkMode=1')
$projects = if ($ClientOnly) { @('freelancer') } else { @('Common', 'Content', 'freelancer') }
foreach ($project in $projects) {
    $extra = @()
    if ($project -ne 'Content') { $extra += $features }
    if ($project -eq 'freelancer') { $extra += $client }
    $log = Join-Path $out "build_$project.log"
    & 'C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe' (Join-Path $repo "src/$project/$project.vcxproj") /t:Build @shared @extra /m:4 /nr:false /v:minimal /nologo *> $log
    if ($LASTEXITCODE -ne 0) { Get-Content $log -Tail 30; throw "$project build failed" }
    Write-Output "PASS: $project Release Win32"
}
