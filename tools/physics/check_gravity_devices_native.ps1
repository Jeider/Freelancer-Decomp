param([string]$Built)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out=Join-Path $repo 'src/obj/gravity_devices_native_check'
if (-not $Built) { $Built=Join-Path $repo 'src/obj/gravity_device_type_bin' }
$vc='C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231'
$sdk='C:/Program Files (x86)/Windows Kits/10'
$v='10.0.26100.0'
New-Item -ItemType Directory -Force -Path $out | Out-Null
Copy-Item -LiteralPath (Join-Path $built 'Common.dll') -Destination $out
$env:INCLUDE="$vc/include;$sdk/Include/$v/ucrt;$sdk/Include/$v/shared;$sdk/Include/$v/um;$repo/src/include;C:/DXSDK/Include"
$env:LIB="$vc/lib/x86;$sdk/Lib/$v/ucrt/x86;$sdk/Lib/$v/um/x86;$built"
$env:PATH="D:/games/FL_MOD/bin;$env:PATH"
[IO.File]::WriteAllText((Join-Path $out 'port.ini'), "[Equipment]`r`ninternal_classes=1`r`n")
Push-Location $out
try {
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /W4 /EHsc /MD /D_ITERATOR_DEBUG_LEVEL=1 /D_CRT_SECURE_NO_WARNINGS (Join-Path $PSScriptRoot 'check_gravity_devices_native.cpp') /Fecheck.exe /link Common.lib dacom.lib
    if ($LASTEXITCODE -ne 0) {throw 'Native fixture compilation failed'}
    & ./check.exe (Join-Path $repo 'DATA/EQUIPMENT/gravity_devices.ini') (Join-Path $repo 'DATA/EQUIPMENT/repair_devices.ini')
    if ($LASTEXITCODE -ne 0) {throw "Native gravity equipment fixture failed: $LASTEXITCODE"}
} finally {Pop-Location}
