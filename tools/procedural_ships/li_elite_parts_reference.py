"""Show original LI pirate elite component boundaries and native wing motion."""
import json
import shutil
import numpy as np
from PIL import Image
from li_elite_concept_audit import a, active_ships, read_ship
from bw_family_audit import bounds, frame, sheet, write_json
from rh_redesign_paths import TOPIC

OUT=TOPIC/'li_elite/structure_review'
COLORS={
    'body':(.60,.63,.67), 'glass':(.18,.31,.42), 'mount':(.35,.39,.44),
    'spoiler':(.77,.37,.64), 'engine1':(.26,.48,.83), 'engine2':(.23,.72,.67),
    'leaf1':(.89,.64,.25), 'leaf2':(.47,.73,.36), 'leaf3':(.43,.69,.88),
    'baydoor':(.82,.42,.39)}


def category(name):
    if 'glass' in name: return 'glass'
    if 'spoiler' in name: return 'spoiler'
    if 'engine01' in name: return 'engine1'
    if 'engine02' in name: return 'engine2'
    if 'baydoor' in name: return 'baydoor'
    for i in range(1,4):
        if f'wing{i}_' in name: return f'leaf{i}'
    return 'mount' if 'wing' in name else 'body'


def main():
    assert shutil.disk_usage(TOPIC).free > 256*1024**2
    OUT.mkdir(parents=True,exist_ok=True)
    src,path,rest,mats,stats,record,names,flight=read_ship('li_elite_pir',active_ships()['li_elite_pir'])
    previous=json.loads((TOPIC/'li_elite/source_audit.json').read_text(encoding='utf8'))
    assert previous['source_sha256']==stats['sha256']
    catids={k:i+1 for i,k in enumerate(COLORS)}
    # The shared preview renderer uses a default grey for untextured materials.
    # A constant white display swatch lets Dc carry the component colors.
    swatch=Image.new('RGB',(2,2),(255,255,255))
    display={catids[k]:dict(name=k,image=swatch,texture='',kind='DcDt',colour=np.array(v))
             for k,v in COLORS.items()}
    def tint(scene):
        return [dict(g,material=catids[category(names[g['part']])]) for g in scene]
    center,radius=frame(flight)
    cameras=[((-1,.42,-.32),'SIDE THREE-QUARTER'),((1,.65,1.1),'REAR THREE-QUARTER'),
             ((-1,0,0),'SIDE'),((0,1,.000001),'TOP')]
    def render(scene,cam,size=600,origin=center,extent=radius):
        return a.source.render(tint(scene),display,origin,extent,cam,size,'texture')
    panels=[(label,render(flight,cam)) for cam,label in cameras]
    sheet(OUT/'native_components.jpg',[panels[:2],panels[2:]],2,
          'LI PIR ELITE / ACTUAL COMPONENTS',
          'Pink: spoiler. Blue/teal: separate engines. Amber/green/light-blue: moving leaves. Red: baydoors.',size=600)
    duration=max(c['duration'] for c in record['channels'] if c['script']==a.SCRIPT)
    times=[0,duration/2,duration]
    poses=[a.motion.scene_at(record,rest,t,a.SCRIPT) for t in times]
    rows=[[(label,render(p,cam,500)) for label,p in zip(['FLIGHT','HALF FOLDED','STOWED'],poses)]
          for cam in [cameras[0][0],cameras[3][0]]]
    sheet(OUT/'native_colored_motion.jpg',rows,3,'LI PIR ELITE / THREE MOVING LEAVES PER SIDE',
          'Native script forward: folding. Colors follow the same mesh parts through all three phases.',size=500)
    aft=[g for g in flight if category(names[g['part']]) in ['spoiler','engine1','engine2']]
    ac,ar=frame(aft)
    sheet(OUT/'native_aft_components.jpg', [[('REAR 3/4',render(flight,(1,.55,1.2),550,ac,ar*1.25)),
          ('SIDE',render(flight,(-1,0,0),550,ac,ar*1.25))]],2,
          'LI PIR ELITE / SPOILER AND ENGINES',
          'These are separate fixed components. Their color does not imply a new animation.',size=550)
    objects=[]
    for name in sorted(set(names.values())):
        groups=[g for g in flight if names[g['part']]==name]
        if not groups: continue
        joint=next((c for c in record['constructs'] if c['name'].lower()==name),None)
        channels=[c for c in record['channels'] if c['script']==a.SCRIPT and c['child'].lower()==name]
        objects.append(dict(object=name,color_group=category(name),triangles=sum(len(g['corners']) for g in groups),
            bounds=bounds(groups),construct=joint,wing_channels=channels))
    assert a.sha(path)==stats['sha256']
    write_json(OUT/'manifest.json',dict(source_model=path.as_posix(),source_sha256=stats['sha256'],
        geometry_unchanged=True,colors=COLORS,objects=objects,motion_times=times,
        images=[dict(path=p.as_posix(),sha256=a.sha(p)) for p in sorted(OUT.glob('*.jpg'))],
        script='tools/procedural_ships/li_elite_parts_reference.py',
        limitations='Neutral display colors only; original poses. No new design collision or animation validation.'))
    print(json.dumps(dict(source_unchanged=True,objects=len(objects),motion_times=times)))


if __name__=='__main__':
    main()
