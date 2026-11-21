"""Rebase the accepted fighter to its main-body centre, including every joint."""
import copy
import numpy as np

BODY = ('Root', 'Port_carved_flank', 'Starboard_carved_flank',
        'Sculpted_roof_shoulders')


def transform(rt, origin):
    r, t = map(np.asarray, rt)
    return r, t + r @ origin - origin


def rebase(entries, groups, hps, nodes):
    import rh_fighter_final as d
    p = np.concatenate([d.points(entries[name]['groups']) for name in BODY])
    lo, hi = p.min(0), p.max(0)
    origin = np.round((lo + hi) / 2, 6)
    assert abs(origin[0]) < 1e-6
    origin[0] = 0
    before_hp = copy.deepcopy(hps)
    samples = []
    for script, end in (('Sc_extend wing', 2), ('Sc_launch extend', 7),
                        ('Sc_extend wing keep', 2), ('Sc_open baydoor', 2.1333333),
                        ('Sc_end anim', 1/30), ('Sc_force extend', 1e17)):
        for time in np.linspace(0, end, 61):
            samples.append((script, time, d.runtime(nodes, time, script)))
    # entries and groups deliberately share the same arrays. Shift each once.
    shifted = set()
    for gs in groups.values():
        for g in gs:
            a = g['corners']
            if id(a) not in shifted:
                a[..., :3] -= origin
                shifted.add(id(a))
    assert all(id(g['corners']) in shifted for e in entries.values() for g in e['groups'])
    for h in hps.values():
        h['position'] = np.asarray(h['position']) - origin
    cons = d.f.mesh.child(d.f.mesh.child(nodes[0], 'Cmpnd'), 'Cons')
    for node in cons.children:
        kind = node.name.lower()
        size = {'fix':176, 'rev':208, 'pris':208}[kind]
        raw = bytearray(node.blob)
        for at in range(0, len(raw), size):
            values = np.frombuffer(raw, '<f4', (size-128)//4, at+128).copy()
            if kind == 'fix':
                values[:3] += values[3:12].reshape(3,3) @ origin - origin
            else:
                # Both frames change, including the stationary pivot/offset.
                values[:3] -= origin
                values[3:6] -= origin
            raw[at+128:at+size] = values.tobytes()
        node.blob = bytes(raw)
    error = 0
    for script, time, old in samples:
        new = d.runtime(nodes, time, script)
        for name, rt in old.items():
            expect = transform(rt, origin)
            error = max(error, *(float(np.max(abs(a-b))) for a,b in zip(expect,new[name])))
    assert error < 2e-6, error
    hp_error = max(float(np.max(abs(h['position'] + origin - before_hp[k]['position'])))
                   for k,h in hps.items())
    assert hp_error < 1e-12
    report = dict(origin_offset=origin, convention='exported = authoring - origin_offset',
                  method='midpoint of main structural torso bounds; excludes cockpit, rear drum, engines and wings',
                  reference_objects=BODY, reference_bounds=[lo,hi],
                  centered_bounds=[lo-origin,hi-origin], matrix_samples=len(samples)*len(groups),
                  max_conjugation_error=error, relative_hardpoint_error=hp_error,
                  hardpoints_preserved=len(hps), orientation_and_shape_unchanged=True)
    d.dump(d.OUT/'origin_check.json', report)
    return origin
