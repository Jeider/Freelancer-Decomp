"""Validate the offline F14 LOD0 UV prototype and its saved Blender review."""
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
import rh_fighter_f14_uv as build


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    out=build.OUT
    data=json.loads((out/'geometry.json').read_text(encoding='utf8'))
    source=json.loads(build.SOURCE.read_text(encoding='utf8'))
    review=json.loads((out/'blender_check.json').read_text(encoding='utf8'))
    audit=json.loads((out/'uv_report.json').read_text(encoding='utf8'))
    current=digest(out/'geometry.json')
    assert review['geometry_sha256']==audit['geometry_sha256']==current
    assert review['saved_and_reopened'] and not review['lid_collisions']
    original={e['name']:e for e in source['objects']}
    closed={e['name'] for e in data['objects'] if e['authored_closed']}
    for e in review['objects']:
        if e['name'] in closed:
            assert e['nonmanifold_edges']==e['inconsistent_winding_edges']==0
            assert e['signed_volume']>0
    rows=[];micro_uv=[];interiors=[]
    for e in data['objects']:
        old=original[e['name']]
        if e['name'] in ('Native_cabin','glass_lod1'):
            assert old['groups']==e['groups'],e['name']
        xyz=[]
        for g in e['groups']:
            a=np.array(g['corners']);assert np.isfinite(a).all()
            p=a[:,:,:3];xyz.extend(p.reshape(-1,3))
            area=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)/2
            mat=data['materials'][str(g['material'])]
            if mat['image_path'] and e['name'] not in ('Native_cabin','glass_lod1'):
                du=a[:,1,6:8]-a[:,0,6:8];dv=a[:,2,6:8]-a[:,0,6:8]
                ua=abs(du[:,0]*dv[:,1]-du[:,1]*dv[:,0])/2
                tiny=ua<1e-12
                assert not np.any(tiny&(area>1e-6)),(e['name'],mat['name'])
                if tiny.any():micro_uv.append(dict(object=e['name'],material=mat['name'],
                    count=int(tiny.sum()),world_area=float(area[tiny].sum()),max_area=float(area[tiny].max())))
            if 'metal' in mat['texture'].lower():
                if e['name']=='Root':
                    assert np.max(abs(p[:,:,0]))<=.82001
                    assert p[:,:,2].min()>=-4.25001 and p[:,:,2].max()<=2.94001
                    assert p[:,:,1].min()>=-.70001
                elif e['name']=='BayDoor_lod1':
                    assert np.max(p[:,:,1]-(.740334+.087487*(p[:,:,2]+3.889885)))<0
                else:raise AssertionError(('Exterior metal',e['name']))
                interiors.append(dict(object=e['name'],material=mat['name'],triangles=len(a)))
        xyz=np.array(xyz);before=np.concatenate([np.array(g['corners'])[...,:3].reshape(-1,3) for g in old['groups']])
        delta=max(float(abs(xyz.min(0)-before.min(0)).max()),float(abs(xyz.max(0)-before.max(0)).max()))
        assert delta<1e-5,(e['name'],delta)
        rows.append(dict(object=e['name'],bounds_delta=delta,triangles=sum(len(g['corners']) for g in e['groups'])))
    limits=[];salts=set()
    for exported in data['exports']:
        assert digest(exported['file'])==exported['sha256']
        salt=exported['salt'];assert salt not in salts;salts.add(salt)
        _,nodes=build.f.mesh.read_tree(Path(exported['file']).read_bytes())
        assert not any(n.name.lower() in ('material library','texture library') for n in nodes[0].children)
        private=list(exported['private_submodels'].values())+list(exported['private_meshes'].values())
        assert all(salt in n for n in private)
        assert len({build.f.mesh.crc(n) for n in private})==len(private)
        for path,node in build.f.mesh.walk(nodes):
            if path.endswith('/VMeshData'):
                _,_,groups,indices,fvf,vertices=struct.unpack_from('<II4H',node.blob)
                assert 0<indices<=65535 and 0<vertices<=65535 and indices%3==0 and fvf==0x112
                limits.append(dict(resource=path,vertices=vertices,indices=indices,groups=groups))
    for path,value in data['sources'].items():assert digest(path)==value,path
    report=dict(status='passed',geometry_sha256=current,blend_sha256=digest(review['blend']),
        source_sha256=digest(build.SOURCE),native_cabin_and_glass_unchanged=True,
        bounds=rows,closed_parts_checked=len(closed),native_baydoor_phases=31,
        cargo_material_assignments=interiors,subpixel_uv_degeneracies=micro_uv,
        uv_degeneracy_threshold_world_area=1e-6,mesh_limits=limits,
        exported_salts=sorted(salts),embedded_materials=False,installed=False,game_launched=False)
    (out/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(dict(status='passed',triangles=data['total_triangles'],
        closed_parts=len(closed),max_vertices=max(r['vertices'] for r in limits),
        max_indices=max(r['indices'] for r in limits),micro_uv_area=sum(r['world_area'] for r in micro_uv))))


if __name__=='__main__':main()
