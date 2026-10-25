$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/radar_check'
$vc = 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231'
$sdk = 'C:/Program Files (x86)/Windows Kits/10'
$version = '10.0.26100.0'
$env:INCLUDE = "$vc/include;$sdk/Include/$version/ucrt;$sdk/Include/$version/shared;$sdk/Include/$version/um;$repo/src/include"
$env:LIB = "$vc/lib/x86;$sdk/Lib/$version/ucrt/x86;$sdk/Lib/$version/um/x86;$repo/bin"
$env:PATH = "$repo/bin;$env:PATH"
Push-Location $out
try {
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /EHsc /O2 /MD /D_ITERATOR_DEBUG_LEVEL=1 (Join-Path $PSScriptRoot 'test_solars.cpp') /Fosolars.obj /Fesolars.exe /link Common.lib
    if ($LASTEXITCODE -ne 0) { throw 'Solar test build failed' }
    & (Join-Path $out 'solars.exe')
    if ($LASTEXITCODE -ne 0) { throw "Solar test failed: $LASTEXITCODE" }
} finally { Pop-Location }
