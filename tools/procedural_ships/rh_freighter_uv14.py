"""Q13: one native UV panel on the fore shelf instead of small repeating tiles."""
from pathlib import Path
import json
import shutil
import numpy as np
import rh_freighter_uv13 as prev

aft,base,old,package=prev.aft,prev.base,prev.old,prev.package
uv,rig,f,q=prev.uv,prev.rig,prev.f,prev.q
WIDTH,TOP=prev.WIDTH,prev.TOP
PREVIOUS=prev.OUT
OUT=PREVIOUS.parent/'uv_14'
REFERENCE=prev.REFERENCE
TOP_GROUP=None


def guard():
    assert shutil.disk_usage(q.ROOT).free>2*1024**3
    for folder in (PREVIOUS,OUT):
        for name,report in [('rh_pir_freighter.cmp','build.json'),('rh_pir_freighter_review_open.cmp','review_open_check.json')]:
            if folder==OUT and not (folder/name).exists():continue
            assert f.digest(folder/name)==json.loads((folder/report).read_text())['cmp_sha256'],(folder,name,'manual edits')


def prepare():
    global TOP_GROUP
    guard();OUT.mkdir(parents=True,exist_ok=True)
    for name in ('mechanical_geometry.json','engine_geometry_check.json','aft_rib_geometry.json','vent_clearance.json',
                 'raised_hold_geometry.json','stern_transition_geometry.json','pale_stern_union.json',
                 'cornice_geometry.json','cornice_union.json','fore_cornice_geometry.json','fore_cornice_union.json'):
        shutil.copyfile(PREVIOUS/name,OUT/name)
    cfg=json.loads((OUT/'fore_cornice_geometry.json').read_text())
    ref=json.loads((REFERENCE/'native_fore.json').read_text())[1]
    # The user may install a prototype at the former source path. Pin the
    # authenticated original instead; never change or restore installed assets.
    pinned=REFERENCE.parent/'native_source/rh_pir_freighter_original.cmp'
    if not pinned.exists():
        choices=[Path(ref['model']),Path(ref['model']).with_name('rh_pir_freighter1.cmp')]
        source=next((p for p in choices if p.exists() and f.digest(p)==ref['model_sha256']),None)
        assert source is not None,'Original reference missing; do not use an installed prototype as the source'
        pinned.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,pinned)
    assert f.digest(pinned)==ref['model_sha256']
    q.SOURCE=pinned
    assert f.digest(Path(ref['material']))==ref['material_sha256']
    ts=np.array([t['corners'] for t in ref['triangles'] if t['material']=='pir_r_panel01_256' and t['source_triangle'] in (93,94)])
    assert ts.shape==(2,3,8)
    source_z=float(ts[:,:,2].min());shape=cfg['native_platform']
    ts[:,:,0]-=shape['source_center_x']
    ts[:,:,1]=TOP
    ts[:,:,2]+=shape['top_z'][0]-source_z
    ts[:,:,3:6]=[0,1,0]
    # Same planar outline; recover the original two triangles solely to keep
    # the native diagonal and continuous UV interpolation, without tile splits.
    TOP_GROUP=dict(material=uv.P,corners=ts)
    cfg['top_uv_recipe']=dict(source=str(pinned),historical_source=ref['model'],source_sha256=ref['model_sha256'],
        source_triangles=[93,94],material='pir_r_panel01_256',charts=1,tiling=False,
        uv_min=ts[:,:,6:8].min((0,1)).tolist(),uv_max=ts[:,:,6:8].max((0,1)).tolist())
    (OUT/'fore_cornice_geometry.json').write_text(json.dumps(cfg,indent=2),encoding='utf8')
    ribs=json.loads((OUT/'aft_rib_geometry.json').read_text())['ribs']
    aft.RIBS.update({int(s):{k:np.array(v) if k in ('oi','oo','bi','bo','arc') else v for k,v in r.items()} for s,r in ribs.items()})


def core_map(name,groups):
    assert TOP_GROUP is not None
    top=[g for g in groups if g['material']==70]
    others=[g for g in groups if g['material']!=70]
    new=[g for g in others if 70<=g['material']<=79]
    rest=[g for g in others if not 70<=g['material']<=79]
    def area(gs):
        ts=np.concatenate([g['corners'] for g in gs])[:,:,:3]
        return np.linalg.norm(np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]),axis=1).sum()/2
    assert abs(area(top)-area([TOP_GROUP]))<2e-5
    return prev.prev.prev.core_map(name,rest)+prev.new_map(new)+[TOP_GROUP]


def main():
    prepare()
    prev.prev.export_model(OUT,PREVIOUS,core_map)


if __name__=='__main__':main()
