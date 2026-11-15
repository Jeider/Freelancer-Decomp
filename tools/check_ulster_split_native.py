"""Validate generated Ulster SURs, explicitly auditing discarded source line leaves."""
import json
import numpy as np
import ulster_shortsplit as p
import check_valensia_native as native

m=p.m
manifest=json.loads((p.OUT/'manifest.json').read_text())
discarded={(d['source'].lower(),d['leaf']) for d in manifest['discarded_degenerate_leaves']}
seen=set();worst=0
for name in manifest['sources']:
    if not name.lower().endswith('.sur'):continue
    for ident,chunks in m.old.parts((m.GAME/name).read_bytes()):
        blob=dict(chunks).get(b'surf')
        if not blob:continue
        for index,h in enumerate(m.old.leaves(blob)):
            a,b,c=[h.points[h.faces[:,i]] for i in range(3)]
            n=np.cross(b-a,c-a);length=np.linalg.norm(n,axis=1)
            if np.any(length<=1e-9):
                key=(name.lower(),index)
                assert key in discarded and np.all(length<=1e-9) and np.linalg.matrix_rank(h.points-h.points.mean(0))<2
                seen.add(key);continue
            error=(n@h.points.T-(n*a).sum(1)[:,None])/length[:,None]
            worst=max(worst,float(error.max()))
assert seen==discarded
print('Source tolerance:',worst,'; discarded zero-area source leaves:',len(seen),flush=True)
native.LEAF_TOLERANCE=worst+.005
native.v.OUT=p.OUT
native.main()
