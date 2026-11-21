"""Check solar coverage and existing distance simplification without launching the game."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
from check_object_fog import compiler_env, digest
import check_physical_asteroid_fog as queue

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage/solar_scope'
BUILD=OUT/'build'
PROBE=OUT/'probe'
SOURCES=('src/RP9/RP9Ex.cpp','src/RP9/RP9Ex.h','src/RP9/RP9SurfaceFade.h',
 'src/RP9/RP9ShaderManifest.h','src/freelancer/Client/space_scene_obj_draw.cpp',
 'src/freelancer/Client/nebula_fog_shape.h','src/include/render/IRPLocalShadows.h',
 'DATA_EXTRA/SHADERS/surface_material.hlsl','DATA_EXTRA/SHADERS/far_rocks.hlsl',
 'tools/nebula_control/check_solar_fog.py','tools/nebula_control/solar_fog_cases.inl')

def main():
    PROBE.mkdir(parents=True,exist_ok=True)
    compiler,env=compiler_env()
    sdk=Path('C:/Program Files (x86)/Windows Kits/10/Include')
    version=sorted(p for p in sdk.iterdir() if (p/'um/Windows.h').exists())[-1]
    env['INCLUDE']=';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper())+';'+str(version/'winrt')+';C:/DXSDK_Jun10/Include'
    env['PATH']=str(ROOT/'bin')+';D:/Games/FL_MOD/bin;'+env['PATH']
    env['FREELANCER_SHADER_CACHE_DIR']=str(PROBE/'cache')
    env['TEMP']=env['TMP']=str(PROBE)
    (PROBE/'bin').mkdir(exist_ok=True)
    shaders=PROBE/'DATA_EXTRA/SHADERS';shaders.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'DATA_EXTRA/SHADERS/surface_material.hlsl',shaders/'surface_material.hlsl')
    # Reuse only previously verified, unchanged bytecode in the isolated cache.
    prior=json.loads((OUT.parent/'material_lod/checks.json').read_text())
    live=Path(os.environ['LOCALAPPDATA'])/'Freelancer-Decomp/RP9/ShaderCache'
    for folder in (PROBE/'cache',PROBE/'manifest_cache'):
        folder.mkdir(exist_ok=True)
        for name,h in prior['cache_files'].items():
            p=live/name
            if p.exists() and digest(p)==h:shutil.copy2(p,folder/name)
    def run(name,cmd):
        log=OUT/(name+'.log')
        with log.open('wb') as stream:
            result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        print(name+': '+log.read_text(errors='replace')[-1500:],flush=True)
        result.check_returncode()
    sys.path.insert(0,str(ROOT/'tools/physics'))
    from check_gravity import function
    policy='src/freelancer/Client/nebula_fog_shape.h'
    stub=queue.STUB.replace('unsigned DrawStateA=','unsigned get_id(){return 0;} unsigned DrawStateA=')
    stub=stub.replace('unsigned NebulaFogShapeScope(){return trial?512:0;}',r'''
unsigned activeSystem=15;int quality=3;
unsigned CreateID(char const* name){return !strcmp(name,"om15")?15:!strcmp(name,"om7")?7:!strcmp(name,"rh_stut")?20:99;}
unsigned StarSysGetActiveSystemId(){return activeSystem;}
namespace GraphicsSettings {enum {Nebulae};int Get(int){return quality;}}
int PortConfigInt(char const*,char const* key,int value){return !strcmp(key,"nebula_object_fog_shape_test")?1:value;}
bool IsPlayerShipId(unsigned){return false;}bool G_SimplifyNebulaObjects=true;
''')
    # Preserve the existing queue stub's controllable trial flag.
    scope=function(policy,'inline unsigned NebulaFogShapeScope(').replace('return Enabled &&','return trial && Enabled &&')
    code=stub+scope+function(policy,'inline bool NebulaFogSolarHull(')
    target='src/freelancer/Client/space_scene_obj_draw.cpp'
    for signature in ('void GameobjUpdateDrawLighting(','void EnqueueObject(','bool NativeNebulaObject('):code+=function(target,signature)
    code+=r'''
int main(){
 for(unsigned system:{15u,7u,20u,99u})for(int q=0;q<=3;++q){activeSystem=system;quality=q;assert((NebulaFogShapeScope()!=0)==(q>=2&&system!=99));}
 activeSystem=15;quality=3;FClientSolarGameobj solar;FSpaceCamera camera;
 for(unsigned type:{0x10u,0x20u,0x40u,0x80u,0x100u,0x400u,0x1000u,0x2000u,0x4000u,0x8000u,0x20000000u,SERVER_ASTEROID_TYPE}){
  solar.type=solar.solar.TypeBits=type;assert(NebulaFogSolarHull(2,type));bucket=-1;
  EnqueueObject(&solar,&camera);assert(bucket==1);GameobjUpdateDrawLighting(&solar,&camera);assert(lastFogEnd==2500);
 }
 for(unsigned type:{1u,2u,4u,8u,0x200u,0x800u})assert(!NebulaFogSolarHull(2,type));
 assert(!NebulaFogSolarHull(1,0x100));
 solar.type=solar.solar.TypeBits=0x100;trial=false;bucket=-1;EnqueueObject(&solar,&camera);assert(bucket==0);
 GameobjUpdateDrawLighting(&solar,&camera);assert(lastFogEnd==20000);trial=true;
 G_FieldEnclosure=0;bucket=-1;EnqueueObject(&solar,&camera);assert(bucket==0);G_FieldEnclosure=1;
 solar.pos={4035,0,0};assert(!NativeNebulaObject(&solar,&camera));solar.pos.x=4036;assert(NativeNebulaObject(&solar,&camera));
 G_SimplifyNebulaObjects=false;assert(!NativeNebulaObject(&solar,&camera));
 puts("PASS system/quality gates, solar hull types, camera fog, queue cover order, unchanged 4000 m hull-distance simplification");
}
'''
    cpu=PROBE/'policy.cpp';cpu.write_text('#include <initializer_list>\n'+code)
    run('policy_build',[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/DFREELANCER_RP9','/Isrc/Include',str(cpu),'/Fo'+str(PROBE/'policy.obj'),'/Fe'+str(PROBE/'bin/policy.exe')])
    run('policy_result',[str(PROBE/'bin/policy.exe')])
    if '--cpu-only' in sys.argv:return
    prefix=(ROOT/'tools/nebula_control/check_object_fog.cpp').read_text().split(' for(float keep:')[0]
    (PROBE/'solar.cpp').write_text(prefix+'\n#include "solar_fog_cases.inl"\n}\n')
    layered=(ROOT/'tools/nebula_control/asteroid_material_lod_cases.inl').read_text()
    layered=layered.replace('e->RockClass=RPRockAsteroid;e->SurfaceShader=RPSurfaceRock;','e->RockClass=0;e->SurfaceShader=RPSurfaceAuto;')
    layered=layered.replace('draw(512,','draw(2560,').replace('draw(768,','draw(2816,')
    (PROBE/'layered.cpp').write_text(prefix+layered+'\n}\n')
    objects=[str(BUILD/'obj/RP9'/(name+'.obj')) for name in ('RP9','RP9Ex','Mgsdb')]
    for name,src,linked,args in (
        ('solar',str(PROBE/'solar.cpp'),True,[str(OUT/'preview.png')]),
        ('layered',str(PROBE/'layered.cpp'),True,[str(OUT/'layered.png')]),
        ('regression','tools/nebula_control/check_object_fog.cpp',True,[str(OUT/'regression.png')]),
        ('manifest','tools/nebula_control/check_object_fog_manifest.cpp',False,[str(ROOT/'DATA_EXTRA/SHADERS')+'/',str(PROBE/'manifest_cache')])):
        exe=PROBE/'bin'/(name+'.exe')
        cmd=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/utf-8',
            '/DRP_DIRECT3D9','/DFREELANCER_DLSS5','/D_ITERATOR_DEBUG_LEVEL=1','/D_CRT_SECURE_NO_WARNINGS','/DNOMINMAX',
            '/Isrc/RP9','/Isrc/include','/Itools/nebula_control','/DSURFACE_SCATTER_CHECK','/DASTEROID_SPAWN_CHECK','/DASTEROID_FOG_COVERAGE_CHECK',
            src,'/Fo'+str(PROBE/(name+'.obj')),'/Fe'+str(exe),*(objects if linked else []),'/link','/LTCG','/LIBPATH:'+str(ROOT/'bin'),
            'd3d9.lib','user32.lib','gdi32.lib','C:/DXSDK_Jun10/Lib/x86/d3dx9.lib']
        if linked:cmd+=['dacom.lib','ddraw.lib','version.lib','C:/DXSDK_Jun10/Lib/x86/DxErr.lib','legacy_stdio_definitions.lib']
        run(name+'_build',cmd);run(name+'_result',[str(exe),*args])
    names=set(re.findall(r'^CACHE ([0-9a-f]{64}\.bin)$',(OUT/'manifest_result.log').read_text(),re.M));assert names
    report={'passed':True,'policy':True,'solar':True,'layered':True,'regression':True,'manifest':True,
        'sources':{n:digest(ROOT/n) for n in SOURCES},
        'binaries':{n:digest(BUILD/'bin'/n) for n in ('RP9.dll','RP9.pdb','freelancer.exe','freelancer.pdb')},
        'cache_files':{n:digest(PROBE/'manifest_cache'/n) for n in sorted(names)},'game_launched':False}
    (OUT/'checks.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
