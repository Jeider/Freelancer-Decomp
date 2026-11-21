"""Native physical-rock material on real RP9, using the three installed om15 meshes."""
from pathlib import Path
import json, shutil, struct, subprocess
import check_asteroid_mesh as mesh
from check_object_fog import compiler_env, digest
ROOT=mesh.ROOT
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/handoff/native_material'
BUILD=OUT/'build';PROBE=OUT/'gpu_probe'

def main():
    compiler,env=compiler_env()
    sdk=Path('C:/Program Files (x86)/Windows Kits/10/Include')
    version=sorted(p for p in sdk.iterdir() if (p/'um/Windows.h').exists())[-1]
    env['INCLUDE']=';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper())+';'+str(version/'winrt')+';C:/DXSDK_Jun10/Include'
    env['PATH']=str(ROOT/'bin')+';D:/Games/FL_MOD/bin;'+env['PATH']
    env['FREELANCER_SHADER_CACHE_DIR']=str(PROBE/'cache');env['TEMP']=env['TMP']=str(PROBE)
    (PROBE/'bin').mkdir(parents=True,exist_ok=True)
    shaders=PROBE/'DATA_EXTRA/SHADERS';shaders.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'DATA_EXTRA/SHADERS/surface_material.hlsl',shaders/'surface_material.hlsl')
    shutil.copy2(Path('D:/Games/FL_MOD/bin/port.ini'),PROBE/'bin/port.ini')
    assets={};mat=mesh.DATA/'SOLAR/ASTEROIDS_MOD/om15/ast_om15.mat'
    assets[str(mat)]=digest(mat);library=mesh.leaves(mat.read_bytes())[1]
    textures={mesh.crc(n.split('/')[-2]):b.rstrip(b'\0').decode('ascii') for n,_,b in library if n.lower().endswith('/dt_name')}
    for letter in 'abc':
        path=mesh.DATA/f'SOLAR/ASTEROIDS_MOD/om15/ast_o15_nrml_{letter}.3db';assets[str(path)]=digest(path)
        nodes=mesh.leaves(path.read_bytes())[1];blob=next(b for n,_,b in nodes if n.lower().endswith('/vmeshdata'))
        _,descriptors,groups=mesh.triangles(blob);assert len(groups)==1
        name=textures[descriptors[0][0]]
        texture=next(b for n,_,b in library+nodes if n.lower().endswith('/'+name.lower()+'/mips') or n.lower().endswith('/'+name.lower()+'/mip0'))
        (PROBE/(letter+'.bin')).write_bytes(struct.pack('<I',len(groups[0]))+b''.join(groups[0]))
        (PROBE/(letter+'.texture')).write_bytes(texture)
    source=(ROOT/'tools/nebula_control/check_object_fog.cpp').read_text()
    source='#include <fstream>\n#include <string>\n#define MESH_DIR "'+PROBE.as_posix()+'/"\n'+source[:source.index(' for(float keep:')]+ '\n#include "asteroid_native_material_cases.inl"\n}\n'
    (PROBE/'route.cpp').write_text(source)
    objects=[str(BUILD/'obj/RP9'/(n+'.obj')) for n in ('RP9','RP9Ex','Mgsdb')]
    cmd=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/utf-8',
        '/DRP_DIRECT3D9','/DFREELANCER_DLSS5','/D_ITERATOR_DEBUG_LEVEL=1','/DASTEROID_SPAWN_CHECK',
        '/D_CRT_SECURE_NO_WARNINGS','/DNOMINMAX','/Isrc/RP9','/Isrc/include','/Itools/nebula_control',str(PROBE/'route.cpp'),
        '/Fo'+str(PROBE/'route.obj'),'/Fe'+str(PROBE/'bin/route.exe'),*objects,'/link','/LTCG','/LIBPATH:'+str(ROOT/'bin'),
        'd3d9.lib','user32.lib','gdi32.lib','dacom.lib','ddraw.lib','version.lib',
        'C:/DXSDK_Jun10/Lib/x86/d3dx9.lib','C:/DXSDK_Jun10/Lib/x86/DxErr.lib','legacy_stdio_definitions.lib']
    for name,run in [('build_gpu',cmd),('result_gpu',[str(PROBE/'bin/route.exe'),str(OUT/'native_material.png')])]:
        with (OUT/(name+'.log')).open('wb') as log:
            result=subprocess.run(run,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        print((OUT/(name+'.log')).read_text(errors='replace')[-4500:],flush=True);result.check_returncode()
    sources=['src/RP9/RP9Ex.cpp','src/RP9/RP9RockNormals.inl','src/include/render/IRPRockNormals.h',
        'DATA_EXTRA/SHADERS/surface_material.hlsl','DATA_EXTRA/SHADERS/asteroid_simple.hlsl',
        'src/freelancer/Client/far_rocks.cpp','src/freelancer/Client/asteroid_lod_data.h',
        'src/freelancer/Client/asteroid_lod_policy.h','src/freelancer/Client/asteroid_lod_batches.inl',
        'tools/nebula_control/check_object_fog.cpp','tools/nebula_control/asteroid_native_material_cases.inl',
        'tools/nebula_control/check_asteroid_native_material.py']
    report={'passed':True,'game_launched':False,'assets':assets,'sources':{n:digest(ROOT/n) for n in sources},
        'binaries':{n:digest(BUILD/'bin'/n) for n in ('RP9.dll','RP9.pdb','freelancer.exe','freelancer.pdb')}}
    (OUT/'gpu_checks.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
