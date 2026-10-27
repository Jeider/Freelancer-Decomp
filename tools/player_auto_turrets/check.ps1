param([string]$GameBin, [switch]$ASan)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (-not $GameBin) { $GameBin = Join-Path $repo $(if ($ASan) { 'binasan' } else { 'bin' }) }
$GameBin = (Resolve-Path $GameBin).Path
$variant = if ($ASan) { 'asan' } else { 'release' }
$out = Join-Path $repo "src/obj/player_auto_turrets_tests/$variant"
New-Item -ItemType Directory -Path $out -Force | Out-Null
$vc = 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231'
$sdk = 'C:/Program Files (x86)/Windows Kits/10'
$version = '10.0.26100.0'
$env:INCLUDE = "$vc/include;$sdk/Include/$version/ucrt;$sdk/Include/$version/shared;$sdk/Include/$version/um;$repo/src/include;C:/DXSDK/Include"
$env:LIB = "$vc/lib/x86;$sdk/Lib/$version/ucrt/x86;$sdk/Lib/$version/um/x86;$GameBin"
$env:PATH = "$GameBin;$vc/bin/Hostx64/x86;$env:PATH"
Push-Location $out
try {
    $runtime = if ($ASan) { @('/MDd', '/D_ITERATOR_DEBUG_LEVEL=2', '/fsanitize=address', '/Zi') } else { @('/MD', '/D_ITERATOR_DEBUG_LEVEL=1') }
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /O2 /W3 /EHsc @runtime (Join-Path $PSScriptRoot 'test_native.cpp') /Fecheck.exe /link Common.lib dacom.lib
    if ($LASTEXITCODE -ne 0) { throw 'Auto turret fixture build failed' }
    & (Join-Path $out 'check.exe')
    if ($LASTEXITCODE -ne 0) { throw "Auto turret fixture failed: $LASTEXITCODE" }
} finally { Pop-Location }
