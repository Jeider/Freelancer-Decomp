param([string]$GameBin, [switch]$FeatureOff, [switch]$ASan)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (-not $GameBin) { $GameBin = Join-Path $repo 'bin' }
$GameBin = (Resolve-Path $GameBin).Path
$out = Join-Path $repo 'src/obj/equipment_slots_tests'
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
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /O2 /W3 /EHsc @runtime /D_CRT_SECURE_NO_WARNINGS (Join-Path $PSScriptRoot 'test_native.cpp') /Fecheck.exe /link Common.lib dacom.lib
    if ($LASTEXITCODE -ne 0) { throw 'Native slot fixture build failed' }
    # This configuration belongs to the fixture, never to the user's game.
    [IO.File]::WriteAllText((Join-Path $out 'port.ini'), "[Equipment]`r`ninternal_classes=1`r`n")
    $mode = if ($FeatureOff) { 'off' } else { 'on' }
    & (Join-Path $out 'check.exe') (Join-Path $PSScriptRoot 'equipment.ini') $mode
    if ($LASTEXITCODE -ne 0) { throw "Native slot fixture failed ($mode): $LASTEXITCODE" }
    [IO.File]::WriteAllText((Join-Path $out 'port.ini'), "[Equipment]`r`ninternal_classes=0`r`n")
    & (Join-Path $out 'check.exe') (Join-Path $PSScriptRoot 'equipment.ini') off
    if ($LASTEXITCODE -ne 0) { throw 'Runtime-disabled compatibility check failed' }
} finally { Pop-Location }
