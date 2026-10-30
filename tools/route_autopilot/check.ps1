$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'check_controls.py')
if ($LASTEXITCODE -ne 0) { throw 'Route input harness failed' }
& python (Join-Path $PSScriptRoot 'check_object_routes.py')
if ($LASTEXITCODE -ne 0) { throw 'Object approach harness failed' }
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/route_autopilot/test'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$vc = 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231'
$sdk = 'C:/Program Files (x86)/Windows Kits/10'
$ver = '10.0.26100.0'
$env:INCLUDE = "$vc/include;$sdk/Include/$ver/ucrt;$sdk/Include/$ver/shared;$sdk/Include/$ver/um"
$env:LIB = "$vc/lib/x86;$sdk/Lib/$ver/ucrt/x86;$sdk/Lib/$ver/um/x86"
Push-Location $out
try {
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /O2 /W4 /WX /MT /EHsc (Join-Path $PSScriptRoot 'test_route.cpp') /Fetest_route.exe
    if ($LASTEXITCODE -ne 0) { throw 'Route harness build failed' }
    & (Join-Path $out 'test_route.exe')
    if ($LASTEXITCODE -ne 0) { throw 'Route harness failed' }
} finally { Pop-Location }
