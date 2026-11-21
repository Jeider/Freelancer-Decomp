"""Physical asteroid submission, RP9 fade pixels/depth, and new startup variants."""
import json
import os
from pathlib import Path
import subprocess
import sys
import check_object_fog as probe

ROOT=probe.ROOT;OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/spawn_fade'
GAME=Path('D:/Games/FL_MOD')

def submit_check():
    sys.path.insert(0,str(ROOT/'tools/physics'))
    from check_asteroid_visuals import STUB
    from check_gravity import function
    test=r'''
int main(){
 FClientEquippedObj rock,ordinary;
 auto draw=[](FClientEquippedObj& go){unsigned lod=0;EquippedObjSubmitDrawRetail(&go,&lod,nullptr,0,nullptr,nullptr);assert(lod==9);};
 draw(ordinary);assert(sets==0&&overrides==0&&ServerAsteroidFade::SurfaceScope(&ordinary)==0);
 ServerAsteroidFade::Begin(&rock);draw(rock);
 assert(sets==0&&overrides==0&&lastExtra==nullptr&&rock.object.CloakPercent==0);
 assert(ServerAsteroidFade::SurfaceScope(&rock)==1024);
 ServerAsteroidFade::Tick(&rock,.375f);draw(rock);
 assert(ServerAsteroidFade::Opacity(&rock)==.5f&&sets==0&&overrides==0);
 assert(ServerAsteroidFade::SurfaceScope(&rock)==(1024u|(127u<<16)));
 ServerAsteroidFade::Begin(&rock);assert(ServerAsteroidFade::Opacity(&rock)==.5f);
 ServerAsteroidFade::Tick(&rock,-1);ServerAsteroidFade::Tick(&rock,std::numeric_limits<float>::quiet_NaN());
 assert(ServerAsteroidFade::Opacity(&rock)==.5f);
 rock.object.CloakPercent=.5f;draw(rock);
 assert(lastOpacity==.5f&&overrides==1&&lastExtra==(void*)3&&rock.object.CloakPercent==.5f);
 rock.object.CloakPercent=0;draw(rock);assert(removes==1&&lastExtra==nullptr);
 ServerAsteroidFade::Tick(&rock,1);draw(rock);
 assert(ServerAsteroidFade::SurfaceScope(&rock)==0&&sets==1&&overrides==1&&removes==1);
 ServerAsteroidFade::Forget(&rock);assert(ServerAsteroidFade::Ages().empty());
 ServerAsteroidFade::Begin(&rock);assert(ServerAsteroidFade::SurfaceScope(&rock)==1024);ServerAsteroidFade::Forget(&rock);
 ordinary.object.CloakPercent=.25f;draw(ordinary);assert(lastOpacity==.75f&&overrides==2);
 puts("PASS production spawn submission: original material throughout; independent genuine cloak, stable lifetime and scope endpoint");
}
'''
    folder=OUT/'probe';folder.mkdir(parents=True,exist_ok=True)
    source=folder/'submit.cpp';source.write_text(STUB+function('src/freelancer/Client/space_scene_obj_draw.cpp','unsigned* EquippedObjSubmitDrawRetail(')+test)
    compiler,env=probe.compiler_env()
    command=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/DFREELANCER_RP9',
        '/Isrc/freelancer/Client',str(source),'/Fo'+str(folder/'submit.obj'),'/Fe'+str(folder/'submit.exe')]
    with (OUT/'submit.log').open('w') as log:
        subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run([str(folder/'submit.exe')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    print('PASS production submission/lifetime')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sources=['src/freelancer/Client/server_asteroid_fade.h','src/freelancer/Client/space_scene_obj_draw.cpp',
        'src/RP9/RP9Ex.cpp','src/RP9/RP9Ex.h','src/RP9/RP9SurfaceFade.h','src/RP9/RP9ShaderManifest.h',
        'src/Include/render/IRPLocalShadows.h',
        *['tools/nebula_control/'+name for name in ('check_asteroid_spawn.py','asteroid_spawn_cases.inl',
        'check_object_fog.py','check_object_fog.cpp','check_object_fog_manifest.cpp',
        'install_asteroid_spawn.py','install_surface_scatter.py','install_asteroid_fog.py')]]
    before={name:probe.digest(ROOT/name) for name in sources}
    guarded=[GAME/'DATA_EXTRA/VOLUMETRIC/volumetric.ini',
        GAME/'DATA/SOLAR/ASTEROIDS_MOD/GENERATED/om15_ast1_asteroids.ini',
        GAME/'DATA/UNIVERSE/SYSTEMS_MOD/OMEGA15/om15.ini']
    for root in (ROOT,GAME):
        for name in ('surface_material.hlsl','far_rocks.hlsl','nebula_volume.hlsl','nebula_volume.hlsli','nebula_composite.hlsl'):
            guarded.append(root/'DATA_EXTRA/SHADERS'/name)
    guarded+=sorted((GAME/'DATA/SOLAR/NEBULA_MOD/GENERATED').glob('gen_om15_*_nebula.ini'))
    guards={str(p):probe.digest(p) for p in guarded}
    submit_check()
    probe.OUT=OUT/'surfaces';probe.BUILD=OUT/'build';probe.PROBE=probe.OUT/'probe'
    probe.EXTRA_DEFINES=['/DSURFACE_SCATTER_CHECK','/DASTEROID_SPAWN_CHECK']
    probe.main()
    assert before=={name:probe.digest(ROOT/name) for name in sources}
    assert guards=={str(p):probe.digest(p) for p in guarded}
    report=json.loads((probe.OUT/'checks.json').read_text())
    (OUT/'checks.json').write_text(json.dumps(dict(sources={**before,**report['sources']},guards=guards,
        binary=probe.digest(OUT/'build/bin/freelancer.exe'),binaries=report['binaries'],
        passed=True,shader_changes=[],profile_changes=False,cache_files={},
        surface_checks=probe.digest(probe.OUT/'checks.json'),game_launched=False,
        scope='Physical asteroid spawn coverage preserves material/light/fog/depth; existing shader and cloud files unchanged'),indent=2))
    print('PASS spawn GPU readback, all 32 coverage startup variants and immutable shaders/clouds/population')

if __name__=='__main__':main()
