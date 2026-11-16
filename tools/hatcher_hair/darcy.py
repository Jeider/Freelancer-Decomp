"""Darcy's short swept hair: conservative sculpt, hair-only subdivision and normals."""
import argparse,json,hashlib,struct
from datetime import datetime
import numpy as np
from build import ROOT,GAME,DataFolder,read_tree,write_tree,child,blob,arr,put,triangles,faces,export
from repair_panel_normals import leaves

OUT=ROOT/'out/darcy_hair';REL='CHARACTERS/HEADS/br_darcy_head.dfm'
HAIR_PREFIX=b'short_hair_br_darcy'
SCULPT=None
PREPARE=None
FOLDED_LOCKS=True
SUBDIVISION_DEPTH=(2,1,0,0,0,0)
def sha(b):return hashlib.sha256(b).hexdigest()

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    baseline=DataFolder(root=OUT/'original')
    if not baseline.data_path(REL).exists():baseline.sync_data_file(REL,(GAME/'DATA'/REL).read_bytes())
    source=baseline.data_path(REL).read_bytes();header,roots=read_tree(source);root=roots[0]
    if PREPARE:PREPARE(root)
    export(root,OUT/'before.json');report=[]
    for lod in child(root,'MultiLevel').children:
        if not lod.name.startswith('Mesh'):continue
        level=int(lod.name[4:]);geo=child(lod,'Geometry');groups=child(lod,'Face_groups')
        targets=[g for g in groups.children if g.children and blob(g,'Material_name').startswith(HAIR_PREFIX)]
        if not targets:continue
        p=arr(geo,'Points','<f4',3);n=arr(geo,'Vertex_normals','<f4',3)
        pi=arr(geo,'Point_indices','<u4').ravel();uv=arr(geo,'UV0','<f4',2);ui=arr(geo,'UV0_indices','<u4').ravel()
        has_uv1=any(node.name=='UV1' for node in geo.children)
        uv1=arr(geo,'UV1','<f4',2) if has_uv1 else uv.copy()
        ui1=arr(geo,'UV1_indices','<u4').ravel() if has_uv1 else ui.copy()
        protected={int(pi[v]) for g in groups.children if g.children and g not in targets for t in triangles(g) for v in t}
        weld={}
        for i,pos in enumerate(p):weld.setdefault(tuple(np.round(pos,5)),[]).append(i)
        for ids in weld.values():
            if any(i in protected for i in ids):protected.update(ids)
        smooth_normals=n.copy()
        for indices in weld.values():
            if any(i in protected for i in indices):continue
            normal=n[indices].mean(axis=0);length=np.linalg.norm(normal)
            if length>1e-10:smooth_normals[indices]=normal/length
        counts=arr(geo,'Point_bone_count','<u4').ravel();first=arr(geo,'Point_bone_first','<u4').ravel()
        ids=arr(geo,'Bone_id_chain','<u4').ravel();weights=arr(geo,'Bone_weight_chain','<f4').ravel()
        skin=[dict(zip(map(int,ids[f:f+c]),map(float,weights[f:f+c]))) for f,c in zip(first,counts)]
        op=p.tolist();on=n.tolist();opi=pi.tolist();oui=ui.tolist();ouv=uv.tolist();oui1=ui1.tolist();ouv1=uv1.tolist()
        def sculpt(pos,normal,mask):
            if SCULPT:return SCULPT(pos,normal,mask,level)
            x,y,z=pos;top=float(np.clip((y-.07)/.08,0,1));back=float(np.clip((.02-z)/.09,0,1))
            q=pos.copy()
            q[0]*=1-.055*mask*back
            q[1]-=mask*(.006*top*back+.002*top)
            q[2]+=mask*.006*back*top
            # Narrow angular crests instead of the earlier smooth cap.
            phase=x*220+z*105+1.4*np.sin(y*21)
            peak=max(0.,1-abs((phase/(2*np.pi))%1-.5)*5)
            ridge=(peak-.28)*.009*mask*top
            q+=normal*ridge
            q[0]-=.004*mask*top*np.clip((z+.02)/.09,0,1)
            return q
        for i in range(len(p)):
            if i not in protected:op[i]=sculpt(p[i],smooth_normals[i],1).tolist()
        emitted={};hair_points=set()
        for target in targets:
            old=triangles(target);new=[]
            def vertex(t,b):
                exact=np.flatnonzero(b>.999999)
                if len(exact):return t[int(exact[0])]
                key=tuple(sorted((t[k],round(float(b[k]),6)) for k in range(3) if b[k]>0))
                if key in emitted:return emitted[key]
                points=p[pi[t]];normals=smooth_normals[pi[t]];pos=b@points;normal=b@normals;normal/=max(np.linalg.norm(normal),1e-9)
                mask=sum(float(b[k]) for k in range(3) if int(pi[t[k]]) not in protected)
                projections=np.array([pos-normals[k]*np.dot(pos-points[k],normals[k]) for k in range(3)])
                pos+=(b@projections-pos)*.3*mask
                pos=sculpt(pos,normal,mask)
                ix=len(op);op.append(pos.tolist());on.append(normal.tolist())
                influences={}
                for k in range(3):
                    for bone,w in skin[int(pi[t[k]])].items():influences[bone]=influences.get(bone,0)+float(b[k])*w
                influences={bone:w for bone,w in influences.items() if w>1e-7};total=sum(influences.values())
                skin.append({bone:w/total for bone,w in influences.items()})
                v=len(opi);opi.append(ix);oui.append(len(ouv));ouv.append((b@uv[ui[t]]).tolist())
                oui1.append(len(ouv1));ouv1.append((b@uv1[ui1[t]]).tolist());emitted[key]=v
                return v
            def subdiv(t,b,depth):
                if not depth:
                    tri=[vertex(t,v) for v in b];new.append(tri);hair_points.update(opi[v] for v in tri);return
                a,c,d=b;ac=(a+c)/2;cd=(c+d)/2;da=(d+a)/2
                for sub in ((a,ac,da),(ac,c,cd),(da,cd,d),(ac,cd,da)):subdiv(t,np.array(sub),depth-1)
            for t in old:subdiv(t,np.eye(3),SUBDIVISION_DEPTH[level])
            faces(target,new)
            report.append(dict(lod=level,hair_before=len(old),hair_after=len(new)))
        # Small folded locks over the scalp: a raised centre edge ending in a
        # pointed tip. Each face has its own normal so the crease stays visible.
        # Roots are embedded in the existing surface; no alpha cards or new pass.
        if level<2 and FOLDED_LOCKS:
            placed=[];extra=0
            for target in targets:
                combined=triangles(target)
                candidates=[]
                for t in combined:
                    ix=[opi[v] for v in t];pts=np.asarray(op)[ix];center=pts.mean(axis=0)
                    if center[1]<.075:continue
                    normal=np.mean(np.asarray(on)[ix],axis=0);normal/=max(np.linalg.norm(normal),1e-9)
                    if normal[1]<.12 and abs(normal[0])<.65:continue
                    candidates.append((center,t,normal))
                candidates.sort(key=lambda item:float(np.sin(np.dot(item[0],[1337,1777,2111]))))
                for center,t,normal in candidates:
                    if any(np.linalg.norm(center-other)<.018 for other in placed):continue
                    if len(placed)>=(34 if level==0 else 18):break
                    placed.append(center)
                    direction=np.array([-.8,.28,-.42]);direction-=normal*np.dot(direction,normal)
                    direction/=max(np.linalg.norm(direction),1e-9)
                    across=np.cross(direction,normal);across/=max(np.linalg.norm(across),1e-9)
                    length=.024; width=.0045
                    # Two buried roots, two shoulders, a ridge and one sharp tip.
                    points=[center-direction*length*.45-across*width-normal*.002,
                            center-direction*length*.45+across*width-normal*.002,
                            center+across*width*.8-normal*.0015,
                            center-across*width*.8-normal*.0015,
                            center+normal*.0035,
                            center+direction*length*.6+normal*.0035]
                    base_uv=np.mean(np.asarray(ouv)[[oui[v] for v in t]],axis=0)
                    base_uv1=np.mean(np.asarray(ouv1)[[oui1[v] for v in t]],axis=0)
                    influences={}
                    for v in t:
                        for bone,w in skin[opi[v]].items():influences[bone]=influences.get(bone,0)+w/3
                    for face in ((0,1,4),(1,2,4),(0,4,3),(3,4,5),(4,2,5),
                                 (0,3,5),(0,5,1),(1,5,2)):
                        a,b,c=[points[i] for i in face];fn=np.cross(b-a,c-a)
                        # Orient the closed lock away from its own interior.
                        outward=(a+b+c)/3-np.mean(points,axis=0)
                        if np.dot(fn,outward)<0:face=tuple(reversed(face));fn=-fn
                        fn/=max(np.linalg.norm(fn),1e-9)
                        fn=fn*.65+normal*.35;fn/=max(np.linalg.norm(fn),1e-9);corners=[]
                        for i in face:
                            ix=len(op);op.append(points[i].tolist());on.append(fn.tolist());skin.append(dict(influences))
                            v=len(opi);opi.append(ix);corners.append(v)
                            # Sample neighbouring hair texels, preserving the original colour.
                            offset=np.array([np.dot(points[i]-center,across),np.dot(points[i]-center,direction)])*1.5
                            oui.append(len(ouv));ouv.append((base_uv+offset).tolist())
                            oui1.append(len(ouv1));ouv1.append(base_uv1.tolist())
                        combined.append(corners);extra+=1
                faces(target,combined)
            report.append(dict(lod=level,folded_locks=len(placed),extra_triangles=extra))
        # Area-weighted normals, welded at UV seams. Preserve all face normals.
        sums={};keys=[tuple(np.round(pos,6)) for pos in op]
        normal_positions=np.asarray(op);normal_directions=np.asarray(on)
        for target in targets:
            for t in triangles(target):
                ix=[opi[v] for v in t];a,b,c=normal_positions[ix];normal=np.cross(b-a,c-a)
                if np.dot(normal,normal_directions[ix].mean(axis=0))<0:normal=-normal
                for i in ix:sums[keys[i]]=sums.get(keys[i],np.zeros(3))+normal
        for i in hair_points-protected:
            normal=sums[keys[i]];length=np.linalg.norm(normal)
            if length>1e-10:on[i]=(normal/length).tolist()
        assert np.array_equal(np.asarray(op,dtype='<f4')[sorted(protected)],p[sorted(protected)])
        assert np.array_equal(np.asarray(on,dtype='<f4')[sorted(protected)],n[sorted(protected)])
        assert len(opi)<65536 and np.isfinite(op).all() and np.isfinite(on).all()
        for name,value,kind in [('Points',op,'<f4'),('Vertex_normals',on,'<f4'),('Point_indices',opi,'<u4'),('UV0',ouv,'<f4'),('UV0_indices',oui,'<u4'),('UV1',ouv1,'<f4'),('UV1_indices',oui1,'<u4')]:
            if name.startswith('UV1') and not has_uv1:continue
            put(geo,name,np.asarray(value,dtype=kind).tobytes())
        starts=[];counts=[];ids=[];weights=[]
        for influence in skin:
            assert abs(sum(influence.values())-1)<1e-4
            starts.append(len(ids));counts.append(len(influence));ids.extend(influence);weights.extend(influence.values())
        for name,value,kind in [('Point_bone_first',starts,'<u4'),('Point_bone_count',counts,'<u4'),('Bone_id_chain',ids,'<u4'),('Bone_weight_chain',weights,'<f4')]:put(geo,name,np.asarray(value,dtype=kind).tobytes())
    data=write_tree(header,roots)
    old={path:b for path,_,b in leaves(source)[1]};new={path:b for path,_,b in leaves(data)[1]}
    for path,b in old.items():
        if '/MultiLevel/' not in path:assert new[path]==b,path
    DataFolder(root=OUT/'stage').sync_data_file(REL,data);export(root,OUT/'after.json')
    previous=json.loads((OUT/'manifest.json').read_text()) if (OUT/'manifest.json').exists() else {}
    known=sorted(set(previous.get('known',[])+[previous.get('previous',sha(source)),previous.get('after',sha(source))]))
    result=dict(before=sha(source),known=known,after=sha(data),lods=report)
    (OUT/'manifest.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

def install():
    r=json.loads((OUT/'manifest.json').read_text());live=DataFolder(root=GAME)
    original=live.data_path(REL).read_bytes();data=DataFolder(root=OUT/'stage').data_path(REL).read_bytes()
    assert sha(original) in [r['before'],r['after']]+r.get('known',[]);assert sha(data)==r['after']
    backup=DataFolder(root=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f'));backup.sync_data_file(REL,original)
    live.sync_data_file(REL,data);assert live.data_path(REL).read_bytes()==data
    print('Installed '+REL+'; other heads unchanged.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
    install() if args.apply else build()
