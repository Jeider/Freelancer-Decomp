"""Reproduce layered-material fog fallback through actual RP9 code, then verify repair."""
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
from check_object_fog import compiler_env,digest

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage/material_lod'
BUILD=OUT/'build'
PROBE=OUT/'probe'

def main():
    expected='--expect-bug' in sys.argv
    compiler,env=compiler_env()
    sdk=Path('C:/Program Files (x86)/Windows Kits/10/Include')
    version=sorted(p for p in sdk.iterdir() if (p/'um/Windows.h').exists())[-1]
    env['INCLUDE']=';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper())+';'+str(version/'winrt')+';C:/DXSDK_Jun10/Include'
    env['PATH']=str(ROOT/'bin')+';D:/Games/FL_MOD/bin;'+env['PATH']
    env['FREELANCER_SHADER_CACHE_DIR']=str(PROBE/'cache')
    if expected:env['FOG_MATERIAL_EXPECT_BUG']='1'
    env['TEMP']=env['TMP']=str(PROBE)
    (PROBE/'bin').mkdir(parents=True,exist_ok=True)
    shaders=PROBE/'DATA_EXTRA/SHADERS';shaders.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'DATA_EXTRA/SHADERS/surface_material.hlsl',shaders/'surface_material.hlsl')
    source=(ROOT/'tools/nebula_control/check_object_fog.cpp').read_text()
    source=source[:source.index(' for(float keep:')]+ '\n#include "asteroid_material_lod_cases.inl"\n}\n'
    (PROBE/'route.cpp').write_text(source)
    objects=[str(BUILD/'obj/RP9'/(name+'.obj')) for name in ('RP9','RP9Ex','Mgsdb')]
    command=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/utf-8',
        '/DRP_DIRECT3D9','/DFREELANCER_DLSS5','/D_ITERATOR_DEBUG_LEVEL=1','/DASTEROID_SPAWN_CHECK',
        '/D_CRT_SECURE_NO_WARNINGS','/DNOMINMAX','/Isrc/RP9','/Isrc/include','/Itools/nebula_control',str(PROBE/'route.cpp'),
        '/Fo'+str(PROBE/'route.obj'),'/Fe'+str(PROBE/'bin/route.exe'),*objects,'/link','/LTCG','/LIBPATH:'+str(ROOT/'bin'),
        'd3d9.lib','user32.lib','gdi32.lib','dacom.lib','ddraw.lib','version.lib',
        'C:/DXSDK_Jun10/Lib/x86/d3dx9.lib','C:/DXSDK_Jun10/Lib/x86/DxErr.lib','legacy_stdio_definitions.lib']
    suffix='before' if expected else 'after'
    for name,cmd in [('build',command),(suffix,[str(PROBE/'bin/route.exe'),str(OUT/(suffix+'.png'))])]:
        with (OUT/(name+'.log')).open('wb') as log:
            result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        print((OUT/(name+'.log')).read_text(errors='replace')[-3000:],flush=True)
        result.check_returncode()
    report={'passed':True,'expect_bug':expected,'binary':digest(BUILD/'bin/RP9.dll'),
        'sources':{name:digest(ROOT/name) for name in ('src/RP9/RP9Ex.cpp','DATA_EXTRA/SHADERS/surface_material.hlsl',
            'tools/nebula_control/asteroid_material_lod_cases.inl','tools/nebula_control/check_asteroid_material_lod.py')},
        'game_launched':False}
    (OUT/(suffix+'.json')).write_text(json.dumps(report,indent=2))
    if '--all-checks' in sys.argv:
        # The common vertex payload changed: validate existing routes and every
        # affected production shader variant, including quality 0 and instancing.
        checks=[('regression','tools/nebula_control/check_object_fog.cpp',objects,
            ['dacom.lib','ddraw.lib','version.lib','C:/DXSDK_Jun10/Lib/x86/DxErr.lib','legacy_stdio_definitions.lib'],
            [str(OUT/'regression.png')]),
            ('manifest','tools/nebula_control/check_object_fog_manifest.cpp',[],[],
            [str(ROOT/'DATA_EXTRA/SHADERS')+'/',str(PROBE/'manifest_cache')])]
        for name,src,objs,libs,args in checks:
            exe=PROBE/'bin'/(name+'.exe')
            cmd=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/utf-8',
                '/DRP_DIRECT3D9','/DFREELANCER_DLSS5','/D_ITERATOR_DEBUG_LEVEL=1',
                '/D_CRT_SECURE_NO_WARNINGS','/DNOMINMAX','/Isrc/RP9','/Isrc/include',
                '/DSURFACE_SCATTER_CHECK','/DASTEROID_SPAWN_CHECK','/DASTEROID_FOG_COVERAGE_CHECK',src,
                '/Fo'+str(PROBE/(name+'.obj')),'/Fe'+str(exe),*objs,'/link','/LTCG','/LIBPATH:'+str(ROOT/'bin'),
                'd3d9.lib','user32.lib','gdi32.lib','C:/DXSDK_Jun10/Lib/x86/d3dx9.lib',*libs]
            for step,run in [('build',cmd),('result',[str(exe),*args])]:
                log=OUT/(name+'_'+step+'.log')
                with log.open('wb') as stream:
                    result=subprocess.run(run,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                print(log.read_text(errors='replace')[-1800:],flush=True)
                result.check_returncode()
        names=set(re.findall(r'^CACHE ([0-9a-f]{64}\.bin)$',(OUT/'manifest_result.log').read_text(),re.M))
        assert names
        report.update(regression=True,manifest=True,cache_files={n:digest(PROBE/'manifest_cache'/n) for n in sorted(names)})
        (OUT/'checks.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
