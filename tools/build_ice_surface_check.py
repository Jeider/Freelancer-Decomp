"""Compile/run the real SM3 ice shader, preserving test inputs outside game DATA."""
from pathlib import Path
import os
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
import generate_station_lods as utf

root = Path(__file__).resolve().parents[1]
out = root / 'src/obj/ice_surface_check'
out.mkdir(parents=True, exist_ok=True)
game = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('D:/games/FL_MOD')


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.children)


_, tree = utf.read_tree((game / 'DATA/SOLAR/ast_ice.mat').read_bytes())
material = next(n for n in walk(tree) if n.name == 'ast_icecrystal2' and n.children)
properties = {n.name: n.blob for n in material.children}
assert properties['Type'].rstrip(b'\0') == b'DcDt', properties
assert properties['Dt_name'].rstrip(b'\0') == b'ast_icecrystal2.tga'
texture = next(n for n in walk(tree) if n.name == 'ast_icecrystal2.tga' and n.children)
(out / 'base.dds').write_bytes(texture.children[0].blob)
_, tree = utf.read_tree((game / 'DATA/SOLAR/ASTEROIDS_MOD/ICE/ice_ast_super.cmp').read_bytes())
mesh = next(n for n in walk(tree) if n.name == 'VMeshData')
# This authored CMP has one trailing NUL after the advertised vertex data.
_, _, group_count, index_count, fvf, vertex_count = struct.unpack_from('<II4H', mesh.blob)
assert fvf == 0x112
mesh_size = 16 + group_count*12 + index_count*2 + vertex_count*32
part = next(n for n in walk(tree) if n.name.startswith('ast01_') and n.name.endswith('.3db'))
level = next(n for n in walk(part.children) if n.name == 'Level0')
ref = next(n for n in walk(level.children) if n.name == 'VMeshRef')
_, _, base_vertex, _, first_index, _, first_group, ref_groups = struct.unpack_from('<II6H', ref.blob)
# CMP contains three independent asteroid parts with their own transforms.
# Show exactly the ast01 Level0 range; combining the raw buffers causes overlap.
corners = []
index_base = 16 + group_count*12
vertex_base = index_base + index_count*2
index_cursor = first_index
for i in range(first_group, first_group+ref_groups):
    material_crc, vertex_begin, _, count, _ = struct.unpack_from('<I4H', mesh.blob, 16+i*12)
    indices = struct.unpack_from(f'<{count}H', mesh.blob, index_base+index_cursor*2)
    index_cursor += count
    if material_crc == utf.crc('ast_icecrystal2'):
        for index in indices:
            vertex = base_vertex + vertex_begin + index
            assert vertex < vertex_count
            corners.append(struct.unpack_from('<8f', mesh.blob, vertex_base+vertex*32))
assert corners
center = [(max(v[k] for v in corners) + min(v[k] for v in corners)) * .5 for k in range(3)]
extent = max(abs(v[k] - center[k]) for v in corners for k in range(3))
data = b''.join(struct.pack('<8f', *[(v[k]-center[k])/extent for k in range(3)], *v[3:]) for v in corners)
(out / 'mesh.bin').write_bytes(data)
print(f'Actual Tau31 input: DcDt/ast_icecrystal2, ast01/Level0 {len(corners)//3} triangles, original DDS', flush=True)
(out / 'baseline.hlsl').write_bytes(subprocess.check_output(['git', 'show', 'HEAD:DATA_EXTRA/SHADERS/surface_material.hlsl'], cwd=root))
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat')
sdk = Path('C:/DXSDK_Jun10')
build = out / 'build.cmd'
build.write_text(f'@echo off\ncall "{vc}" > nul\nif errorlevel 1 exit /b 1\n'
    f'set "INCLUDE=%INCLUDE%;{sdk / "Include"}"\n'
    'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /Isrc\\RP9 '
    'tools\\check_ice_surface.cpp /Fosrc\\obj\\ice_surface_check\\check.obj '
    '/Fesrc\\obj\\ice_surface_check\\check.exe '
    f'/link d3d9.lib "{sdk / "Lib/x86/d3dx9.lib"}" user32.lib\n')
subprocess.run(['cmd', '/c', str(build)], cwd=root, check=True)
env = dict(os.environ)
env['PATH'] = str(root / 'bin') + os.pathsep + env.get('PATH', '')
env['FREELANCER_SHADER_CACHE_DIR'] = str(root / 'src/obj/ice_surface_cache')
subprocess.run([str(out / 'check.exe')], cwd=root, env=env, check=True)

# Link the route fixture against the freshly built production RP9 object files.
# Build RP9 Release first; its STL configuration uses iterator checks in Release.
route = out / 'route_build.cmd'
route.write_text(f'@echo off\ncall "{vc}" > nul\nif errorlevel 1 exit /b 1\n'
    f'set "INCLUDE=%INCLUDE%;{sdk / "Include"}"\n'
    'cl /nologo /EHsc /MD /O2 /std:c++17 /DRP_DIRECT3D9 /D_ITERATOR_DEBUG_LEVEL=1 '
    '/D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /Isrc\\RP9 /Isrc\\include '
    'tools\\check_ice_surface_route.cpp /Fosrc\\obj\\ice_surface_check\\route.obj '
    '/Febin\\ice_surface_route_check.exe src\\obj\\RP9\\Release\\RP9.obj '
    'src\\obj\\RP9\\Release\\RP9Ex.obj src\\obj\\RP9\\Release\\Mgsdb.obj '
    '/link /LTCG /LIBPATH:bin dacom.lib d3d9.lib ddraw.lib version.lib '
    f'"{sdk / "Lib/x86/d3dx9.lib"}" "{sdk / "Lib/x86/DxErr.lib"}" '
    'legacy_stdio_definitions.lib user32.lib\n')
subprocess.run(['cmd', '/c', str(route)], cwd=root, check=True)
subprocess.run([str(root / 'bin/ice_surface_route_check.exe')], cwd=root, env=env, check=True)
