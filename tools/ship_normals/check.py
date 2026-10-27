"""Verify generated assets and render production normal-map shader on D3D9."""
import hashlib, io, json, os, struct, subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from generate import derive,derive_surface
from solar_content import HUMAN_LIBRARIES, artificial_material, human_solars
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'src/obj/ship_normals'

# A painted dark channel must indent, not bulge; constant colour stays flat.
pixels=np.full((64,64,3),200,np.uint8);pixels[:,24:40]=30
b=io.BytesIO();Image.fromarray(pixels).save(b,format='PNG')
_,_,normal=derive(b.getvalue())
assert normal[32,23,3]>.55 and normal[32,40,3]<.45, 'dark groove slopes point inward'
pixels[:]=100;b=io.BytesIO();Image.fromarray(pixels).save(b,format='PNG')
_,_,normal=derive(b.getvalue());assert np.max(np.abs(normal[:,:,[1,3]]-.5))<1e-5
r=json.loads((OUT/'generation.json').read_text());assets=OUT/'assets/DATA_EXTRA/SHIP_NORMALS'
profiles=(assets/'profiles.txt').read_text(encoding='latin1').splitlines()
solar_profiles=(assets/'solar_profiles.txt').read_text(encoding='latin1').splitlines()
assert 'solar_mat_dyson.mat' not in HUMAN_LIBRARIES
for name in ('detailmap_ast_rock02','detailmap_ast_ice','detailmap_b'):
    assert not artificial_material(name,'rock3b.tga')
for row in solar_profiles:
    _,key=row.split(' ',1)
    assert artificial_material(*key.split('|'))
assert set((assets/'human_solars.txt').read_text().splitlines())==human_solars(Path(r['game']))
assert 'solar/dockable/trading_outpost_lod.cmp' in human_solars(Path(r['game']))
profiles+=solar_profiles
assert len(profiles)==r['profiles']
for row in profiles:
    name,key=row.split(' ',1)
    assert name in r['maps'] and 'nmd' not in key and 'nomad' not in key
for name,info in r['maps'].items():
    data=(assets/name).read_bytes()
    assert hashlib.sha256(data).hexdigest()==info['sha256']
    assert data[:4]==b'DDS ' and data[84:88]==(b'DXT1' if info.get('kind')=='surface' else b'DXT5')
    h,w=struct.unpack_from('<II',data,12);mips=struct.unpack_from('<I',data,28)[0]
    assert max(h,w)<=512 and mips==max(h,w).bit_length()
    if info.get('kind')=='surface':
        decoded=np.asarray(Image.open(io.BytesIO(data)).convert('RGB'),np.float32)/255
        assert decoded[:,:,0].min()>.47 and decoded[:,:,0].max()<.83
        # BC1 endpoint fitting can overshoot; the shader clamps coverage to .55.
        assert decoded[:,:,1].max()<.65 and decoded[:,:,2].min()>.85
assert set(r['surface_maps']).issubset(row.split(' ',1)[0] for row in profiles)
for diffuse,material in r['surface_maps'].items():
    assert r['maps'][diffuse]['kind']=='normal' and r['maps'][material]['kind']=='surface'
for rel,sha in r['source_files'].items():
    assert hashlib.sha256((Path(r['game'])/rel).read_bytes()).hexdigest()==sha,rel
assert any('nmd' in model for model in (assets/'excluded_models.txt').read_text().splitlines())
print(f'PASS: dark recess sign, flat colour, {len(profiles)} profiles, {len(r["maps"])} compressed mipchains, original assets unchanged',flush=True)
build=OUT/'check.cmd'
build.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
 'if errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
 'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /Isrc/RP9 /Isrc/include '
 'tools/ship_normals/check.cpp /Fosrc/obj/ship_normals/check.obj /Febin/ship_normal_check.exe '
 '/link d3d9.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" user32.lib\n')
subprocess.run(['cmd','/c',str(build)],cwd=ROOT,check=True)
env=dict(os.environ,FREELANCER_SHADER_CACHE_DIR=str(OUT/'test_cache'))
subprocess.run([str(ROOT/'bin/ship_normal_check.exe')],cwd=ROOT,env=env,check=True)
