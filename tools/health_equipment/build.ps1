$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/health_equipment'
$bin = Join-Path $out 'bin'
New-Item -ItemType Directory -Force -Path $bin | Out-Null
Get-ChildItem -LiteralPath (Join-Path $repo 'bin') -File | Where-Object { $_.Extension -in '.lib', '.dll' } | ForEach-Object {
    if ($_.Name -notin 'Common.dll','Server.dll','Common.lib','Server.lib' -or -not (Test-Path -LiteralPath (Join-Path $bin $_.Name))) {
        Copy-Item -LiteralPath $_.FullName -Destination $bin -Force
    }
}
foreach ($project in 'Common','Server','freelancer') {
    $log = Join-Path $out "$project.log"
    & 'C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe' (Join-Path $repo "src/$project/$project.vcxproj") /t:Build /p:Configuration=Release /p:Platform=Win32 /p:PlatformToolset=v145 /p:FreelancerRp9=1 /p:Dx8SdkDir=C:/DXSDK /p:Dx9SdkDir=C:/DXSDK_Jun10 /p:BuildProjectReferences=false /p:FreelancerEquipmentSlots=1 /p:FreelancerPlayerFlightActions=1 "/p:OutDir=$bin/" "/p:IntDir=$out/obj/$project/" /m:4 /nr:false /v:minimal /nologo *> $log
    if ($LASTEXITCODE -ne 0) { Get-Content $log -Tail 35; throw "Build failed: $project" }
    Write-Host "PASS: $project Release Win32"
}
