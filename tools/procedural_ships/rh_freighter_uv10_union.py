"""Join the marked pale stern extension into the existing core shell, offline."""
import json
import sys
from pathlib import Path
import bpy
import bmesh
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
from rh_concept_b_final_blender import mesh_object,groups_from_mesh
OUT=HERE.parents[1]/'out/ship_design/rh_freighter/prototypes/uv_10'
PREFIX='Aft pale shoulder'
REPORT='pale_stern_union.json'
if '--variant' in sys.argv:
    variant=sys.argv[sys.argv.index('--variant')+1]
    assert variant.replace('_','').isalnum();OUT=OUT.parent/variant
if '--prefix' in sys.argv:PREFIX=sys.argv[sys.argv.index('--prefix')+1]
if '--report' in sys.argv:
    REPORT=sys.argv[sys.argv.index('--report')+1]
    assert Path(REPORT).name==REPORT and REPORT.endswith('.json')


def conform_seams(mesh):
    """Restore collinear boundary vertices lost by an earlier ngon export."""
    bm=bmesh.new();bm.from_mesh(mesh);splits=0
    for _ in range(40):
        boundary=[e for e in bm.edges if e.is_boundary]
        vertices={v for e in boundary for v in e.verts};candidate=None
        for edge in boundary:
            a,c=edge.verts;d=c.co-a.co;length=d.length_squared
            if length<1e-12:continue
            for v in vertices:
                if v in edge.verts:continue
                t=(v.co-a.co).dot(d)/length
                if 1e-5<t<1-1e-5 and (a.co+d*t-v.co).length<2e-6:
                    candidate=(edge,a,v,t);break
            if candidate:break
        if candidate is None:break
        edge,a,v,t=candidate
        opposite=[next(x for x in face.verts if x not in edge.verts) for face in edge.link_faces if len(face.verts)==3]
        _,new=bmesh.utils.edge_split(edge,a,t);new.co=v.co.copy()
        for tip in opposite:bmesh.ops.connect_verts(bm,verts=[new,tip])
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);splits+=1
    bad=sum(not e.is_manifold for e in bm.edges)
    assert not bad,('unclosed source before union',bad)
    bm.to_mesh(mesh);bm.free();mesh.update()
    return splits


def main():
    path=OUT/'mechanical_geometry.json';data=json.loads(path.read_text())
    core=next(o for o in data['objects'] if o['name'].startswith('Continuous hull'))
    additions=[o for o in data['objects'] if o['name'].startswith(PREFIX)]
    expected=int(sys.argv[sys.argv.index('--expected-count')+1]) if '--expected-count' in sys.argv else (2 if PREFIX=='Aft pale shoulder' else 1)
    assert len(additions)==expected
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mid in {g['material'] for ob in [core,*additions] for g in ob['groups']}:bpy.data.materials.new(str(mid))
    target,_=mesh_object(core,core['name']);before=len(target.data.polygons)
    restored=conform_seams(target.data) if '--conform-seams' in sys.argv else 0
    steps=[]
    def bounds(mesh):
        return [(min(v.co[a] for v in mesh.vertices),max(v.co[a] for v in mesh.vertices)) for a in range(3)]
    for entry in additions:
        operand,_=mesh_object(entry,entry['name']);bpy.context.view_layer.objects.active=target
        # Boolean INDEX mode uses slot numbers, not semantic material names.
        # Give both meshes the same slots so each authored face role survives.
        source_slots=list(operand.data.materials)
        for material in source_slots:
            if material.name not in target.data.materials:target.data.materials.append(material)
        target_slots=list(target.data.materials)
        remap={i:target_slots.index(material) for i,material in enumerate(source_slots)}
        indices=[remap[p.material_index] for p in operand.data.polygons]
        operand.data.materials.clear()
        for material in target_slots:operand.data.materials.append(material)
        for polygon,index in zip(operand.data.polygons,indices):polygon.material_index=index
        previous_bounds=bounds(target.data)
        previous_faces=len(target.data.polygons)
        mod=target.modifiers.new('Join pale stern extension','BOOLEAN')
        mod.operation='UNION';mod.solver='MANIFOLD' if '--manifold-solver' in sys.argv else 'EXACT';mod.object=operand
        bpy.ops.object.modifier_apply(modifier=mod.name)
        assert len(target.data.polygons)>0,('union erased target',entry['name'])
        current_bounds=bounds(target.data)
        assert all(a[0]<=b[0]+2e-5 and a[1]>=b[1]-2e-5 for a,b in zip(current_bounds,previous_bounds)),('union shrank target',entry['name'],previous_faces,len(target.data.polygons))
        steps.append(dict(operand=entry['name'],faces_before=previous_faces,faces_after=len(target.data.polygons)))
        bpy.data.objects.remove(operand,do_unlink=True)
    bm=bmesh.new();bm.from_mesh(target.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bad=sum(not e.is_manifold for e in bm.edges)
    assert not bad,('unclosed joined stern',bad)
    bm.to_mesh(target.data);bm.free();target.data.update()
    core['groups']=groups_from_mesh(target.data,[int(m.name) for m in target.data.materials])
    data['objects']=[o for o in data['objects'] if not o['name'].startswith(PREFIX)]
    if PREFIX=='Aft pale shoulder':data['uv10_changes']['pale_extensions_united_with_core']=True
    data.setdefault('construction_unions',[]).append(dict(prefix=PREFIX,closed=True))
    path.write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
    report=dict(core_faces_before=before,core_faces_after=len(target.data.polygons),nonmanifold_edges=bad,
        unions=len(additions),removed_only_buried_intersections=True,restored_collinear_seam_vertices=restored,
        solver='MANIFOLD' if '--manifold-solver' in sys.argv else 'EXACT',steps=steps)
    (OUT/REPORT).write_text(json.dumps(report,indent=2),encoding='utf8')
    print('STERN_UNION',report)


if __name__=='__main__':main()
