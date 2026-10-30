$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/hud_tilt_checks'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$vc = 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231'
$sdk = 'C:/Program Files (x86)/Windows Kits/10'
$ver = '10.0.26100.0'
$env:INCLUDE = "$vc/include;$sdk/Include/$ver/ucrt;$sdk/Include/$ver/shared;$sdk/Include/$ver/um"
$env:LIB = "$vc/lib/x86;$sdk/Lib/$ver/ucrt/x86;$sdk/Lib/$ver/um/x86"
Push-Location $out
try {
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /W4 /WX /EHsc /MT (Join-Path $PSScriptRoot 'check.cpp') /Fecheck.exe
    if ($LASTEXITCODE -ne 0) { throw 'Math harness compilation failed' }
    & ./check.exe
    if ($LASTEXITCODE -ne 0) { throw 'Math harness failed' }
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /W4 /WX /EHsc /MT /c (Join-Path $repo 'src/freelancer/Client/hud_tilt.cpp') /Fohud_tilt_disabled.obj
    if ($LASTEXITCODE -ne 0) { throw 'Non-RP9 fallback failed' }
    $fxc = "$sdk/bin/$ver/x64/fxc.exe"
    foreach ($stage in @(@('vs_3_0','VSMain'),@('ps_3_0','PSMain'))) {
        & $fxc /nologo /WX /T $stage[0] /E $stage[1] /Fo "$($stage[1]).bin" (Join-Path $repo 'DATA_EXTRA/SHADERS/hud_tilt.hlsl')
        if ($LASTEXITCODE -ne 0) { throw 'HUD shader compilation failed' }
    }
    Write-Output 'PASS: shader model 3 VS/PS and non-RP9 fallback'
} finally { Pop-Location }
