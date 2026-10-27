$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/cockpit_check'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$vc = 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231'
$sdk = 'C:/Program Files (x86)/Windows Kits/10'
$version = '10.0.26100.0'
$savedInclude = $env:INCLUDE
$savedLib = $env:LIB
$env:INCLUDE = "$vc/include;$sdk/Include/$version/ucrt;$sdk/Include/$version/shared;$sdk/Include/$version/um"
$env:LIB = "$vc/lib/x86;$sdk/Lib/$version/ucrt/x86;$sdk/Lib/$version/um/x86"
Push-Location $out
try {
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /O2 /W4 /WX /MT /EHsc (Join-Path $PSScriptRoot 'test_head_motion.cpp') /Fecheck.exe
    if ($LASTEXITCODE -ne 0) { throw 'Cockpit test build failed' }
    & (Join-Path $out 'check.exe')
    if ($LASTEXITCODE -ne 0) { throw 'Cockpit head motion checks failed' }
} finally {
    Pop-Location
    $env:INCLUDE = $savedInclude
    $env:LIB = $savedLib
}
