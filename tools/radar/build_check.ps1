param([string]$HudIni, [string]$GameBin)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/radar_check'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$vc = 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231'
$sdk = 'C:/Program Files (x86)/Windows Kits/10'
$version = '10.0.26100.0'
$env:INCLUDE = "$vc/include;$sdk/Include/$version/ucrt;$sdk/Include/$version/shared;$sdk/Include/$version/um"
$env:LIB = "$vc/lib/x86;$sdk/Lib/$version/ucrt/x86;$sdk/Lib/$version/um/x86"
Push-Location $out
try {
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /O2 /W4 /WX /MT /EHsc (Join-Path $PSScriptRoot 'test_projection.cpp') /Fecheck.exe
    if ($LASTEXITCODE -ne 0) { throw 'Radar test build failed' }
    & (Join-Path $out 'check.exe')
    if ($LASTEXITCODE -ne 0) { throw 'Radar geometry checks failed' }
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /O2 /W4 /WX /MT /EHsc (Join-Path $PSScriptRoot 'test_vectors.cpp') /Fevectors.exe
    if ($LASTEXITCODE -ne 0) { throw 'Radar vectors build failed' }
    & (Join-Path $out 'vectors.exe')
    if ($LASTEXITCODE -ne 0) { throw 'Radar vectors checks failed' }
    if ($HudIni) {
        & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /O2 /W4 /WX /MT /EHsc (Join-Path $PSScriptRoot 'test_symbols.cpp') /Fesymbols.exe
        if ($LASTEXITCODE -ne 0) { throw 'Radar symbols build failed' }
        & (Join-Path $out 'symbols.exe')
        if ($LASTEXITCODE -ne 0) { throw 'Radar symbols checks failed' }
        if (-not $GameBin) { throw 'Use -GameBin with -HudIni for native Common.dll' }
        $env:INCLUDE += ";$repo/src/include"
        $env:LIB += ";$repo/bin"
        & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /EHsc /O2 /D_CRT_SECURE_NO_WARNINGS (Join-Path $PSScriptRoot 'test_render.cpp') /Forender.obj /Ferender.exe /link Common.lib d3d9.lib user32.lib
        if ($LASTEXITCODE -ne 0) { throw 'Radar render fixture build failed' }
        $env:PATH = "$GameBin;$env:PATH"
        & (Join-Path $out 'render.exe') $HudIni
        if ($LASTEXITCODE -ne 0) { throw 'Radar render fixture failed' }
    }
} finally { Pop-Location }
