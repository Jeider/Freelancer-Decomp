$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out=Join-Path $repo 'src/obj/gravity_device_type_bin'
New-Item -ItemType Directory -Force -Path $out | Out-Null
Get-ChildItem -LiteralPath (Join-Path $repo 'src/obj/ship_trader_radar_bin') -Filter '*.lib' | Where-Object { $_.Name -ne 'Common.lib' } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $out -Force
}
foreach ($project in 'Common','Server','freelancer') {
    $log=Join-Path $repo "src/obj/gravity_device_$project.log"
    & 'C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe' (Join-Path $repo "src/$project/$project.vcxproj") /p:Configuration=Release /p:Platform=Win32 /p:PlatformToolset=v145 /p:FreelancerRp9=1 /p:Dx8SdkDir=C:/DXSDK /p:Dx9SdkDir=C:/DXSDK_Jun10 /p:BuildProjectReferences=false "/p:OutDir=$out/" /m:4 /nr:false /v:minimal /nologo *> $log
    if ($LASTEXITCODE -ne 0) { Get-Content $log -Tail 30; throw "Build failed: $project" }
    Write-Output "PASS: $project Release Win32"
}
