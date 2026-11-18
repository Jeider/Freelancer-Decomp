"""Check the scoped profile, real quality gate and production GPU volume without the game."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_object_fog/full_volume'
PROBE=OUT/'probe'
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/nebula_control')]
import exclusion_volume_all as reference
from build_asf_hq import compiler_env
from prepare_omega15 import GAME,STAGE,CONFIG,digest

def run(name,command,env):
    log=OUT/(name+'.log')
    with log.open('wb') as stream:r=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    if r.returncode:print(log.read_text(errors='replace')[-5000:])
    r.check_returncode()

def main():
    for folder in ('inputs','textures','cache'): (PROBE/folder).mkdir(parents=True,exist_ok=True)
    config=reference.sections(reference.read(STAGE/CONFIG))
    common={**reference.defaults(),**next(d for n,d in config if n=='nebula')}
    styles={d['name']:d for n,d in config if n=='nebulastyle'}
    overrides={d['file'].lower():d for n,d in config if n=='nebulaoverride'}
    selected=[k for k,v in overrides.items() if v.get('style')=='om15_full_volume']
    assert sorted(selected)==['gen_om15_neb1_nebula','gen_om15_neb2_nebula','gen_om15_neb3_nebula','gen_om15_story_neb1_nebula']
    settings=styles['om15_full_volume'];assert settings['minimum_quality']=='2'
    assert all(settings[k]=='1' for k in ('replace_object_fog','replace_fog_overlay','replace_clouds'))
    assert settings['hybrid_clouds']=='0'
    reference.OUT=PROBE
    system=reference.sections(reference.read(GAME/'DATA/UNIVERSE/SYSTEMS_MOD/OMEGA15/om15.ini'))
    star=next(d['star'] for n,d in system if n=='object' and 'star' in d)
    stars={d['nickname'].lower():d for n,d in reference.sections(reference.read(GAME/'DATA/SOLAR/stararch.ini')) if 'nickname' in d}
    case={'id':'omega15','basename':'gen_om15_neb1_nebula','text':reference.read(GAME/'DATA/SOLAR/NEBULA_MOD/GENERATED/gen_om15_neb1_nebula.ini'),'context':{'volumetric':True,'star':star}}
    reference.constants(case,common,styles,overrides,stars);assert case['status']=='ready' and not case['notes'],case
    source=(ROOT/'src/freelancer/Client/nebula_volume.cpp').read_text(encoding='utf-8-sig')
    noise=source[source.index('    unsigned int Hash(unsigned int X)'):source.index('    // Coverage (the fraction')]
    (PROBE/'nebula_noise_fixture.h').write_text('const unsigned long kNoiseSize=64;\nfloat Clamp(float x,float a,float b){return std::max(a,std::min(b,x));}\n'+noise)
    # Compile and execute the actual production quality function with real policy,
    # substituting only Common's saved-settings lookup.
    struct=source[source.index('    struct FNebulaVolumeSettings'):source.index('    struct FNebulaOverride')]
    struct=struct[:struct.index('    };')+6]
    function=source[source.index('    void ApplyUserQuality('):source.index('    FNebulaVolumeSettings SettingsFor(')]
    quality='''#define COMMON_EXPORTS
#include "graphics_policy.h"
#include <cstdio>
#include <cstdlib>
int values[GraphicsSettings::Count]={};
namespace GraphicsSettings { int Get(int setting,bool configured){return values[setting];} }
float PortGraphicsRenderValue(char const*key,float authored){return GraphicsSettings::RenderValue(values,key,authored);}
'''+struct+function+'''
int main(){for(int q=0;q<4;++q){values[GraphicsSettings::Nebulae]=q;
 FNebulaVolumeSettings s={};s.Enabled=1;s.MinimumQuality=2;s.ResolutionScale=.5f;s.StepCount=96;s.ShadowSteps=4;ApplyUserQuality(s);
 if((s.Enabled>.5f)!=(q>=2) || s.StepCount!=(q==1?32.f:q==2?64.f:96.f))return 3;
 printf("PASS quality %d: volume %.0f, steps %.0f; retail fallback %d\\n",q,s.Enabled,s.StepCount,s.Enabled<=.5f);
 s.MinimumQuality=0;s.Enabled=1;ApplyUserQuality(s);if((s.Enabled>.5f)!=(q>0))return 4;
 }puts("PASS other profiles retain their existing quality policy");}
'''
    (PROBE/'quality.cpp').write_text(quality)
    compiler,env=compiler_env();env['INCLUDE']=';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper())+';C:/DXSDK_Jun10/Include'
    env['PATH']=str(ROOT/'bin')+';'+str(GAME/'bin')+';'+env['PATH'];env['TEMP']=env['TMP']=str(PROBE)
    for name,file,libs in [('quality',str(PROBE/'quality.cpp'),[]),('volume','tools/nebula_control/check_omega15_volume.cpp',['d3d9.lib','user32.lib','C:/DXSDK_Jun10/Lib/x86/d3dx9.lib'])]:
        command=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/utf-8','/DNOMINMAX','/D_CRT_SECURE_NO_WARNINGS','/Isrc/RP9','/Isrc/include','/I'+str(PROBE),file,'/Fo'+str(PROBE/(name+'.obj')),'/Fe'+str(PROBE/(name+'.exe')),'/link',*libs]
        run(name+'_build',command,env)
    run('quality',[str(PROBE/'quality.exe')],env)
    for q in (2,3):
        run('volume_'+str(q),[str(PROBE/'volume.exe'),str(PROBE/'inputs/omega15.bin'),str(ROOT/'DATA_EXTRA/SHADERS')+'/',str(PROBE/'cache'),str(OUT/('depth_'+str(q)+'.png')),str(q)],env)
        print((OUT/('volume_'+str(q)+'.log')).read_text())
    inputs=['src/freelancer/Client/nebula_volume.cpp','src/freelancer/Client/nebula_fog_shape.h','src/include/graphics_policy.h','tools/nebula_control/omega15_volume.ini','DATA_EXTRA/SHADERS/nebula_volume.hlsl','DATA_EXTRA/SHADERS/nebula_volume.hlsli','DATA_EXTRA/SHADERS/nebula_composite.hlsl']
    report={'passed':True,'sources':{p:digest(ROOT/p) for p in inputs},'staged_profile':digest(STAGE/CONFIG),'case':case,'binary':digest(ROOT/'out/graphics_settings/nebula_asteroid_mesh/build/bin/freelancer.exe'),'game_launched':False,'preview':'synthetic depth-step fixture, not an in-game screenshot',
            'cache_files':{p.name:digest(p) for p in (PROBE/'cache').glob('*.bin')}}
    (OUT/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print((OUT/'quality.log').read_text())

if __name__=='__main__':main()
