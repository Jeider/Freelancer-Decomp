"""Isolated GPU timestamp benchmark of the installed Nomad material, without game edits."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
out = root / 'src/obj/nomad_surfaces'
out.mkdir(parents=True, exist_ok=True)
source = root / 'DATA_EXTRA/SHADERS/surface_material.hlsl'
installed = Path('D:/games/FL_MOD/DATA_EXTRA/SHADERS/surface_material.hlsl')
assert source.read_bytes() == installed.read_bytes(), 'Benchmark must match installed shader'
vc = sorted(Path('C:/Program Files/Microsoft Visual Studio').glob('*/Community/VC/Tools/MSVC/*'))[-1]
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = sorted(p.name for p in (sdk/'Include').iterdir() if (p/'um/Windows.h').exists())[-1]
dx = Path('C:/DXSDK_Jun10')
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str, [vc/'include', sdk/f'Include/{version}/ucrt', sdk/f'Include/{version}/shared', sdk/f'Include/{version}/um', dx/'Include', root/'src/RP9']))
env['LIB'] = ';'.join(map(str, [vc/'lib/x86', sdk/f'Lib/{version}/ucrt/x86', sdk/f'Lib/{version}/um/x86']))
env['FREELANCER_SHADER_CACHE_DIR'] = str(out/'cache')
env['NOMAD_QUICK'] = '1'
exe = out/'benchmark.exe'
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/O2', '/std:c++17', '/EHsc', '/MT', '/DNOMINMAX', '/D_CRT_SECURE_NO_WARNINGS', '/DNOMAD_BENCHMARK', str(root/'tools/nomad_surfaces/check.cpp'), f'/Fe{exe}', '/link', 'user32.lib', 'd3d9.lib', str(dx/'Lib/x86/d3dx9.lib')], cwd=out, env=env, check=True)
shutil.copy2(root/'bin/d3dx9_43.dll', out/'d3dx9_43.dll')
for width in (1920, 3840):
    env['NOMAD_BENCH_WIDTH'] = str(width)
    log = out/f'benchmark_{width}.txt'
    with log.open('w') as f:
        f.write(f'Shader SHA256 {hashlib.sha256(source.read_bytes()).hexdigest()}\n')
        f.flush()
        result = subprocess.run([str(exe)], cwd=root, env=env, stdout=f, stderr=subprocess.STDOUT)
    print(log.read_text(), flush=True)
    result.check_returncode()
