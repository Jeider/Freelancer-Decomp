"""Build and run a hidden GPU check against the current Release RP9 objects."""
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
out = root / 'src/obj/hud_tilt_checks'
out.mkdir(parents=True, exist_ok=True)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
dx = Path('C:/DXSDK_Jun10')
env = os.environ.copy()
env['PATH'] = str(root / 'bin') + os.pathsep + env.get('PATH', '')
env['FREELANCER_SHADER_CACHE_DIR'] = str(out / 'cache')
env['INCLUDE'] = ';'.join(map(str, [vc/'include', sdk/f'Include/{version}/ucrt', sdk/f'Include/{version}/shared', sdk/f'Include/{version}/um', dx/'Include', root/'src/RP9']))
env['LIB'] = ';'.join(map(str, [vc/'lib/x86', sdk/f'Lib/{version}/ucrt/x86', sdk/f'Lib/{version}/um/x86']))
exe = out / 'gpu.exe'
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/O2', '/std:c++17', '/EHsc', '/MD', '/DRP_DIRECT3D9', '/D_ITERATOR_DEBUG_LEVEL=1', '/DNOMINMAX', '/D_CRT_SECURE_NO_WARNINGS', f'/I{root/"src/include"}', str(root/'tools/hud_tilt/gpu.cpp'), f'/Fe{exe}', *[str(root/f'src/obj/RP9/Release/{n}.obj') for n in ['RP9','RP9Ex','Mgsdb']], '/link', '/LTCG', f'/LIBPATH:{root/"bin"}', 'dacom.lib', 'user32.lib', 'd3d9.lib', 'ddraw.lib', 'version.lib', 'legacy_stdio_definitions.lib', str(dx/'Lib/x86/d3dx9.lib'), str(dx/'Lib/x86/DxErr.lib')], cwd=out, env=env, check=True)
subprocess.run([str(exe)], cwd=root, env=env, check=True)
