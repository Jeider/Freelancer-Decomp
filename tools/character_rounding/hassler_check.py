"""Reopen and verify the editable prototype; no game launch or game writes."""
import sys,json,hashlib,math,gzip
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(Path(__file__).parent))
from blender_workspace import configure
from hassler_build import OUT,C4,load,bindings,dump
configure('character_rounding')

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def positions(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    p=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();return p

def main():
    path=OUT/'hassler_rigged.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding')
    scene=bpy.context.scene;scene.frame_set(1);rig=bpy.data.objects['RIG — native Rheinland'];body=load('body')
    assert len(rig.data.bones)==len(body['bones'])==28
    max_bind_error=0.
    for b,B in zip(body['bones'],bindings(body)):
        native=C4@Matrix(B.tolist());current=rig.data.bones[b['name']].matrix_local
        max_bind_error=max(max_bind_error,max(abs(native[i][j]-current[i][j]) for i in range(4) for j in range(4)))
        assert np.array_equal(np.asarray(rig.data.bones[b['name']]['native_inverse_bind']),np.asarray(b['native_bind'])),b['name']
        actual=rig.data.bones[b['name']].parent
        assert (actual.name if actual else None)==b['parent']
    assert max_bind_error<2e-5,max_bind_error
    for label in ('ARCHIVE — native body (disabled)','ARCHIVE — full Meshy (disabled)'):
        col=bpy.data.collections[label];assert col.hide_render and col.hide_viewport
    ob=bpy.data.objects['Hassler — EDIT clothing'];lining=bpy.data.objects['Hassler — inner collar lining']
    me=ob.data;me.calc_loop_triangles();assert 'Meshy source UV' in me.uv_layers and 'EDIT — clothing charts' in me.uv_layers
    uv=me.uv_layers['EDIT — clothing charts'];pts=np.array([v.co[:] for v in me.vertices])
    weights=np.zeros((len(pts),len(rig.data.bones)))
    for v in me.vertices:
        for g in v.groups:weights[v.index,g.group]=g.weight
    assert np.max(abs(weights.sum(1)-1))<2e-6
    assert (np.count_nonzero(weights>0,axis=1)<=4).all()
    rest=positions(ob);rest_error=float(np.max(np.linalg.norm(rest-pts,axis=1)));assert rest_error<2e-5,rest_error
    split=set();negative_uv=0;degenerate=0;uv_degenerate=0;max_uv=0;uv_failures={};uv_bad_area=0.
    region_names=sorted(r['name'] for r in json.loads((OUT/'uv_regions.json').read_text())['regions'])
    for tri in me.loop_triangles:
        v=pts[list(tri.vertices)];area=np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))
        degenerate+=area<1e-12
        tex=np.array([uv.data[i].uv[:] for i in tri.loops]);signed=np.cross(tex[1]-tex[0],tex[2]-tex[0])
        negative_uv+=signed<0;uv_degenerate+=abs(signed)<1e-13
        if abs(signed)<1e-13:
            name=region_names[me.attributes['clothing_region'].data[tri.polygon_index].value]
            uv_failures[name]=uv_failures.get(name,0)+1;uv_bad_area+=area*.5
        assert np.isfinite(tex).all() and tex.min()>=-1e-5 and tex.max()<=1.00001
        for li in tri.loops:
            loop=me.loops[li];n=me.corner_normals[li].vector;t=uv.data[li].uv
            split.add((loop.vertex_index,tuple(round(c,6) for c in n),tuple(round(c,7) for c in t)))
    count=len(split)+len(lining.data.vertices)*2
    assert count<65536,('DFM 16-bit logical-vertex range exceeded',count)
    checks=[]
    # Use real bend poses from this file, not arbitrary per-bone translations.
    original_edges=np.array([tuple(e.vertices) for e in me.edges]);lengths=np.linalg.norm(pts[original_edges[:,1]]-pts[original_edges[:,0]],axis=1)
    for frame in (1,30,60,90,120,150):
        scene.frame_set(frame);p=positions(ob);assert np.isfinite(p).all()
        lengths2=np.linalg.norm(p[original_edges[:,1]]-p[original_edges[:,0]],axis=1)
        ratio=lengths2/np.maximum(lengths,1e-6)
        worst=int(ratio.argmax());regular=lengths>.002
        checks.append({'frame':frame,'max_edge_stretch':float(ratio.max()),'p99_edge_stretch':float(np.quantile(ratio,.99)),
                       'worst_ratio_edge_rest_m':float(lengths[worst]),'worst_ratio_edge_posed_m':float(lengths2[worst]),
                       'max_stretch_for_edges_over_2mm':float(ratio[regular].max()),
                       'max_stretch_edge_midpoint':pts[original_edges[worst]].mean(0).tolist()})
    scene.frame_set(1)
    for kind,hp,name in [('head','hp_head','Hassler head — native unchanged'),('left_hand','hp_left b','Left glove — native unchanged'),('right_hand','hp_right b','Right glove — native unchanged')]:
        data=load(kind);obj=bpy.data.objects[name]
        transform=C4@Matrix((np.array(body['hardpoints'][hp]['matrix'])@np.linalg.inv(np.array(data['hardpoints'][hp]['matrix']))).tolist())
        wanted=np.array([transform@Vector(p) for p in data['points']]);actual=np.array([v.co[:] for v in obj.data.vertices])
        assert len(actual)==len(wanted) and np.max(abs(actual-wanted))<1e-6
        assert obj['source_sha256']==data['sha256']
    missing=[]
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file and im.users and not Path(bpy.path.abspath(im.filepath)).exists():missing.append(im.filepath)
    assert not missing,missing
    audit=json.loads((OUT/'source_audit.json').read_text())
    for entry in list(audit['user_inputs'].values())+list(audit['native'].values()):assert digest(Path(entry['path']))==entry['sha256'],entry['path']
    # Export a transparent wire guide and normalized chart list for editing.
    uvpoints=np.array([uv.data[l.index].uv[:] for l in me.loops]);wire=[]
    for f in me.polygons:
        wire.append([uvpoints[l].tolist() for l in f.loop_indices])
    (OUT/'uv_wire.json.gz').write_bytes(gzip.compress(json.dumps(wire,separators=(',',':')).encode()))
    report={'blend':str(path),'blend_sha256':digest(path),'reopened':True,'native_bind_max_matrix_error':max_bind_error,
            'native_body_skeleton_preserved':True,'head_and_glove_geometry_unchanged':True,'original_collections_hidden':True,
            'rest_error_m':rest_error,'body_triangles':len(me.loop_triangles)+sum(len(f.vertices)-2 for f in lining.data.polygons),
            'body_vertices':len(pts)+len(lining.data.vertices),'dfm_logical_vertices_upper_bound':count,'dfm_index_limit':65535,
            'within_dfm_index_range':True,'max_influences':int((weights>0).sum(1).max()),'degenerate_triangles':int(degenerate),
            'degenerate_uv_triangles':int(uv_degenerate),'mirrored_uv_triangles':int(negative_uv),'poses':checks,
            'uv_collapsed_area_m2':uv_bad_area,'uv_collapsed_by_region':uv_failures,
            'source_files_unchanged':True,'game_export_validated':False,'game_animations_validated':False,'installed':False}
    dump(OUT/'validation.json',report);print(json.dumps(report,indent=2))

if __name__=='__main__':main()
