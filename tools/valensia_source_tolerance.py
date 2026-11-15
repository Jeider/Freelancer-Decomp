"""Report geometric roundoff already present in the original industrial SURs."""
import numpy as np
import valensia_optimize as v

for name in ('space_industrial01a', 'space_industrial01a_alt', 'space_industrial02a', 'space_industriala', 'space_industriala_alt'):
    path = v.GAME/'DATA/SOLAR/misc'/(name+'.sur')
    hulls = v.leaves(dict(v.parts(path.read_bytes())[0][1])[b'surf'])
    worst = 0
    for h in hulls:
        a, b, c = [h.points[h.faces[:,i]] for i in range(3)]
        normal = np.cross(b-a,c-a)
        distance = (normal@h.points.T-(normal*a).sum(1)[:,None])/np.linalg.norm(normal,axis=1)[:,None]
        worst = max(worst, distance.max())
    print(name, worst)
