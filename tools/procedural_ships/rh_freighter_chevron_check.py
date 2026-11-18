"""Compare the offline uv_08 revision with uv_07 and audit ROOT's actual cost."""
import collections
import json
import numpy as np
import rh_freighter_aft_chevron as edit

OUT=edit.OUT
f=edit.f


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def hp_semantics(nodes):
    names=f.component_map(nodes)
    return {(names[h['file']],h['name']): (h['position'],h['orientation'])
            for h in f.hp_world(nodes).values()}


def main():
    edit.guard()
    before=read(edit.PREVIOUS/'mechanical_geometry.json')
    after=read(OUT/'mechanical_geometry.json')
    old={o['name']:o for o in before['objects']}
    unchanged=[]
    for ob in after['objects']:
        if ob['name'].startswith('Continuous hull'):continue
        assert ob==old[ob['name']],ob['name']
        unchanged.append(ob['name'])
    _,nodes=f.mesh.read_tree((OUT/'rh_pir_freighter.cmp').read_bytes())
    _,previous=f.mesh.read_tree((edit.PREVIOUS/'rh_pir_freighter.cmp').read_bytes())
    hp,rhp=hp_semantics(nodes),hp_semantics(previous)
    assert hp.keys()==rhp.keys()
    for key in hp:
        assert np.allclose(hp[key][0],rhp[key][0],atol=1e-7),key
        assert np.allclose(hp[key][1],rhp[key][1],atol=1e-7),key
    names=f.component_map(nodes);flight,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    decoded={names[file]:f.base.world(gs,*flight[file.lower()]) for file,gs in f.local_geometry(nodes).items()}
    checks=[]
    for side,part in [(-1,'rh_port_side_lod1'),(1,'rh_star_side_lod1')]:
        quads=edit.strip_unfold(side);counts=collections.Counter();error=0
        for group in decoded[part]:
            for tri in np.array(group['corners']):
                for segment,(quad,co) in quads.items():
                    coords=edit.aft.on_quad(tri,quad,co)
                    if coords is None:continue
                    assert group['material']==edit.uv.S
                    err=float(abs(tri[:,6:8]-(coords*.18+[.11,.53])).max())
                    assert err<2e-5,(part,segment,err)
                    error=max(error,err);counts[segment]+=1;break
        assert len(counts)==10,(part,counts)
        checks.append(dict(part=part,segments=dict(counts),max_export_uv_error=error))
    rows=read(OUT/'mesh_breakdown.json')['objects'];root=[o for o in rows if o['owner']=='Root']
    core=next(o for o in rows if o['object'].startswith('Continuous hull'))
    core_ob=next(o for o in after['objects'] if o['name'].startswith('Continuous hull'))
    wall_counts=collections.Counter()
    for g in core_ob['groups']:
        for t in np.array(g['corners']):
            p=t[:,:3];n=edit.old.normal(t)
            for axis,position,normal,label in [(0,2.39,-1,'right'),(0,-2.39,1,'left'),
                    (1,-3.10,1,'floor'),(2,-3.72,1,'front'),(2,5.72,-1,'rear')]:
                if abs(p[:,axis]-position).max()<1e-4 and n[axis]*normal>.99:
                    wall_counts[label]+=1
    assert len(wall_counts)==5,wall_counts
    b=read(OUT/'build.json')
    report=dict(cmp_sha256=f.digest(OUT/'rh_pir_freighter.cmp'),
        unchanged_geometry_objects=unchanged,hardpoints_identical_to_uv07=len(hp),
        side_uv_roundtrip=checks,side_shared_edge_continuity=edit.SEAMS,
        root_export_triangles=sum(o['export_triangles'] for o in root),
        core_export_triangles=core['export_triangles'],core_authoring_triangles=core['source_triangles'],
        main_hold_wall_authoring_triangles=dict(wall_counts),
        hump_authoring_triangles=sum(o['source_triangles'] for o in root if o['object'].startswith('Stepped circular')),
        hump_export_triangles=sum(o['export_triangles'] for o in root if o['object'].startswith('Stepped circular')),
        total_triangles=b['total_triangles'],maximum=b['maximum'],
        removed_hidden_geometry=False,damage_geometry_authored=False,
        limitation='Core counts include visible belly, nose and stern plus pocket and hold walls; not a hidden-triangle count. No GPU timing performed.',
        installed=False,game_launched=False)
    (OUT/'revision_check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('unchanged_geometry_objects','side_uv_roundtrip','side_shared_edge_continuity')},indent=2))


if __name__=='__main__':main()
