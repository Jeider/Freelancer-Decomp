"""Check current Omega-15 assets and procedural proxy rendering in a standalone GPU harness."""
import json
from pathlib import Path
import check_asteroid_mesh as mesh
OUT=mesh.ROOT/'out/graphics_settings/nebula_asteroid_mesh/handoff'
GAME=Path('D:/Games/FL_MOD')

def sections(path):
    result=[]
    for raw in path.read_text(encoding='cp1251').splitlines():
        line=raw.split(';',1)[0].strip()
        if line.startswith('['):result.append((line.strip('[]').lower(),[]))
        elif '=' in line and result:
            key,value=line.split('=',1);result[-1][1].append((key.strip().lower(),value.strip()))
    return result

def main():
    field=GAME/'DATA/SOLAR/ASTEROIDS_MOD/GENERATED/om15_ast1_asteroids.ini'
    raw=sections(field)
    dyn=[dict(v)['asteroid'] for n,v in raw if n=='dynamicasteroids']
    server=[dict(v)['asteroid'] for n,v in raw if n=='serverdynamicasteroids']
    arches=lambda path:{dict(v)['nickname']:dict(v) for n,v in sections(path) if 'nickname' in dict(v)}
    ds=arches(GAME/'DATA/SOLAR/dasteroidarch.ini');ss=arches(GAME/'DATA/SOLAR/solararch.ini')
    assert len(dyn)==len(server)==3
    models=[]
    for decor,physical in zip(dyn,server):
        assert ds[decor]['da_archetype'].lower()==ss[physical]['da_archetype'].lower()
        models.append({'decoration':decor,'physical':physical,'geometry':ds[decor]['da_archetype']})
    exclusions=[v for n,v in raw if n=='exclusion zones'];assert len(exclusions)==1
    flags=[int(value) for key,value in exclusions[0] if key in ('exclude_dynamic_asteroids','exclude_billboards')]
    assert len(flags)==16 and all(flags)
    mesh.OUT=OUT;mesh.PROBE=OUT/'gpu_probe';mesh.KEEP_ORIGIN=True
    mesh.EXTRA_DEFINES=['/DASTEROID_HANDOFF_CHECK']
    if '--decor-only' in __import__('sys').argv:mesh.EXTRA_DEFINES+=['/DASTEROID_DECOR_ONLY_CHECK']
    mesh.EXTRA_SOURCES=['src/include/procedural_asteroids.h','src/include/procedural_asteroid_replica.h',
        'src/freelancer/Client/procedural_asteroid_client.cpp','src/freelancer/Client/procedural_asteroid_client.h',
        'src/freelancer/Client/client_gameobj.cpp','src/freelancer/Client/space_scene_obj_draw.cpp',
        'tools/nebula_control/asteroid_handoff_gpu_cases.inl','tools/nebula_control/check_asteroid_handoff_gpu.py']
    if '--performance' in __import__('sys').argv:
        mesh.EXTRA_SOURCES+=['src/freelancer/Client/procedural_asteroid_mesh.inl','src/RP9/RP9Ex.cpp',
                            'src/RP9/RP9.h','src/include/render/IRenderPipelineEx.h']
    mesh.main()
    path=OUT/'checks.json';report=json.loads(path.read_text());report['matching_models']=models
    report['exclusions']=8;report['cpu']=json.loads((OUT/'cpu_checks.json').read_text())
    report['sources'].update(report['cpu']['sources'])
    if '--performance' in __import__('sys').argv:
        report['client']=json.loads((OUT/'client_checks.json').read_text());report['sources'].update(report['client']['sources'])
    for name in ('src/Server/server_chat.cpp','src/Server/IServerImpl.cpp','src/freelancer/Client/client_iclient.cpp',
                 'src/freelancer/Client/star_sys.cpp','src/freelancer/freelancer.vcxproj'):
        report['sources'][name]=mesh.digest(mesh.ROOT/name)
    names=['Server.dll','Server.pdb','freelancer.exe','freelancer.pdb']
    if '--performance' in __import__('sys').argv:names+=['RP9.dll','RP9.pdb']
    report['binaries']={name:mesh.digest(OUT/'build/bin'/name) for name in names}
    path.write_text(json.dumps(report,indent=2))

if __name__=='__main__':
    if '--performance' in __import__('sys').argv:OUT=OUT/'performance'
    if '--decor-only' in __import__('sys').argv:OUT=OUT/'decor_only'
    main()
