"""Read-only audit of this session's assets and Pythonlancer overwrite paths."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from sync_story_dev import split_dev,generator_static,semantic,SYSTEMS
from check_valensia_mega import templates
from bake_compound import placements_from_template

REPO=Path(__file__).resolve().parents[1]
GAME=Path('D:/Games/FL_MOD');PY=GAME/'Assets/Pythonlancer'
OUT=REPO/'out/pythonlancer_preservation'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check-baseline',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    baseline=OUT/'baseline.json'
    if args.check_baseline:
        expected=json.loads(baseline.read_text());changed=[]
        for name,digest in expected.items():
            path=GAME/name
            if not path.exists() or sha(path)!=digest:changed.append(name)
        print(json.dumps({'changed_protected_files':changed,'checked':len(expected)},indent=2));return
    manifests={};latest={}
    for task in ('valensia_mega','terraform_mega','potsdam_mega','potsdam_panels','ulster_megabase','ulster_shortbase','ulster_shortsplit','stuttgart_mega','forbes_mega'):
        path=REPO/'out'/task/'installed.json'
        data=json.loads(path.read_text());manifests[task]=len(data['hashes'])
        latest.update(data['hashes'])
    for path in sorted((REPO/'out/stations/station_batch').glob('*/installed.json'),key=lambda p:p.stat().st_mtime_ns):
        data=json.loads(path.read_text());manifests[path.parent.name]=len(data['hashes'])
        latest.update(data['hashes'])
    from optimized_station_paths import audit_paths
    latest=audit_paths(latest)
    # Later unrelated engine builds/config appends are legitimate. Check exact
    # hashes only for immutable geometry and current source templates in scope.
    geometry={n:h for n,h in latest.items() if n.endswith(('.cmp','.sur'))}
    model_mismatches=[n for n,h in geometry.items() if not (GAME/n).exists() or sha(GAME/n)!=h]
    dev={}
    protected=set(geometry)
    for name,folder in SYSTEMS.items():
        rel=f'DATA/UNIVERSE/SPECIAL/{folder}/{name}'
        live=(GAME/(rel+'.ini')).read_text(encoding='utf-8-sig')
        raw=(GAME/(rel+'_dev.ini')).read_bytes()
        prefix,tail=split_dev(raw)
        dev[name]={'roundtrip_matches_live':semantic(generator_static(raw))==semantic(live),'tail_bytes':len(tail)}
        protected.add(rel+'_dev.ini')
    template_names=('valensia.py','terraforming.py','potsdam.py','ulster_megabase.py','stuttgart_megabase.py','forbes_megafactory.py')
    template_names=sorted(set(template_names)|{Path(n).name for n in latest if n.startswith('Assets/Pythonlancer/templates/dockable/') and n.endswith('.py')})
    template_hashes={}
    for name in template_names:
        relative='Assets/Pythonlancer/templates/dockable/'+name
        template_hashes[name]=sha(GAME/relative)==latest[relative]
        protected.add(relative)
    potsdam_source=templates((PY/'templates/dockable/potsdam.py').read_text(encoding='utf-8-sig'))['Potsdam']
    potsdam_expected={x.name:x for x in placements_from_template(potsdam_source)}
    potsdam_live={x.name:x for x in placements_from_template((GAME/'DATA/UNIVERSE/SYSTEMS_MOD/RH_BERLIN/rh_ber.ini').read_text(encoding='utf-8-sig'))
        if x.name=='rh_ber_04' or x.name.startswith('rh_ber_04_')}
    potsdam_ok=set(potsdam_expected)==set(potsdam_live) and all(
        (row.archetype.lower(),row.rotate,row.loadout)==(potsdam_live[n].archetype.lower(),potsdam_live[n].rotate,potsdam_live[n].loadout)
        and all(abs(a+b-c)<.0001 for a,b,c in zip(row.pos,(38000,0,18000),potsdam_live[n].pos))
        for n,row in potsdam_expected.items())
    solar=(GAME/'DATA/SOLAR/solararch.ini').read_text(encoding='utf-8-sig')
    vienna=[]
    for block in re.split(r'(?m)(?=^\[Solar\])',solar):
        if not re.search(r'(?mi)^nickname\s*=\s*vienna_',block):continue
        model=re.search(r'(?mi)^DA_archetype\s*=\s*([^\r\n]+)',block)
        if model:
            name='DATA/'+model[1].strip().replace('\\','/')
            assert (GAME/name).exists(),name
            protected.add(name)
            surface=str(Path(name).with_suffix('.sur')).replace('\\','/')
            assert (GAME/surface).exists(),surface
            protected.add(surface);vienna.append(name)
    data_folder=(PY/'tools/data_folder.py').read_text(encoding='utf-8-sig')
    exclusion=(PY/'tools/nebula_exclusion.py').read_text(encoding='utf-8-sig')
    hook='prepare_exclusion_shells(content)' in data_folder and 'SHELL_MAX_ALPHA = 0.8' in exclusion
    volume=(GAME/'DATA_EXTRA/VOLUMETRIC/volumetric.ini').read_text(encoding='utf-8-sig')
    section=re.search(r'(?ims)^\[Nebula\]\s*\n(.*?)(?=^\[|\Z)',volume)[1]
    values={k:v.strip() for k,v in re.findall(r'(?m)^([a-z_]+)\s*=\s*([^\r\n;]+)',section)}
    expected={'render_in_exclusion':'1','exclusion_march_distance':'6000','exclusion_transition_fraction':'0.2',
        'exclusion_density_scale':'0.15','exclusion_core_haze':'0.04'}
    volume_ok=all(values.get(k)==v for k,v in expected.items())
    protected.update(['DATA/SOLAR/solararch.ini','DATA/SOLAR/loadouts.ini','DATA/EQUIPMENT/select_equip.ini',
        'Assets/Pythonlancer/tools/data_folder.py','Assets/Pythonlancer/tools/nebula_exclusion.py',
        'Assets/Pythonlancer/universe/systems/or_hq_static.py','DATA_EXTRA/VOLUMETRIC/volumetric.ini',
        'bin/Common.dll','bin/freelancer.exe',
        'DATA/SOLAR/NEBULA_MOD/m11_vienna_nebula.ini','DATA/SOLAR/NEBULA_MOD/m13_asf_hq_nebula.ini',
        'DATA/SOLAR/ASTEROIDS_MOD/asf_hq/m13_asf_right_field.ini'])
    for path in (GAME/'DATA_EXTRA/SHADERS').glob('nebula*'):
        if path.is_file():protected.add(path.relative_to(GAME).as_posix())
    # All output filenames of DataFolder methods, recorded for review.
    output_literals=sorted(set(re.findall(r"['\"]([^'\"\n]*\.(?:ini|cmp|sur|dll|hlsl))['\"]",data_folder)))
    static_config_writers={n: n in output_literals for n in ('solararch.ini','loadouts.ini','select_equip.ini')}
    checks={'optimized_models_checked':len(geometry),'model_mismatches':model_mismatches,
        'vienna_models_present':len(vienna),'templates_match_installed':template_hashes,'story_dev':dev,'potsdam_template_matches_live':potsdam_ok,
        'exclusion_generation_hook':hook,'global_exclusion_settings':volume_ok,'static_configs_generated_by_DataFolder':static_config_writers}
    check_paths=set(protected)
    check_paths.update(n for n in latest if n.startswith('DATA/UNIVERSE/') and n.endswith('.ini') and 'Original' not in n)
    check_paths.update(f'DATA/UNIVERSE/SPECIAL/{folder}/{name}.ini' for name,folder in SYSTEMS.items())
    check_paths.add('DATA/UNIVERSE/SYSTEMS_MOD/RH_BERLIN/rh_ber.ini')
    check_paths.add('DATA/UNIVERSE/SYSTEMS_MOD/BR_WARWICK/br_wrw.ini')
    check_paths.add('DATA/UNIVERSE/SYSTEMS_MOD/TAU4/tau4.ini')
    check_paths.add('DATA/UNIVERSE/SYSTEMS_MOD/RH_STUTTGART/rh_stut.ini')
    check_paths.add('DATA/UNIVERSE/SYSTEMS_MOD/LI_FORBES/li_for.ini')
    overlays={}
    for build in (GAME/'BUILDS').iterdir():
        if not build.is_dir():continue
        differences=[];matches=[]
        for name in sorted(check_paths):
            target=build/name
            if not target.is_file():continue
            (matches if sha(target)==sha(GAME/name) else differences).append(name)
        markers={}
        for filename,marker in [('DATA/UNIVERSE/SPECIAL/ORDER_HQ/or_hq.ini',b'archetype = tfm_or_hq_body'),
            ('DATA/UNIVERSE/SPECIAL/RH_VIENNA/rh_vien.ini',b'archetype = vienna_core_1'),
            ('DATA/UNIVERSE/SYSTEMS_MOD/RH_BERLIN/rh_ber.ini',b'archetype = pdm_top_rotating')]:
            file=build/filename
            markers[filename]=file.exists() and marker in file.read_bytes()
        overlays[build.name]={'would_overwrite_differently':differences,'matches':matches,'has_latest_station_marker':markers}
    snapshot={n:sha(GAME/n) for n in sorted(protected)}
    if not baseline.exists():baseline.write_text(json.dumps(snapshot,indent=2))
    report=dict(checks=checks,build_overlays=overlays,protected_files=len(snapshot),datafolder_output_literals=output_literals)
    (OUT/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(checks,indent=2))
    print('BUILD OVERLAYS',json.dumps({n:x['would_overwrite_differently'] for n,x in overlays.items()},indent=2))
    print('Read-only audit; protected baseline entries:',len(snapshot))
    assert not model_mismatches and all(template_hashes.values()) and all(d['roundtrip_matches_live'] for d in dev.values()) and hook and volume_ok and potsdam_ok


if __name__=='__main__':main()
