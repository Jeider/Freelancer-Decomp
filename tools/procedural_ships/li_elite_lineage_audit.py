"""Compare current LI/Order elite variants for the pirate concept direction.

Read-only game access; source geometry references only, no exports or installs.
"""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

import pirate_art_audit as a
from bw_family_audit import bounds, frame, sheet, write_json
from li_elite_concept_audit import active_ships, CAMS
from rh_redesign_paths import TOPIC

OUT = TOPIC/'li_elite/comparison'
CASES = [('li_pir_elite','li_elite_pir','li_pir_elite_48355e14'),
         ('li_elite','li_elite','li_elite_3d93b41a'),
         ('or_elite','or_elite','or_elite_8fee9923'),
         ('li_elite2','li_elite2','li_elite2_d33774ab')]


def valid(c):
    return (c['native_size_valid'] and c['bound_joint'] and c['finite']
            and c['monotonic_times'] and not c.get('parent_mismatch'))


def point_set(scene):
    return np.unique(np.round(np.concatenate([g['corners'][...,:3].reshape(-1,3)
                                             for g in scene]),5), axis=0)


def geometry_key(scene):
    tris = []
    for g in scene:
        for tri in g['corners'][...,:3]:
            tris.append(tuple(sorted(tuple(np.round(v,5)) for v in tri)))
    return hashlib.sha256(np.array(sorted(tris),dtype='<f8').tobytes()).hexdigest()


def main():
    free = shutil.disk_usage(TOPIC).free
    assert free > 512*1024**2
    OUT.mkdir(parents=True,exist_ok=True)
    active = active_ships()
    loaded, reports, glass_sets = [], {}, {}
    for key,alias,old_key in CASES:
        folder = OUT/key; folder.mkdir(exist_ok=True)
        values = active[alias]
        src = dict(model=values['da_archetype'][0].replace('\\','/').lower(),
                   materials=[v.replace('\\','/').lower() for v in values['material_library']])
        path = a.source.DATA/src['model']
        rest,mats,stats = a.source.load(src)
        rest = [dict(g,part=g['part'].lower()) for g in rest]
        old = json.loads((TOPIC/'analysis/full_models/models'/(old_key+'.json')).read_text(encoding='utf8'))
        assert old['sha256']==stats['sha256'], 'Changed installed source: '+key
        _,nodes = a.source.mesh.read_tree(path.read_bytes())
        flat = {p.lower():n.blob for p,n in a.source.mesh.walk(nodes)}
        cons = a.full.constructs(flat); channels = a.full.channels(flat,cons)
        names = {a.source.mesh.string(b).lower():a.source.mesh.string(
            flat[p.rsplit('/',1)[0]+'/object name']).lower()
            for p,b in flat.items() if '/cmpnd/' in p and p.endswith('/file name')}
        wing = [c for c in channels if c['script']==a.SCRIPT]
        assert wing and all(valid(c) for c in wing)
        launch_channels = [c for c in channels if c['script']=='sc_launch extend']
        assert launch_channels and all(valid(c) for c in launch_channels)
        record = dict(path=src['model'],constructs=cons,channels=channels)
        duration = max(c['duration'] for c in wing)
        times = np.linspace(0,duration,5).tolist()
        poses = [a.motion.scene_at(record,rest,t,a.SCRIPT) for t in times]
        flight = poses[0]
        center,radius = frame(flight)
        def render(pose,cam,mode='texture',origin=center,extent=radius):
            return a.source.render(pose,mats,origin,extent,cam,550,mode)
        sheet(folder/'native_flight.jpg', [[(CAMS[j][1],render(flight,CAMS[j][0],mode='clay' if j==5 else 'texture'))
              for j in range(i*2,i*2+2)] for i in range(3)],2,key+' / ACTUAL FLIGHT',
              'Current installed geometry; shared scale within sheet; not a game screenshot.')
        sheet(folder/'native_wing_motion.jpg', [[(f'{label} t={times[i]:.2f}',render(poses[i],cam))
              for i,label in [(0,'FLIGHT'),(2,'FOLDING'),(4,'STOWED')]]
              for cam in [CAMS[0][0],CAMS[2][0]]],3,key+' / NATIVE WING MECHANISM',
              'Forward script playback folds; reverse extends. Same frame and camera.')
        launch_duration = max(c['duration'] for c in launch_channels)
        launch = a.motion.scene_at(record,rest,launch_duration,'sc_launch extend')
        launch_delta = max(float(np.abs(g['corners']-h['corners']).max()) for g,h in zip(flight,launch))
        direct = a.source.load(src,pose=(a.SCRIPT,0))[0]
        direct_delta = max(float(np.abs(g['corners']-h['corners']).max()) for g,h in zip(flight,direct))
        assert direct_delta < 2e-6
        glass = [g for g in flight if 'glass' in mats[g['material']]['name'].lower()]
        glass_sets[key] = point_set(glass)
        cc,cr = frame(glass)
        sheet(folder/'cockpit_reference.jpg', [[(label,render(flight,cam,origin=cc,extent=cr*1.5))
              for cam,label in [CAMS[0],CAMS[3],CAMS[2]]]],3,key+' / SOURCE CABIN',
              'Compare geometry; only li_pir_elite cabin is the fixed redesign module.')
        door_script = values.get('bay_door_anim',[None])[0]
        door_info = dict(archetype_script=door_script,channels=[],has_cargo_animation=False)
        if door_script:
            door_script=door_script.lower()
            doors=[c for c in channels if c['script']==door_script]
            assert doors and all(valid(c) for c in doors)
            end=max(c['duration'] for c in doors)
            held=[dict(c,script=door_script,times=[0,end],values=[c['first'],c['first']]) for c in wing]
            dr=dict(record,channels=doors+held)
            dp=[a.motion.scene_at(dr,rest,t,door_script) for t in [0,end]]
            dn={c['child'].lower() for c in doors}
            dc,rr=frame([g for p in dp for g in p if names[g['part']] in dn])
            sheet(folder/'native_baydoor_motion.jpg', [[(label,render(p,(-.65,1.4,-.7),origin=dc,extent=max(rr*1.6,3.3)))
                  for label,p in zip(['CLOSED','OPEN'],dp)]],2,key+' / BAYDOOR',
                  'Wings held in flight; native cargo animation only.')
            door_info.update(channels=doors,has_cargo_animation=True)
        parts=[]
        for obj in sorted(set(names.values())):
            sub=[g for g in flight if names[g['part']]==obj]
            if not sub: continue
            parts.append(dict(object=obj,triangles=sum(len(g['corners']) for g in sub),
                              geometry_sha256_rounded_1e5=geometry_key(sub),flight_bounds=bounds(sub)))
        assets=[path]+[a.source.DATA/v for v in src['materials']]+[a.source.DATA/values['cockpit'][0]]
        report=dict(alias=alias,source_model=path.as_posix(),source_sha256=stats['sha256'],
            archetype=values,source_stats=stats,constructs=cons,channels=channels,parts=parts,
            assets=[dict(path=p.as_posix(),sha256=a.sha(p)) for p in assets],
            wing_times=times,phase_bounds=[bounds(p) for p in poses],wing_channels=wing,
            baydoor=door_info,glazing_bounds=bounds(glass),glazing_triangles=sum(len(g['corners']) for g in glass),
            native_channel_findings=[c for c in channels if not valid(c)],
            launch_to_flight_max_delta=launch_delta,independent_pose_loader_max_delta=direct_delta,
            checked_pose_tolerance=2e-6,source_unchanged=a.sha(path)==stats['sha256'],
            complete_lod0_triangles=old['lods'],
            caveats=['Installed mod, not authenticated retail.',
                     'Reference renderer reads VMeshRef geometry; direct placeholder VMeshPart is not displayed.',
                     'Native float32 rotations are not exactly orthonormal; tolerance is explicit.',
                     'No collision, back-face or in-game glass validation.'])
        assert report['source_unchanged']
        write_json(folder/'source_audit.json',report)
        reports[key]=report
        loaded.append((key,flight,mats,center,radius))
        print(key,'size',report['phase_bounds'][0]['dimensions'],'launch delta',launch_delta,flush=True)
    common=max(row[4] for row in loaded)
    for style,filename in [('texture','family_textured.jpg'),('clay','family_shape.jpg')]:
        rows=[[(key+' / '+label,a.source.render(scene,mats,center,common,cam,550,style))
               for key,scene,mats,center,_ in loaded]
              for cam,label in [CAMS[0],CAMS[3],CAMS[4],CAMS[2]]]
        sheet(OUT/filename,rows,4,'LI ELITE / ORDER / ELITE2 / SAME UNIT SCALE',
              'Actual flight state. Differences in height and silhouette are not normalized away.')
    # Quantify glass similarity independently of its material names and export salt.
    base=glass_sets['li_pir_elite']; base_center=(base.min(0)+base.max(0))/2
    comparison=[]
    for key,points in glass_sets.items():
        delta=(points.min(0)+points.max(0))/2-base_center
        centered=points-delta
        distances=np.linalg.norm(centered[:,None,:]-base[None,:,:],axis=2)
        max_nearest=max(float(distances.min(1).max()),float(distances.min(0).max()))
        comparison.append(dict(model=key,source_glass_center_shift=delta.tolist(),
            max_nearest_after_translation=max_nearest,geometry_congruent_at_2e5=max_nearest<2e-5,
            note='Glass surface only. Does not approve replacing the target cockpit shell.'))
    pir_parts={p['object']:p for p in reports['li_pir_elite']['parts']}
    regular_parts={p['object']:p for p in reports['li_elite']['parts']}
    identical={key:(pir_parts[key]['geometry_sha256_rounded_1e5']==regular_parts[key]['geometry_sha256_rounded_1e5'])
               for key in sorted(pir_parts.keys() & regular_parts.keys())}
    write_json(OUT/'comparison.json',dict(glass=comparison,li_elite_vs_pirate_geometry=identical,
               common_view_radius=common,free_bytes_before=free))
    refs=[dict(path=p.as_posix(),sha256=a.sha(p)) for p in sorted(OUT.rglob('*.jpg'))]
    write_json(OUT/'manifest.json',dict(models=[dict(model=k,path=r['source_model'],sha256=r['source_sha256'])
               for k,r in reports.items()],references=refs,script='tools/procedural_ships/li_elite_lineage_audit.py'))
    print(json.dumps(dict(all_sources_unchanged=True,models=len(reports),glass=comparison)))


if __name__=='__main__':
    main()
