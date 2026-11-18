"""Read-only RH pirate fighter geometry/mechanism references for concept art."""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

import pirate_art_audit as a
from rh_redesign_paths import TOPIC

OUT = TOPIC / 'rh_fighter'
REFS = OUT / 'references'


def bounds(scene):
    p = np.concatenate([g['corners'][..., :3].reshape(-1, 3) for g in scene])
    lo, hi = p.min(0), p.max(0)
    return dict(min=lo.tolist(), max=hi.tolist(), dimensions=(hi-lo).tolist())


def main():
    assert shutil.disk_usage(OUT.anchor).free > 1024**3
    REFS.mkdir(parents=True, exist_ok=True)
    source = json.loads((TOPIC / 'pirate_art/ships/rh_fighter_pir/source.json').read_text())
    path = a.source.DATA / source['model']
    assert a.sha(path) == source['sha256']
    scene, mats, stats = a.source.load(source)
    scene = [dict(g, part=g['part'].lower()) for g in scene]
    _, nodes = a.source.mesh.read_tree(path.read_bytes())
    flat = {p.lower(): n.blob for p, n in a.source.mesh.walk(nodes)}
    constructs = a.full.constructs(flat)
    channels = a.full.channels(flat, constructs)
    assert all(c['native_size_valid'] and c['bound_joint'] and not c.get('parent_mismatch') for c in channels)
    record = dict(path=source['model'], constructs=constructs, channels=channels)
    phases = [a.motion.scene_at(record, scene, t, a.SCRIPT) for t in (0, .5, 1, 1.5, 2)]
    launch = a.motion.scene_at(record, scene, 7, 'sc_launch extend')
    delta = max(float(np.abs(x['corners'][..., :3]-y['corners'][..., :3]).max()) for x,y in zip(phases[0],launch))
    assert delta < 1e-6
    flight = phases[0]
    b = bounds(flight); center=(np.array(b['min'])+b['max'])/2
    points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in flight])
    radius=float(np.linalg.norm(points-center,axis=1).max())
    sheet=Image.new('RGB',(1600,1180),a.BG);d=ImageDraw.Draw(sheet)
    d.text((15,12),'ACTUAL RH PIR FIGHTER / FLIGHT / native geometry, cabin and single rear engine',font=a.FONT,fill='white')
    for cam,box,label in [((1,.55,-1.25),(0,75,940,1120),'PERSPECTIVE'),((1,0,0),(950,75,1600,460),'SIDE'),((0,1,.00001),(950,470,1600,1120),'TOP')]:
        im=a.source.render(flight,mats,center,radius,cam,1000,'texture')
        ar=np.asarray(im);ys,xs=np.where(np.any(ar!=np.array(a.BG),axis=2))
        im=im.crop((max(0,int(xs.min())-20),max(0,int(ys.min())-20),min(1000,int(xs.max())+21),min(1000,int(ys.max())+21)))
        x0,y0,x1,y1=box;im=ImageOps.contain(im,(x1-x0-20,y1-y0-35))
        sheet.paste(im,(x0+(x1-x0-im.width)//2,y0+30+(y1-y0-30-im.height)//2))
        d.text((x0+15,y0),label,font=a.FONT,fill='white')
    d.text((15,1140),'Native dimensions XYZ: '+', '.join(f'{v:.3f}' for v in b['dimensions'])+' / views fitted separately / no in-game capture',font=a.SMALL,fill='white')
    sheet.save(REFS/'native_flight.jpg',quality=96)
    sheet=Image.new('RGB',(1800,1270),a.BG);d=ImageDraw.Draw(sheet)
    for row,cam in enumerate(((0,0,-1),(0,1,.00001))):
        for col,i in enumerate((0,2,4)):
            sheet.paste(a.source.render(phases[i],mats,center,radius,cam,600,'texture'),(col*600,40+row*600))
            d.text((col*600+12,12+row*600),['FLIGHT / t=0','FOLDING / t=1','STOWED / t=2'][col],font=a.FONT,fill='white')
    d.text((12,1245),'Front + top: diagonal inner slide and outer 63-degree roll. Native hierarchy, no geometry edits.',font=a.SMALL,fill='white')
    sheet.save(REFS/'native_wing_motion.jpg',quality=96)
    wing=[c for c in channels if c['script']==a.SCRIPT]
    door=next(c for c in channels if c['script']=='sc_open baydoor')
    door_record=dict(record,channels=[door]+[dict(c,script=door['script'],times=[0,door['duration']],values=[c['first'],c['first']]) for c in wing])
    door_poses=[a.motion.scene_at(door_record,scene,t,door['script']) for t in (0,door['duration'])]
    sheet=Image.new('RGB',(1400,750),a.BG);d=ImageDraw.Draw(sheet)
    for i,pose in enumerate(door_poses):
        sheet.paste(a.source.render(pose,mats,np.array([0.,.5,-1.5]),6.0,(.7,1.1,-.7),700,'texture'),(i*700,35))
        d.text((i*700+15,10),['CARGO DOOR CLOSED','CARGO DOOR OPEN / slides aft'][i],font=a.FONT,fill='white')
    d.text((15,728),'The large aft circular housing is FIXED. Cargo door uses a separate nearly longitudinal Pris slide.',font=a.SMALL,fill='white')
    sheet.save(REFS/'native_baydoor_motion.jpg',quality=96)
    parts=[]
    for name in sorted({g['part'] for g in scene}):
        parts.append(dict(name=name,flight=bounds([g for g in flight if g['part']==name]),stowed=bounds([g for g in phases[-1] if g['part']==name])))
    assets=[path]+[a.source.DATA/x['path'] for x in source['material_sources']+source['cockpit_sources']]+[Path('H:/FL/EXP/EXTRA_ART/RH/r_fighter01.JPG')]
    report=dict(source=source,source_path=path.as_posix(),assets=[dict(path=p.as_posix(),sha256=a.sha(p)) for p in assets],
                constructs=constructs,channels=channels,source_triangles=stats['triangles'],phase_bounds=[bounds(s) for s in phases],
                launch_to_flight_max_delta=delta,parts=parts,
                runtime_basis='wing_anim.h: wing t=0 flight, forward to t=2 stowed; common_cship.cpp: bay open forward, close reverse',
                binding_note='Part names lowercased locally for case-insensitive Cmpnd binding.',
                limitations='Offline reconstruction, not runtime capture or collision-clearance proof.')
    (OUT/'source_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(dict(source_sha=source['sha256'],dimensions=[x['dimensions'] for x in report['phase_bounds']],launch_delta=delta,refs=str(REFS)),indent=2))


if __name__=='__main__':main()
