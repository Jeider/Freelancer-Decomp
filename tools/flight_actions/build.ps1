param([ValidateSet(0,1)][int]$Enabled = 1, [switch]$Isolated)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/flight_actions'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$vc = 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231'
$sdk = 'C:/Program Files (x86)/Windows Kits/10'
$ver = '10.0.26100.0'
$env:INCLUDE = "$vc/include;$sdk/Include/$ver/ucrt;$sdk/Include/$ver/shared;$sdk/Include/$ver/um"
$env:LIB = "$vc/lib/x86;$sdk/Lib/$ver/ucrt/x86;$sdk/Lib/$ver/um/x86"
Push-Location $out
try {
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /O2 /W4 /WX /MT /EHsc (Join-Path $PSScriptRoot 'test_control.cpp') /Fetest_control.exe
    if ($LASTEXITCODE -ne 0) { throw 'Flight controller harness build failed' }
    & (Join-Path $out 'test_control.exe')
    if ($LASTEXITCODE -ne 0) { throw 'Flight controller harness failed' }
} finally { Pop-Location }
$log = Join-Path $out "build_$Enabled.log"
$extra = @()
if ($Isolated) {
    $isolatedBin = Join-Path $out 'bin'
    $isolatedObj = Join-Path $out 'obj'
    New-Item -ItemType Directory -Force -Path $isolatedBin, $isolatedObj | Out-Null
    Get-ChildItem -LiteralPath (Join-Path $repo 'bin') -Filter '*.lib' | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $isolatedBin -Force
    }
    $extra = @("/p:OutDir=$isolatedBin/", "/p:IntDir=$isolatedObj/")
}
& 'C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe' (Join-Path $repo 'src/freelancer/freelancer.vcxproj') /t:Build /p:Configuration=Release /p:Platform=Win32 /p:PlatformToolset=v145 /p:FreelancerRp9=1 /p:Dx8SdkDir=C:/DXSDK /p:Dx9SdkDir=C:/DXSDK_Jun10 /p:BuildProjectReferences=false "/p:FreelancerPlayerFlightActions=$Enabled" @extra /m:4 /nr:false /v:minimal /nologo *> $log
if ($LASTEXITCODE -ne 0) { Get-Content $log -Tail 40; throw "Client build failed: $log" }
Write-Host "PASS: Release Win32, FlightActions=$Enabled. Log: $log"
