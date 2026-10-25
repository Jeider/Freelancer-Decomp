$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/beta_evade_patch'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$vc = 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231'
$sdk = 'C:/Program Files (x86)/Windows Kits/10'
$version = '10.0.26100.0'
$env:INCLUDE = "$vc/include;$sdk/Include/$version/ucrt;$sdk/Include/$version/shared;$sdk/Include/$version/um"
$env:LIB = "$vc/lib/x86;$sdk/Lib/$version/ucrt/x86;$sdk/Lib/$version/um/x86"
$cl = "$vc/bin/Hostx64/x86/cl.exe"
Push-Location $out
try {
    & $cl /nologo /std:c++17 /O2 /W4 /WX /MT /EHsc /LD (Join-Path $PSScriptRoot 'patch.cpp') /Febeta_evade_patch.dll /link /MACHINE:X86 /DYNAMICBASE /NXCOMPAT advapi32.lib
    if ($LASTEXITCODE -ne 0) { throw 'DLL build failed' }
    & $cl /nologo /std:c++17 /O2 /W4 /WX /MT /EHsc (Join-Path $PSScriptRoot 'launcher.cpp') /Febeta_evade_launcher.exe /link /MACHINE:X86 /DYNAMICBASE /NXCOMPAT advapi32.lib user32.lib
    if ($LASTEXITCODE -ne 0) { throw 'Launcher build failed' }
    & $cl /nologo /std:c++17 /O2 /W4 /WX /MT /EHsc (Join-Path $PSScriptRoot 'test_patch.cpp') /Febeta_evade_test.exe /link /MACHINE:X86 advapi32.lib
    if ($LASTEXITCODE -ne 0) { throw 'Harness build failed' }
    & (Join-Path $out 'beta_evade_test.exe')
    if ($LASTEXITCODE -ne 0) { throw 'Harness failed' }
} finally { Pop-Location }
$files = @('beta_evade_patch.dll','beta_evade_launcher.exe')
$payload = @{}
foreach ($f in $files) { $payload[$f] = (Get-FileHash -LiteralPath (Join-Path $out $f) -Algorithm SHA256).Hash }
$sources = @{}
foreach ($f in @('patch.cpp','launcher.cpp','verified_files.h','test_patch.cpp','build.ps1','install.ps1','verify.py','README.txt')) {
    $sources[$f] = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $f) -Algorithm SHA256).Hash
}
@{format=1; sources=$sources; payload=$payload} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'payload.json') -Encoding UTF8
Write-Host "Built and hashed: $out"
