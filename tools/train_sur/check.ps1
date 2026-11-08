$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/train_sur_check'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$vc = 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231'
$sdk = 'C:/Program Files (x86)/Windows Kits/10'
$version = '10.0.26100.0'
$env:INCLUDE = "$repo/src/include;$vc/include;$sdk/Include/$version/ucrt;$sdk/Include/$version/shared;$sdk/Include/$version/um"
$env:LIB = "$repo/bin;$vc/lib/x86;$sdk/Lib/$version/ucrt/x86;$sdk/Lib/$version/um/x86"
$env:PATH = "$repo/bin;$env:PATH"
$commands = Get-Content -Raw (Join-Path $repo 'src/obj/Common/Release/Common.tlog/CL.command.1.tlog')
$iteratorLevel = if ($commands -match '/D _ITERATOR_DEBUG_LEVEL=(\d)') { $Matches[1] } else { '0' }
Push-Location $out
try {
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /O2 /W4 /MD /EHsc "/D_ITERATOR_DEBUG_LEVEL=$iteratorLevel" (Join-Path $PSScriptRoot 'check.cpp') /Fecheck.exe /link Common.lib DALib.lib dacom.lib
    if ($LASTEXITCODE -ne 0) { throw 'SUR checker build failed' }
    & (Join-Path $out 'check.exe') (Join-Path $repo 'out/train_sur/train_car.sur') (Join-Path $repo 'out/train_sur/train_cargo.sur')
    if ($LASTEXITCODE -ne 0) { throw 'SUR checker failed' }
} finally { Pop-Location }
