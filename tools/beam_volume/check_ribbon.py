"""Compile the production ALE ribbon emitter with an in-memory draw context."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
out = root / 'src/obj/beam_volume'
out.mkdir(parents=True, exist_ok=True)
source = (root / 'src/Alchemy/alchemy_appearances.cpp').read_text(encoding='utf8')
begin = source.index('    void FLBeamAppearance::FillCameraRibbon()')
end = source.index('    #pragma float_control', begin)
fixture = (root / 'tools/beam_volume/ribbon_fixture.cpp').read_text()
(out / 'ribbon.cpp').write_text(fixture.replace('// PRODUCTION_EMITTER', source[begin:end]))
build = out / 'ribbon.cmd'
build.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
                 'if errorlevel 1 exit /b 1\n'
                 'cl /nologo /EHsc /O2 /std:c++17 /Isrc/include src/obj/beam_volume/ribbon.cpp '
                 '/Fosrc/obj/beam_volume/ribbon.obj /Febin/beam_ribbon_check.exe\n'
                 'if errorlevel 1 exit /b 1\nbin\\beam_ribbon_check.exe\n')
subprocess.run(['cmd', '/c', str(build)], cwd=root, check=True)
