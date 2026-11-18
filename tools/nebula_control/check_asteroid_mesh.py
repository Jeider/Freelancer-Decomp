"""Validate the Omega-15 decorative mesh layer using actual assets and a hidden D3D9 probe."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh'
PROBE=OUT/'probe'
DATA=Path('D:/Games/FL_MOD/DATA')
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/nebula_control')]
from repair_panel_normals import leaves,triangles
from generate_station_lods import crc
from build_asf_hq import compiler_env

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    PROBE.mkdir(parents=True,exist_ok=True)
    compiler,env=compiler_env()
    env['INCLUDE']=';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper())+';C:/DXSDK_Jun10/Include'
    env['PATH']=str(ROOT/'bin')+';D:/Games/FL_MOD/bin;'+env['PATH']
    env['TEMP']=env['TMP']=str(PROBE)
    sources=['src/freelancer/Client/far_rocks.cpp','src/freelancer/Client/nebula_asteroid_mesh.h','DATA_EXTRA/SHADERS/far_rocks.hlsl']
    before={p:digest(ROOT/p) for p in sources}
    assets={}
    material=DATA/'SOLAR/ASTEROIDS_MOD/om15/ast_om15.mat'
    assets[str(material)]=digest(material)
    library=leaves(material.read_bytes())[1]
    texture_names={crc(n.split('/')[-2]):b.rstrip(b'\0').decode('ascii') for n,_,b in library if n.lower().endswith('/dt_name')}
    arguments=[]; models=[]
    for letter in 'abc':
        path=DATA/f'SOLAR/ASTEROIDS_MOD/om15/ast_o15_nrml_{letter}.3db'
        assets[str(path)]=digest(path)
        nodes=leaves(path.read_bytes())[1]
        blob=next(b for n,_,b in nodes if n.lower().endswith('/vmeshdata'))
        _,descriptors,groups=triangles(blob)
        assert len(groups)==1
        texture_name=texture_names[descriptors[0][0]]
        texture=next(b for n,_,b in library+nodes if n.lower().endswith('/'+texture_name.lower()+'/mips') or n.lower().endswith('/'+texture_name.lower()+'/mip0'))
        vertices=[list(struct.unpack('<8f',v)) for v in groups[0]]
        centre=[(min(v[k] for v in vertices)+max(v[k] for v in vertices))/2 for k in range(3)]
        radius=max(math.dist(v[:3],centre) for v in vertices)
        for v in vertices:
            v[:3]=[(v[k]-centre[k])/radius for k in range(3)]
        mesh_file,texture_file=PROBE/(letter+'.bin'),PROBE/(letter+'.texture')
        mesh_file.write_bytes(struct.pack('<I',len(vertices))+b''.join(struct.pack('<8f',*v) for v in vertices))
        texture_file.write_bytes(texture)
        arguments += [str(mesh_file),str(texture_file),str(radius)]
        models.append(dict(name=path.name,triangles=len(vertices)//3,radius=radius,texture=texture_name))
    exe=PROBE/'check.exe'
    command=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/utf-8','/DNOMINMAX','/D_CRT_SECURE_NO_WARNINGS','/Isrc/RP9',
             'tools/nebula_control/check_asteroid_mesh.cpp','/Fo'+str(PROBE/'check.obj'),'/Fe'+str(exe),
             '/link','d3d9.lib','user32.lib','C:/DXSDK_Jun10/Lib/x86/d3dx9.lib']
    for name,cmd in [('build',command),('result',[str(exe),str(ROOT/'DATA_EXTRA/SHADERS')+'/',str(PROBE/'cache'),*arguments,str(OUT/'preview.png')])]:
        log=OUT/(name+'.log')
        with log.open('wb') as stream:
            result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode: print(log.read_text(errors='replace')[-5000:])
        result.check_returncode()
    assert before=={p:digest(ROOT/p) for p in sources}
    checks=dict(sources=before,assets=assets,models=models,passed=True,
                binary=digest(OUT/'build/bin/freelancer.exe'),game_launched=False,
                cache_files={p.name:digest(p) for p in (PROBE/'cache').iterdir() if re.fullmatch(r'[a-f0-9]{64}\.bin',p.name)})
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
    print((OUT/'result.log').read_text(errors='replace'))

if __name__=='__main__':main()
