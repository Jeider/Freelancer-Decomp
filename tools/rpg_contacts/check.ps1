$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out = Join-Path $repo 'src/obj/rpg_contacts/test'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$source = Get-Content -LiteralPath (Join-Path $repo 'src/Content/RpgContacts.cpp') -Raw
$source = [regex]::Replace($source, '(?m)^#include "[^"]+"\r?\n', '')
[IO.File]::WriteAllText((Join-Path $out 'runtime.inc'), $source)
$space = Get-Content -LiteralPath (Join-Path $repo 'src/Content/RpgSpace.cpp') -Raw
$space = [regex]::Replace($space, '(?m)^#include "[^"]+"\r?\n', '')
[IO.File]::WriteAllText((Join-Path $out 'space_runtime.inc'), $space)
$generic = Get-Content -LiteralPath (Join-Path $repo 'src/Content/GenericScripts.cpp') -Raw
$entry = [regex]::Match($generic, '(?s)void __cdecl StartBarCharacterScript\(.*?\n\}').Value
if (!$entry) { throw 'Cannot find production generic-script entry point' }
[IO.File]::WriteAllText((Join-Path $out 'generic_entry.inc'), $entry)
$vc = 'C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231'
$sdk = 'C:/Program Files (x86)/Windows Kits/10'
$ver = '10.0.26100.0'
$env:INCLUDE = "$vc/include;$sdk/Include/$ver/ucrt;$sdk/Include/$ver/shared;$sdk/Include/$ver/um"
$env:LIB = "$vc/lib/x86;$sdk/Lib/$ver/ucrt/x86;$sdk/Lib/$ver/um/x86"
Push-Location $out
try {
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /O2 /W4 /WX /MT /EHsc /I. (Join-Path $PSScriptRoot 'test_runtime.cpp') /Fetest.exe
    if ($LASTEXITCODE -ne 0) { throw 'RPG runtime harness build failed' }
    & ./test.exe
    if ($LASTEXITCODE -ne 0) { throw 'RPG runtime harness failed' }
    & "$vc/bin/Hostx64/x86/cl.exe" /nologo /std:c++17 /O2 /W4 /WX /MT /EHsc /I. (Join-Path $PSScriptRoot 'test_space.cpp') /Fespace_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'RPG space harness build failed' }
    & ./space_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'RPG space harness failed' }
} finally { Pop-Location }
