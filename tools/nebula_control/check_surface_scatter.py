"""Model-only fog, distant meshes and authored exclusions; no game launch."""
import json
import os
from pathlib import Path
import check_asteroid_mesh as mesh
import check_object_fog as surface

OUT=mesh.ROOT/'out/graphics_settings/nebula_asteroid_mesh/surface_scatter'
GAME=Path('D:/Games/FL_MOD')

def sections(path):
    result=[]
    for raw in path.read_text(encoding='utf-8-sig').splitlines():
        line=raw.split(';',1)[0].strip()
        if line.startswith('['):result.append((line.strip('[]').lower(),[]))
        elif '=' in line and result:
            key,value=line.split('=',1);result[-1][1].append((key.strip().lower(),value.strip()))
    return result

def main():
    mesh.OUT=OUT;mesh.PROBE=OUT/'probe';mesh.PROBE.mkdir(parents=True,exist_ok=True)
    mesh.EXTRA_DEFINES=['/DASTEROID_OVERLAY_ORDER_CHECK','/DASTEROID_SURFACE_SCATTER_CHECK']
    mesh.EXTRA_SOURCES=['src/freelancer/Client/cli_asteroid.cpp','src/freelancer/Client/cli_asteroid.h',
        'src/freelancer/Client/far_rocks.h','src/freelancer/Client/space_scene_obj_draw.cpp',
        'src/freelancer/Client/nebula_fog_shape.h','src/RP9/RP9Ex.cpp','src/RP9/RP9Ex.h',
        'DATA_EXTRA/SHADERS/surface_material.hlsl',
        *['tools/nebula_control/'+name for name in ('check_surface_scatter.py','check_asteroid_mesh.py',
        'check_asteroid_mesh.cpp','asteroid_draw_order_cases.inl','asteroid_surface_scatter_cases.inl',
        'asteroid_exclusion_cases.inl','check_object_fog.py','check_object_fog.cpp','check_object_fog_manifest.cpp',
        'install_surface_scatter.py','install_asteroid_fog.py')]]
    field=GAME/'DATA/SOLAR/ASTEROIDS_MOD/GENERATED/om15_ast1_asteroids.ini'
    system=GAME/'DATA/UNIVERSE/SYSTEMS_MOD/OMEGA15/om15.ini'
    guarded=[field,system,GAME/'DATA_EXTRA/VOLUMETRIC/volumetric.ini',
             GAME/'Assets/Pythonlancer/universe/content/asteroid_definition.py']
    guarded+=sorted((GAME/'DATA/SOLAR/NEBULA_MOD/GENERATED').glob('gen_om15_*_nebula.ini'))
    for name in ('nebula_volume.hlsl','nebula_volume.hlsli','nebula_composite.hlsl'):
        guarded += [root/'DATA_EXTRA/SHADERS'/name for root in (mesh.ROOT,GAME)]
    guards={str(p):mesh.digest(p) for p in guarded}
    zones={dict(values)['nickname'].lower():dict(values) for name,values in sections(system) if name=='zone'}
    selected=[]
    for name,values in sections(field):
        if name!='exclusion zones':continue
        current=None
        for key,value in values:
            if key=='exclusion':current=value.lower()
            if key=='exclude_dynamic_asteroids' and int(value):selected.append(zones[current])
    assert len(selected)==8 and all(z['shape']=='SPHERE' for z in selected)
    fixture=mesh.PROBE/'exclusions.txt'
    fixture.write_text('\n'.join(z['pos'].replace(',',' ')+' '+z['size'] for z in selected))
    os.environ['FREELANCER_ASTEROID_EXCLUSION_FIXTURE']=str(fixture)
    mesh.main()
    surface.OUT=OUT/'surfaces';surface.BUILD=OUT/'build';surface.PROBE=surface.OUT/'probe'
    surface.EXTRA_DEFINES=['/DSURFACE_SCATTER_CHECK']
    surface.main()
    assert guards=={str(p):mesh.digest(p) for p in guarded}
    report_path=OUT/'checks.json';report=json.loads(report_path.read_text())
    route=json.loads((surface.OUT/'checks.json').read_text())
    report.update(guards={**guards,**report['assets']},
        shader_changes=['far_rocks.hlsl','surface_material.hlsl'],profile_changes=False,
        scope='Omega-15 medium/high opaque surface scatter; local meshes to 6 km, complete exclusions',
        surface_checks=mesh.digest(surface.OUT/'checks.json'),
        limitations='Offline real-asset and RP9 route tests; complete in-game scene remains user visual review')
    report_path.write_text(json.dumps(report,indent=2))
    print('PASS model-only scatter, native material routing, shader variants, exclusion geometry and immutable nebula guards')

if __name__=='__main__':main()
