"""Offline RP9 probe of Lutz's installed head; never starts or modifies the game."""
import hashlib
import argparse
import json
import os
import struct
import subprocess

from build import ROOT, GAME, read_tree, child, blob, arr, triangles

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--staged', action='store_true')
args = parser.parse_args()
TOPIC = ROOT / 'out/hair_lighting/lutz'
OUT = TOPIC / ('probe_after' if args.staged else 'probe_before')
OUT.mkdir(parents=True, exist_ok=True)
source = (TOPIC/'stage' if args.staged else GAME) / 'DATA/CHARACTERS/HEADS/rh_sales_head.dfm'
root = read_tree(source.read_bytes())[1][0]
geo = child(child(child(root, 'MultiLevel'), 'Mesh0'), 'Geometry')
points = arr(geo, 'Points', '<f4', 3)
normals = arr(geo, 'Vertex_normals', '<f4', 3)
pi = arr(geo, 'Point_indices', '<u4').ravel()
uv = arr(geo, 'UV0', '<f4', 2)
ui = arr(geo, 'UV0_indices', '<u4').ravel()
groups = child(child(child(root, 'MultiLevel'), 'Mesh0'), 'Face_groups')
selected = [g for g in groups.children if g.children and
            blob(g, 'Material_name').rstrip(b'\0').decode() in
            ('rh_sales_head01', 'short_hair_rh_sales_head01')]
with (OUT / 'head.bin').open('wb') as output:
    output.write(struct.pack('<I', len(selected)))
    for group in selected:
        name = blob(group, 'Material_name').rstrip(b'\0').decode()
        indices = [v for tri in triangles(group) for v in tri]
        output.write(struct.pack('<II', int(name.startswith('short_hair_')), len(indices)))
        for v in indices:
            output.write(struct.pack('<8f', *points[pi[v]], *normals[pi[v]], uv[ui[v]][0], 1-uv[ui[v]][1]))
atlas = blob(child(child(root, 'Texture library'), 'rh_sales_head02.TGA'), 'MIP0')
(OUT / 'diffuse.tga').write_bytes(atlas)
(OUT / 'inputs.json').write_text(json.dumps({'head': str(source),
    'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'description': 'Actual LOD0 face/hair geometry and texture, neutral pose; synthetic lighting, offline RP9'}, indent=2))
cmd = OUT / 'build.cmd'
objects = ROOT / 'out/base_neural/on/obj/RP9'
cmd.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
    'if errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
    'cl /nologo /EHsc /MD /O2 /std:c++17 /DRP_DIRECT3D9 /DFREELANCER_DLSS5 /D_ITERATOR_DEBUG_LEVEL=1 '
    '/D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /Isrc/RP9 /Isrc/include tools/hatcher_hair/check_lutz.cpp '
    '/Foout/hair_lighting/lutz/check.obj /Febin/lutz_material_check.exe '
    f'"{objects}/RP9.obj" "{objects}/RP9Ex.obj" "{objects}/Mgsdb.obj" '
    '/link /LTCG /LIBPATH:bin dacom.lib d3d9.lib ddraw.lib version.lib '
    '"C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" "C:/DXSDK_Jun10/Lib/x86/DxErr.lib" legacy_stdio_definitions.lib user32.lib\n')
with (OUT / 'build.log').open('w') as log:
    result = subprocess.run(['cmd', '/c', str(cmd)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
if result.returncode:
    print((OUT / 'build.log').read_text(errors='replace'))
    raise SystemExit(result.returncode)
env = dict(os.environ, FREELANCER_SHADER_CACHE_DIR=str(OUT / 'shader_cache'))
result = subprocess.run([str(ROOT / 'bin/lutz_material_check.exe'), str(OUT)], cwd=ROOT, env=env,
                        capture_output=True, text=True)
(OUT / 'gpu.log').write_text(result.stdout + result.stderr)
print(result.stdout + result.stderr)
raise SystemExit(result.returncode)
