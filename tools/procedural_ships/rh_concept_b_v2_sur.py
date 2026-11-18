"""Static unfolded collision: real embedded equipment hulls and ship-sized shield."""
import json
import struct as S
import numpy as np
from scipy.spatial import ConvexHull
import rh_concept_b_v2 as v
from ship_collision_audit import sur_parts,surface

f,damage,OUT=v.f,v.damage,v.OUT
sur=damage.sur


def read_hulls(blob):
    result=[]
    def visit(at):
        right,ledge=S.unpack_from('<ii',blob,at)
        if right:visit(at+28);visit(at+right);return
        off=at+ledge;point_offset,client,flags,count,_=S.unpack_from('<iIIHH',blob,off)
        ids=[S.unpack_from('<H',blob,off+20+face*16+k*4)[0] for face in range(count) for k in range(3)]
        points=[S.unpack_from('<3f',blob,off+point_offset+index*16) for index in sorted(set(ids))]
        result.append((client,np.array(points)))
    visit(S.unpack_from('<i',blob,32)[0]);return result


def main():
    nodes=f.mesh.read_tree((OUT/'unfolded_reference.cmp').read_bytes())[1]
    names=f.component_map(nodes);tr,_=f.audit.transforms(nodes);local=f.local_geometry(nodes)
    world={file:f.base.world(gs,*tr[file.lower()]) for file,gs in local.items()}
    prior=json.loads((f.OUT/'collision_manifest.json').read_text())
    regions={p['name']:p['regions'] for p in prior['parts']}
    own={};all_hulls=[];report=[]
    for file,groups in world.items():
        name=names[file]
        if '_glass_' in name.lower() or name.lower().startswith('baydoor'):continue
        triangles=np.concatenate([g['corners'][...,:3] for g in groups])
        hulls=damage.hull_regions(triangles,f.mesh.crc(name),regions[name])
        points=triangles.reshape(-1,3);covered=np.zeros(len(points),bool)
        for h in hulls:
            q=ConvexHull(h.points);covered|=np.all(points@q.equations[:,:3].T+q.equations[:,3]<=3e-4,axis=1)
        if not covered.all():
            leftover=triangles[np.any(~covered.reshape(-1,3),axis=1)]
            for side in (-1,1):
                pts=leftover[np.mean(leftover[...,0],axis=1)*side>=0].reshape(-1,3)
                if len(pts)>=4 and np.linalg.matrix_rank(pts-pts[0])==3:hulls.append(sur.make_hull(pts,f.mesh.crc(name)))
        r,t=tr[file.lower()];own[name]=[sur.Hull((h.points-t)@r,h.faces,h.hull_id) for h in hulls]
        all_hulls+=hulls;report.append(dict(part=name,hulls=len(hulls),vertices=len(points)))
    original=f.mesh.read_tree(v.ORIGINAL.read_bytes())[1]
    old_hp=f.hp_world(original);new_hp=f.hp_world(nodes)
    old_name={f.mesh.crc(h['name']):key for key,h in old_hp.items()};embedded={}
    for pid,chunks in sur_parts(v.ORIGINAL.with_suffix('.sur').read_bytes()):
        if pid!=f.mesh.crc('Root'):continue
        for tag,blob in chunks:
            if tag!=b'surf':continue
            for client,points in read_hulls(blob):
                if client in old_name:embedded[old_name[client]]=points
    templates={k:k for k in embedded if k!='hpmount'}
    templates.update(hpthruster02='hpthruster01',hpweapon06='hpweapon05',hpmiscgun01='hpweapon05',
                     hpturret02='hpturret01',hpturret03='hpturret01')
    hpids={name:[] for name in own};equipment=[]
    for name,template in templates.items():
        if name not in new_hp:continue
        target=new_hp[name];source=old_hp[template]
        local_points=(embedded[template]-source['position'])@np.array(source['orientation'])
        points=local_points@np.array(target['orientation']).T+target['position']
        h=sur.make_hull(points,f.mesh.crc(target['name']))
        owner=names[target['file']];r,t=tr[target['file'].lower()]
        own[owner].append(sur.Hull((h.points-t)@r,h.faces,h.hull_id));hpids[owner].append(h.hull_id)
        all_hulls.append(h)
        equipment.append(dict(name=target['name'],owner=owner,template=source['name'],triangles=len(h.faces),
                              bounds=[h.points.min(0),h.points.max(0)]))
    # Shield wraps the visible unfolded ship AND embedded equipment hulls.
    points=np.concatenate([h.points for h in all_hulls]);envelope=sur.make_hull(points,0)
    center=(points.min(0)+points.max(0))*.5
    points=center+(envelope.points-center)*1.06
    shield=sur.make_hull(points,f.mesh.crc('HpMount'))
    own['Root'].append(shield);all_hulls.append(shield);hpids['Root'].append(shield.hull_id)
    q=ConvexHull(shield.points)
    covered=np.concatenate([h.points for h in all_hulls[:-1]])
    assert np.all(covered@q.equations[:,:3].T+q.equations[:,3]<=2e-4)
    raw=bytearray(b'vers'+S.pack('<f',2.))
    for name,hulls in own.items():
        root=name=='Root'
        ids=sorted({i for values in hpids.values() for i in values}) if root else sorted(hpids[name])
        payload,lo,hi=sur.encode_surface(all_hulls if root else hulls)
        raw.extend(S.pack('<II',f.mesh.crc(name),2+int(root)+int(bool(ids))))
        if root:raw.extend(b'!fxd')
        raw.extend(b'exts'+S.pack('<6f',*lo,*hi)+b'surf'+S.pack('<I',len(payload))+payload)
        if ids:raw.extend(b'hpid'+S.pack('<I',len(ids))+np.array(ids,'<u4').tobytes())
    dest=OUT/'rh_concept_b.sur';dest.write_bytes(raw)
    parsed=sur_parts(raw)
    # !fxd creates a separately built physical body in this engine. Only Root
    # has it: every child uses the static unfolded surface in the root aggregate.
    for part,chunks in parsed:
        assert (b'!fxd' in [tag for tag,_ in chunks])==(part==f.mesh.crc('Root'))
        for tag,blob in chunks:
            if tag==b'surf':surface(blob)
    v.dump('sur_manifest.json',dict(sur_sha256=f.digest(dest),pose='unfolded; static root aggregate',
        physical_bodies=['Root'],parts=report,equipment=equipment,
        shield=dict(name='HpMount',triangles=len(shield.faces),bounds=[shield.points.min(0),shield.points.max(0)],
                    covers_hull_and_equipment=True),
        original_sur_sha256=f.digest(v.ORIGINAL.with_suffix('.sur'))))
    v.dump('sur_preview.json',[dict(name=next((n for n in names.values() if f.mesh.crc(n)==h.hull_id),hex(h.hull_id)),
        points=h.points,faces=h.faces,shield=h.hull_id==f.mesh.crc('HpMount')) for h in all_hulls])
    print('STATIC SUR',len(raw),'bytes',len(equipment),'equipment hulls; shield',len(shield.faces),'triangles',flush=True)


if __name__=='__main__':main()
