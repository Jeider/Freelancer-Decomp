"""Q13: matching fore/aft cornices and calm single-chart hood skin."""
from pathlib import Path
import collections
import json
import shutil
import subprocess
import sys
import numpy as np
import rh_freighter_uv14 as prev
import rh_freighter_uv13 as fore
import rh_freighter_uv12 as exporter
import rh_freighter_uv11 as stern
import rh_freighter_uv10 as hull

aft,base,old,package=prev.aft,prev.base,prev.old,prev.package
uv,rig,f,q=prev.uv,prev.rig,prev.f,prev.q
PREVIOUS=prev.OUT
OUT=PREVIOUS.parent/'uv_15'
REFERENCE=prev.REFERENCE
TOP=prev.TOP
TOP_GROUP=None
MIRROR_Z=None


def dump(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')


def guard():
    assert shutil.disk_usage(q.ROOT).free>2*1024**3
    for folder in (PREVIOUS,OUT):
        for name,report in [('rh_pir_freighter.cmp','build.json'),('rh_pir_freighter_review_open.cmp','review_open_check.json')]:
            if folder==OUT and not (folder/name).exists():continue
            assert f.digest(folder/name)==json.loads((folder/report).read_text())['cmp_sha256'],(folder,name,'manual edits')


def mirror(groups,role_offset=0):
    result=[]
    for g in groups:
        t=np.array(g['corners'],float).copy()[:,::-1,:]
        t[:,:,2]=2*MIRROR_Z-t[:,:,2];t[:,:,5]*=-1
        result.append(dict(material=g['material']+role_offset,corners=t))
    return result


def prepare():
    global TOP_GROUP,MIRROR_Z
    guard();OUT.mkdir(parents=True,exist_ok=True)
    refs=json.loads((REFERENCE/'native_fore.json').read_text());ref=refs[1]
    q.SOURCE=REFERENCE.parent/'native_source/rh_pir_freighter_original.cmp'
    assert f.digest(q.SOURCE)==ref['model_sha256'] and f.digest(q.MAT)==ref['material_sha256']
    cfg=json.loads((PREVIOUS/'fore_cornice_geometry.json').read_text())
    shape=cfg['native_platform']
    # Match each platform's back edge to the existing hood at exactly Y=2.80.
    aft_meet=5.72+(3.81-TOP)/((3.81-2.48)/(7.72-5.72))
    MIRROR_Z=(aft_meet+shape['top_z'][1])/2
    ts=np.array([t['corners'] for t in ref['triangles'] if t['material']=='pir_r_panel01_256' and t['source_triangle'] in (93,94)])
    z0=ts[:,:,2].min();ts[:,:,0]-=shape['source_center_x'];ts[:,:,1]=TOP
    ts[:,:,2]+=shape['top_z'][0]-z0;ts[:,:,3:6]=[0,1,0]
    TOP_GROUP=dict(material=uv.P,corners=ts)
    data=json.loads((PREVIOUS/'mechanical_geometry.json').read_text())
    platform,_=fore.native_platform(refs[0])
    for ob in (fore.cornice_base(),platform):
        ob['name']=ob['name'].replace('Fore long cornice','Aft mirrored cornice')
        ob['groups']=mirror(ob['groups'],10)
        data['objects'].append(ob)
    data['uv15_changes']=dict(source_cmp_sha256=f.digest(PREVIOUS/'rh_pir_freighter.cmp'),mirror_plane_z=MIRROR_Z,
        aft_cornice='mirrored unchanged front base and platform',hood_uv='one native pale chart')
    dump('mechanical_geometry.json',data)
    for name in ('engine_geometry_check.json','aft_rib_geometry.json','vent_clearance.json','raised_hold_geometry.json',
                 'stern_transition_geometry.json','pale_stern_union.json','cornice_union.json','fore_cornice_union.json'):
        shutil.copyfile(PREVIOUS/name,OUT/name)
    ribs=json.loads((OUT/'aft_rib_geometry.json').read_text())['ribs']
    aft.RIBS.update({int(s):{k:np.array(v) if k in ('oi','oo','bi','bo','arc') else v for k,v in r.items()} for s,r in ribs.items()})
    cfg['hood_uv_recipe']=dict(material='pir_r_panel01_256',charts=1,tiling=False,uv_box=[.5059,.2627,.998,.855])
    dump('fore_cornice_geometry.json',cfg)
    rear=json.loads((PREVIOUS/'cornice_geometry.json').read_text())
    rear.update(profile_zy=None,symmetric_with_front=True,mirror_plane_z=MIRROR_Z,width=cfg['width'],
        top_z=[2*MIRROR_Z-z for z in reversed(shape['top_z'])],fascia_z=2*MIRROR_Z-cfg['fascia_z'],fascia_y=cfg['fascia_y'],
        native_platform=shape,previous_top_z=rear['top_z'],previous_width=rear['width'],
        lower_return_zy=[[2*MIRROR_Z-z,y] for z,y in cfg['lower_return_zy']],
        preserved_lower_inset=True)
    dump('cornice_geometry.json',rear)
    dump('cornice_symmetry.json',dict(plane_z=MIRROR_Z,front=shape,aft_top_z=rear['top_z'],
        top_y=TOP,base_width=cfg['width'],construction='same two solids mirrored, no scaling',
        attachment='each shelf back edge meets its own existing hood at Y=2.80'))
    refsdir=REFERENCE.parent/'cornices_15';refsdir.mkdir(exist_ok=True)
    sources=[]
    for i,key in enumerate(('lb9eE8','ZUHA10'),1):
        source=Path(f'C:/Users/Freel/AppData/Local/Temp/codex-clipboard-{key}.png');target=refsdir/f'{i}_{key}.png'
        if not target.exists() and source.exists():shutil.copyfile(source,target)
        if target.exists():sources.append(dict(file=target.name,sha256=f.digest(target),original=str(source)))
    (refsdir/'sources.json').write_text(json.dumps(sources,indent=2),encoding='utf8')


def area(groups):
    t=np.concatenate([g['corners'] for g in groups])[:,:,:3]
    return np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1).sum()/2


def cornice_map(groups,back=False):
    if back:groups=mirror(groups,-10)
    tops=[g for g in groups if g['material']==70]
    assert abs(area(tops)-area([TOP_GROUP]))<3e-5,'Shelf top must remain the full mirrored outline'
    others=[g for g in groups if g['material'] not in (70,77)]
    mapped=fore.new_map(others)+[dict(material=TOP_GROUP['material'],corners=TOP_GROUP['corners'].copy())]
    pale=collections.defaultdict(list)
    for g in groups:
        if g['material']!=77:continue
        for t in np.array(g['corners']):
            base.fixed_box(t,t[:,[0,2]],[-2.35,-7.62],[2.35,-4.1],(.5059,.2627,.998,.855),uv.P,pale)
    mapped+=package.pack(pale)
    return mirror(mapped) if back else mapped


def core_map(name,groups):
    front=[g for g in groups if 70<=g['material']<=79]
    back=[g for g in groups if 80<=g['material']<=89]
    remaining=[g for g in groups if 60<=g['material']<=67]
    assert not any(g['material'] in (60,61,62) for g in remaining),'Old upper cornice should be fully buried'
    rest=[];pale=collections.defaultdict(list)
    for g in groups:
        if 60<=g['material']<=89:continue
        kept=[]
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t)
            if g['material']!=51 and p[:,2].min()>=5.71999 and p[:,2].max()<=8.30001 and n[1]>.4:
                base.fixed_box(t,np.column_stack((-p[:,0],-p[:,2])),[-2.35,-8.30],[2.35,-5.72],(.5059,.2627,.998,.855),uv.P,pale)
            else:kept.append(t)
        if kept:rest.append(dict(material=g['material'],corners=np.array(kept)))
    return hull.core_map(name,rest)+stern.map_new(remaining)+cornice_map(front)+cornice_map(back,True)+package.pack(pale)


def main():
    prepare()
    subprocess.run([sys.executable,str(q.ROOT/'tools/blender_workspace.py'),'--topic','ship_design','--script',
        str(q.ROOT/'tools/procedural_ships/rh_freighter_uv10_union.py'),'--','--variant','uv_15',
        '--prefix','Aft mirrored cornice','--expected-count','2','--report','mirrored_cornice_union.json','--conform-seams','--manifold-solver'],check=True,cwd=q.ROOT)
    exporter.export_model(OUT,PREVIOUS,core_map)


if __name__=='__main__':main()
