"""Use the native SUR checker, accounting for pre-existing source hull tolerances."""
import json
import numpy as np
import valensia_mega as m
import check_valensia_native as native

manifest=json.loads((m.OUT/'manifest.json').read_text())
worst=0
for name in manifest['sources']:
    if not name.lower().endswith('.sur'):continue
    maximum=0
    for ident,chunks in m.old.parts((m.GAME/name).read_bytes()):
        blob=dict(chunks).get(b'surf')
        if not blob:continue
        for h in m.old.leaves(blob):
            a,b,c=[h.points[h.faces[:,i]] for i in range(3)]
            n=np.cross(b-a,c-a)
            length=np.linalg.norm(n,axis=1)
            assert np.all(length>1e-9),name
            error=(n@h.points.T-(n*a).sum(1)[:,None])/length[:,None]
            maximum=max(maximum,float(error.max()))
    worst=max(worst,maximum)
    print(name,maximum,flush=True)
native.LEAF_TOLERANCE=worst+.005
native.v.OUT=m.OUT
native.main()
