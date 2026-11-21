"""Reopen and check the lower belt, native BR trousers/boots and waist seam."""
import sys,json,gzip
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step15 as s
from hassler_step13_check import snapshot
from hassler_step04_check import rig_snapshot
from hassler_step08_check import evaluated
from hassler_step03_check import topology
configure('character_rounding')


def physical_edges(me):
    key=lambda i:tuple(round(float(x),5) for x in me.vertices[i].co)
    edges={}
    for f in me.polygons:
        ids=list(f.vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):edges.setdefault(tuple(sorted((key(a),key(b)))),[]).append(f.index)
    return edges


def main():
    bpy.ops.wm.open_mainfile(filepath=str(s.PARENT));configure('character_rounding');bpy.context.scene.frame_set(1)
    excluded={s.s14.BASE,s.s14.BELT,s.s14.BUCKLE,s.s14.LOOPS,s.s14.WAIST}
    names=[o.name for o in bpy.data.collections['EDIT — native costume upper study'].objects if o.type=='MESH' and o.name not in excluded]
    names+=['Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged']
    before={n:snapshot(bpy.data.objects[n]) for n in names};bones=rig_snapshot()
    path=s.OUT/'hassler_native_upper.blend';digest=s.s13.sha(path)
    bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    report=json.loads((s.OUT/'report.json').read_text(encoding='utf8'));assert s.s13.sha(s.PARENT)==report['parent_sha256']
    for n,old in before.items():
        now=snapshot(bpy.data.objects[n])
        for k in ('points','normals','world'):assert np.array_equal(old[k],now[k]),(n,k)
        for k in ('faces','weights','materials','material_indices'):assert old[k]==now[k],(n,k)
        for k,v in old['uv_layers'].items():assert np.array_equal(v,now['uv_layers'][k]),(n,k)
    after=rig_snapshot();assert set(after)==set(bones)
    for n,(m,w,p) in after.items():assert np.array_equal(m,bones[n][0]) and w==bones[n][1] and p==bones[n][2]
    d=json.loads(gzip.decompress(Path(report['donor']['json']).read_bytes()));assert d['sha256']==report['donor']['dfm_sha256']
    assert s.s13.sha(Path(report['donor']['json']))==report['donor']['json_sha256']
    rh=s.native.load('body');assert [(b['name'],b['native_bind']) for b in d['bones']]==[(b['name'],b['native_bind']) for b in rh['bones']]
    pants=bpy.data.objects[s.LOWER];me=pants.data;p=np.array(d['points']);uv=me.uv_layers[0];selected={tuple(f) for f in report['pants']['source_faces']}
    # All native faces below the crotch must survive, including the outer toes.
    expected={(gi,fi) for gi,g in enumerate(d['groups']) for fi,f in enumerate(g['faces']) if max(p[f,1])<-.08}
    assert expected<=selected,('Missing lower source faces',sorted(expected-selected))
    maxpos=maxuv=maxskin=0.;nativefaces=0
    groupnames=[g.name for g in pants.vertex_groups]
    for face,(gi,fi) in zip(me.polygons,report['pants']['source_faces']):
        nativeface=d['groups'][gi]['faces'][fi]
        if max(p[nativeface,1])>s.TOP_Z:continue
        assert len(face.vertices)==len(nativeface)
        nativefaces+=1
        for vi,li,ni in zip(face.vertices,face.loop_indices,nativeface):
            maxpos=max(maxpos,float(np.linalg.norm(me.vertices[vi].co-s.native.C@Vector(d['points'][ni]))))
            maxuv=max(maxuv,float(np.max(abs(np.array(uv.data[li].uv)-d['uv'][ni]))))
            actual={groupnames[g.group]:g.weight for g in me.vertices[vi].groups if g.weight>0}
            want={d['bones'][int(j)]['name']:v for j,v in d['skin'][ni].items() if v>0}
            assert actual.keys()==want.keys()
            maxskin=max(maxskin,max(abs(actual[n]-want[n]) for n in want))
    assert maxpos<2e-7 and maxuv<2e-7 and maxskin<2e-7,(maxpos,maxuv,maxskin)
    boundary=[edge for edge,faces in physical_edges(me).items() if len(faces)==1]
    assert all(min(q[2] for q in edge)>.10 for edge in boundary),('Open lower/boot edge',boundary)
    parts={};new={};maxweights=0
    for ob in bpy.data.collections['EDIT — native costume upper study'].objects:
        if ob.type!='MESH':continue
        data=evaluated(ob);parts[ob.name]={k:data[k] for k in ('vertices','triangles')}
        if ob.name not in (s.LOWER,s.WAIST,s.BELT,s.BUCKLE,s.LOOPS):continue
        mesh=ob.data;mesh.calc_loop_triangles();layer=mesh.uv_layers[0];zero=0;inherited=0
        for t in mesh.loop_triangles:
            a,b,c=[np.array(layer.data[i].uv) for i in t.loops]
            bad=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-11
            zero+=int(bad)
            if bad and ob.name==s.LOWER:
                gi,fi=report['pants']['source_faces'][t.polygon_index]
                a,b,c=np.array(d['uv'])[d['groups'][gi]['faces'][fi]]
                inherited+=int(abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-11)
        assert zero==inherited,(ob.name,'New degenerate UV',zero,inherited)
        for v in mesh.vertices:
            weights=[g.weight for g in v.groups if g.weight>0];assert abs(sum(weights)-1)<3e-6
            maxweights=max(maxweights,len(weights))
        assert np.isfinite(data['p']).all()
        t=topology(mesh);new[ob.name]={'uv_degenerate_triangles':zero,'inherited_native_uv_degenerates':inherited,'new_uv_degenerates':zero-inherited,'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles)}
        if ob.name in (s.BELT,s.BUCKLE,s.LOOPS):
            assert not t['boundary_loops'] and t['nonmanifold_edges']==0
            bm=bmesh.new();bm.from_mesh(mesh);volume=bm.calc_volume(signed=True);bm.free();assert volume>0
            new[ob.name]['signed_volume_m3']=float(volume)
        if ob.name==s.WAIST:
            for f in mesh.polygons:assert np.dot(f.normal,[f.center.x,f.center.y-.035,0])>0,('Waist inward',f.index)
    assert maxweights<=4 and sum(d['vertices'] for d in parts.values())<65535
    belt=bpy.data.objects[s.BELT];z=[v.co.z for v in belt.data.vertices]
    gap=report['belt']['tunic_hem_z']-max(z);assert .02<gap<.04 and max(z)-min(z)<.055
    poses=[]
    for frame in (1,30,60,90,120):
        scene.frame_set(frame);base=evaluated(pants);waist=evaluated(bpy.data.objects[s.WAIST]);band=evaluated(belt);coat=evaluated(bpy.data.objects[s.s13.GARMENT])
        seam=max(float(np.linalg.norm(waist['p'][a]-base['p'][b])) for a,b in report['waist_closure']['attachments']);assert seam<2e-6
        contacts=band['tree'].overlap(coat['tree']);assert not contacts,('Belt/tunic overlap',frame,contacts[:5])
        selfhits=[(i,j) for i,j in band['tree'].overlap(band['tree']) if i<j and not set(band['faces'][i])&set(band['faces'][j])];assert not selfhits
        poses.append({'frame':frame,'waist_seam_max_error_m':seam,'belt_tunic_crossings':0,'belt_self_intersections':0})
    scene.frame_set(1)
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_render and col.hide_viewport
    result={'reopened':True,'checks_passed':True,'blend_sha256':digest,'parent_sha256':report['parent_sha256'],'upper_head_hands_uv_materials_rig_exact':True,'native_br_bind_matrices_equal':True,'native_lower_faces_preserved':nativefaces,'all_source_faces_below_crotch_preserved':len(expected),'native_position_max_error_m':maxpos,'native_uv_max_error':maxuv,'native_skin_max_error':maxskin,'pants_open_edges_only_at_waist':len(boundary),'max_skin_influences':maxweights,'belt_tunic_vertical_gap_m':gap,'new_parts':new,'poses':poses,'parts':parts,'body_triangles_with_modifiers':sum(p['triangles'] for p in parts.values()),'game_installed':False,'game_animations_validated':False}
    if '--render' in sys.argv:
        for label,direction,target,scale in [('full_front',(0,1,.03),(0,0,.99),2.08),('full_back',(0,-1,.03),(0,0,.99),2.08),('full_three_quarter',(.65,1,.08),(0,0,.99),2.08),('waist_front',(0,1,.08),(0,.02,1.15),.59),('waist_side',(1,0,.1),(0,.02,1.15),.59),('waist_back',(0,-1,.08),(0,.02,1.15),.59),('boots',(.4,1,.1),(0,.02,.36),.84)]:s.render(scene,label,direction,target,scale)
        scene.frame_set(120);s.render(scene,'turn_pose',(.65,1,.12),(0,.02,1.25),1.28);scene.frame_set(1)
        scene.frame_set(90);s.render(scene,'step_pose',(.65,1,.12),(0,0,.99),2.08);scene.frame_set(1)
        result['previews_bound_to_blend_sha256']=digest
    assert s.s13.sha(path)==digest
    (s.OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('CHECK15',json.dumps({k:result[k] for k in ('checks_passed','body_triangles_with_modifiers','belt_tunic_vertical_gap_m')}),flush=True)

if __name__=='__main__':main()
