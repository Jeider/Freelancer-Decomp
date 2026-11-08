param([ValidateSet(0,1)][int]$Enabled = 1, [switch]$Client,
      [ValidateSet('Release','DebugASan')][string]$Configuration = 'Release')
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$project = if ($Client) { 'freelancer' } else { 'Content' }
$suffix = if ($Client) { '_client' } else { '' }
$out = Join-Path $repo "src/obj/rpg_contacts/build_${Configuration}_${Enabled}$suffix"
$dll = Join-Path $out 'bin'
$obj = Join-Path $out 'obj'
New-Item -ItemType Directory -Force -Path $out, $dll, $obj | Out-Null
Get-ChildItem -LiteralPath (Join-Path $repo 'bin') -Filter '*.lib' | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $dll -Force
}
$log = Join-Path $out 'build.log'
$env:LIB = "$dll;$env:LIB"
& 'C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe' (Join-Path $repo "src/$project/$project.vcxproj") /t:Build "/p:Configuration=$Configuration" /p:Platform=Win32 /p:PlatformToolset=v145 /p:FreelancerRp9=1 /p:Dx8SdkDir=C:/DXSDK /p:Dx9SdkDir=C:/DXSDK_Jun10 /p:BuildProjectReferences=false "/p:FreelancerRpgWorld=$Enabled" "/p:FlASanOutDir=$dll" "/p:OutDir=$dll/" "/p:IntDir=$obj/" /m:4 /nr:false /v:minimal /nologo *> $log
if ($LASTEXITCODE -ne 0) { Get-Content $log -Tail 45; throw "Content build failed: $log" }
Write-Host "PASS: $project $Configuration Win32 RPG=$Enabled. $log"
