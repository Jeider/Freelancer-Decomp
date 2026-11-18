"""Check editable/native agreement and new proper surface crossings near shoulders."""
import json
from pathlib import Path
import numpy as np
import epaulettes as e


def corners(data):
    p=np.array(data['points']);pi=np.array(data['point_indices'])
    return p[pi[np.array([t for g in data['groups'] for t in g['faces']])]]


def segment_hits(a,b,tri):
    direction=b-a;u=tri[1]-tri[0];v=tri[2]-tri[0];h=np.cross(direction,v);det=u@h
    if abs(det)<1e-14:return False
    s=a-tri[0];x=(s@h)/det;q=np.cross(s,u);y=(direction@q)/det;t=(v@q)/det
    return 1e-5<t<1-1e-5 and x>1e-5 and y>1e-5 and x+y<1-1e-5


def crossings(tris,parents):
    lo=tris.min(1);hi=tris.max(1);found=set()
    for i,a in enumerate(tris):
        if hi[i,1]<.49 or np.max(abs(a[:,0]))<.11:continue
        candidates=np.flatnonzero((hi>=lo[i]-1e-7).all(1)&(lo<=hi[i]+1e-7).all(1)&(np.arange(len(tris))>i))
        for j in candidates:
            pair=tuple(sorted((int(parents[i]),int(parents[j]))))
            if pair[0]==pair[1] or pair in found:continue
            b=tris[j]
            if np.min(np.linalg.norm(a[:,None]-b[None,:],axis=-1))<1e-6:continue
            if any(segment_hits(x,y,b) for x,y in zip(a,np.roll(a,-1,axis=0))) or any(segment_hits(x,y,a) for x,y in zip(b,np.roll(b,-1,axis=0))):found.add(pair)
    return found


def main():
    for name in e.TARGETS:
        folder=e.OUT/name;native=json.loads((folder/'native_validation.json').read_text());topology=json.loads((folder/'topology.json').read_text())
        before=e.c.load_json(folder/'before.json.gz');after=e.c.load_json(folder/'after.json.gz')
        raw=Path(native['dfm']).read_bytes();assert e.c.digest(raw)==native['dfm_sha256']
        h,roots=e.c.read_tree(raw);records,groups,faces=e.c.as_records(roots[0])
        assert native['geometry_sha256']==topology['geometry_sha256']==e.c.digest(e.c.write_tree(h,[e.c.mesh_of(roots[0])]))
        for i,r in enumerate(records):
            assert np.array_equal(r['p'],after['points'][after['point_indices'][i]])
            assert np.array_equal(r['n'],after['normals'][after['point_indices'][i]])
            assert np.array_equal(r['uv'],after['uv'][after['uv_indices'][i]])
            assert r['skin']=={int(k):v for k,v in after['skin'][i].items()}
        assert [[list(t) for t in group] for group in faces]==[g['faces'] for g in after['groups']]
        a=corners(before);b=corners(after);old=crossings(a,np.arange(len(a)));new=crossings(b,topology['face_parent_flat'])
        introduced=sorted(new-old)
        e.dump(folder/'surface_validation.json',dict(dfm_sha256=native['dfm_sha256'],geometry_sha256=native['geometry_sha256'],
            editable_data_matches_export=True,proper_crossings_before=sorted(old),proper_crossings_after=sorted(new),
            introduced_proper_crossings=introduced,all_passed=not introduced,
            scope='Proper noncoplanar triangle crossings near epaulettes, excluding shared-vertex neighbors; unchanged existing crossings allowed.'))
        assert not introduced,(name,'New surface crossings',introduced)
        print('SURFACES_PASS',name,'existing',len(old),'after',len(new),'new',len(introduced),flush=True)


if __name__=='__main__':main()
