"""Assemble isolated ship/damage assets with fresh private identities."""
import collections,copy,json,secrets,struct,subprocess,sys,io
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from scipy.spatial import ConvexHull
import rh_freighter_final as d
import rh_concept_b_final_damage as damage
from rh_pir_elite_build import salt_tree
f=d.f
ATLAS='rh_pir_freighter_projection_lod'

def outline_lines(nodes):
    source=json.loads((d.PREVIOUS/'mechanical_geometry.json').read_text());objects={o['name']:o for o in source['objects']}
    lines=collections.defaultdict(list)
    from rh_freighter_min_lod import roof_dividers
    lines['Root'].extend(roof_dividers())
    def loop(owner,ps):lines[owner].extend(np.stack((ps,np.roll(ps,-1,axis=0)),axis=1))
    def projected(owner,ob,axis,side=None):
        p=d.points(ob['groups']);axes=[i for i in range(3) if i!=axis]
        if side is not None:p=p[p[:,axis]*side>0]
        unique={}
        for v in p:
            k=tuple(v[axes].round(4))
            if k not in unique or (v[axis]*(side or 1)>unique[k][axis]*(side or 1)):unique[k]=v
        keys=list(unique);xy=np.array(keys);ids=ConvexHull(xy).vertices
        loop(owner,np.array([unique[keys[i]] for i in ids]))
    for name in ('Original cockpit - immutable','Continuous hull - stepped belly and low foredeck rise'):
        for side in (-1,1):projected('Root',objects[name],0,side)
        projected('Root',objects[name],1)
    for side in (-1,1):
        engine='port_engine_lod1' if side<0 else 'starboard_engine_lod1'
        angles=np.deg2rad(15+np.arange(12)*30);rings=[]
        for z,w,h in ((9.90,1.29,1.24),(12.158,.98,.94)):
            ring=np.column_stack((side*1.8+w*np.cos(angles),-.28+h*np.sin(angles),np.full(12,z)))
            loop(engine,ring);rings.append(ring)
        for i in (1,4,7,10):lines[engine].append([rings[0][i],rings[1][i]])
        for prefix in ('Lower diagonal hull','Stepped circular shoulder'):
            name=f'{prefix} {side:+}'
            projected('Root',objects[name],0,side)
        # Reconstruct the actual authored panel perimeter, excluding vent vanes,
        # sockets, triangular diagonals and decorative recess boundaries.
        from rh_freighter_uv_b3 import UP_BACK,UP_FACE
        owner='rh_port_side_lod1' if side<0 else 'rh_star_side_lod1'
        a=np.column_stack((np.full(len(UP_BACK),side*2.62),UP_BACK[:,1],UP_BACK[:,0]))
        b=np.column_stack((np.full(len(UP_FACE),side*3.50),UP_FACE[:,1],UP_FACE[:,0]))
        loop(owner,a);loop(owner,b)
        lines[owner].extend(np.array([[a[i],b[i]] for i in (0,2,3,6,8)]))
        for index in (1,2,3):
            ob=objects[f'New transverse unit {side:+} {index}'];p=d.points(ob['groups']);outer=p[p[:,0]*side>abs(p[:,0]).max()-.001]
            coords=np.unique(outer,axis=0);ids=ConvexHull(coords[:,[2,1]]).vertices
            loop(owner,coords[ids])
    tr,_=f.audit.transforms(nodes,('Sc_extend wing',0));names=f.component_map(nodes)
    result={}
    for file,name in names.items():
        r,t=tr[file.lower()];raw=lines[name];unique={}
        for line in raw:
            if np.linalg.norm(line[1]-line[0])<.06:continue
            key=tuple(sorted(tuple(v.round(4)) for v in line));unique[key]=line
        result[name]=(np.array(list(unique.values()))-t)@r if unique else []
    return result

def atlas():
    raw=Image.new('RGB',(4096,4096),(100,95,85))
    for views in d.read('projectors.json').values():
        for v in views:
            a=np.array(Image.open(d.OUT/v['image']).convert('RGBA'));valid=a[:,:,3]>100
            assert valid.any(),v['image']
            nn=distance_transform_edt(~valid,return_distances=False,return_indices=True)
            raw.paste(Image.fromarray(a[nn[0],nn[1],:3]),tuple(k*512 for k in v['tile']))
    path=d.OUT/(ATLAS+'.png');buffer=io.BytesIO();raw.resize((2048,2048),Image.Resampling.LANCZOS).save(buffer,format='PNG')
    if not path.exists() or path.read_bytes()!=buffer.getvalue():path.write_bytes(buffer.getvalue())
    exe=d.ROOT/'out/ship_design/tool_cache/lod_materials/lod_dds.exe';dds=path.with_suffix('.dds')
    if '--dds-ready' in sys.argv:
        assert dds.stat().st_mtime>=path.stat().st_mtime
        rawdds=dds.read_bytes();assert rawdds[:4]==b'DDS ' and rawdds[84:88]==b'DXT1' and struct.unpack_from('<I',rawdds,28)[0]==12
        gpu_check='PASS standalone D3D9: 12 DXT1 mips; full blocks <=1, partial-block error <=3'
    else:
        r=subprocess.run([str(exe),str(path),str(dds)],capture_output=True,text=True,check=True);gpu_check=r.stdout.strip()
    header,ns=d.tree(d.MAT);mat=f.folder(ATLAS,f.textnode('Type','DcDt'),f.mesh.Node('Dc',np.ones(3,'<f4').tobytes()),f.textnode('Dt_name',ATLAS+'.tga'))
    ns[0].children=[f.folder('Material library',mat),f.folder('Texture library',f.folder(ATLAS+'.tga',f.mesh.Node('MIPS',dds.read_bytes())))]
    target=d.ASSETS/'rh_pir_freighter_lods.mat';target.write_bytes(f.mesh.write_tree(header,ns))
    d.dump(d.OUT/'atlas.json',dict(material=ATLAS,material_crc=f.mesh.crc(ATLAS),sha256=f.digest(target),gpu_check=gpu_check,size=2048,source_png_sha256=f.digest(path)))

def add_damage_points(nodes):
    names=f.component_map(nodes);tr,_=f.audit.transforms(nodes,('Sc_extend wing',0));rootfile=next(k for k,v in names.items() if v=='Root')
    root=f.mesh.child(nodes[0],rootfile);fixed=f.mesh.child(f.mesh.child(root,'Hardpoints'),'Fixed');r,t=tr[rootfile.lower()];result={}
    for zone,part in d.PARTS.items():
        side=-1 if zone.startswith('port') else 1
        anchor=np.array([side*1.8,-.28,9.0]) if 'engine' in zone else np.array([side*3.,1.,.5])
        name='DpRPF_'+zone
        assert name.lower() not in d.hardpoints(nodes)
        fixed.children.append(f.folder(name,f.mesh.Node('Position',np.array(r.T@(anchor-t),'<f4').tobytes()),
            f.mesh.Node('Orientation',np.array(r.T,'<f4').tobytes())))
        native_zone={'port_engine':'portengine','starboard_engine':'starengine'}.get(zone,zone)
        result[zone]=dict(hardpoint=name,part=part,position=anchor,orientation=np.eye(3),archetype='rh_pir_freighter_dmg_'+native_zone+'_cap')
    return result

def simple(zone,groups,salt):
    # Standalone surviving assembly replacement; never a flying debris cap.
    header,ns=d.tree(d.SOURCE/('rh_pir_freighter_dmg_'+zone+'.3db'));root=ns[0];root.children=[]
    lib=f.folder('VMeshLibrary');ml=f.folder('MultiLevel',f.mesh.Node('Switch2',np.array([0,10000],'<f4').tobytes()))
    blob,v=f.mesh.pack(f.merge(groups));vname='rpf_damage_'+salt+'.vms'
    lib.children.append(f.folder(vname,f.mesh.Node('VMeshData',blob)))
    ml.children.append(f.folder('Level0',f.folder('VMeshPart',f.mesh.Node('VMeshRef',f.fresh_ref(vname,blob,v)))))
    root.children=[lib,ml,f.folder('Hardpoints',f.folder('Fixed',f.folder('DpConnect',f.mesh.Node('Position',np.zeros(3,'<f4').tobytes()),f.mesh.Node('Orientation',np.eye(3,dtype='<f4').tobytes()))))]
    path=d.ASSETS/('rh_pir_freighter_dmg_'+zone+'.3db');path.write_bytes(f.mesh.write_tree(header,ns))
    triangles=np.concatenate([g['corners'][...,:3] for g in groups]);lo=triangles.min((0,1));hi=triangles.max((0,1))
    cuts=np.linspace(lo[2]-.001,hi[2]+.001,5)
    hs=damage.hull_regions(triangles,0,[[(2,a,b)] for a,b in zip(cuts,cuts[1:])]);surface,lo,hi=damage.sur.encode_surface(hs)
    path.with_suffix('.sur').write_bytes(b'vers'+struct.pack('<fII',2.,0,3)+b'!fxd'+b'exts'+struct.pack('<6f',*lo,*hi)+b'surf'+struct.pack('<I',len(surface))+surface)
    return dict(file=path.name,sha256=f.digest(path),triangles=sum(len(g['corners']) for g in groups),private_vms=vname)

def wire(nodes,flight):
    """Own silhouette/crease edges per part, no triangulation or UV seam lines."""
    names=f.component_map(nodes);tr,_=f.audit.transforms(nodes,('Sc_extend wing',0));local=f.local_geometry(nodes,2)
    report={};lib=f.mesh.child(nodes[0],'VMeshLibrary')
    contours=outline_lines(nodes)
    for file,name in names.items():
        part=f.mesh.child(nodes[0],file);part.children=[n for n in part.children if n.name.lower()!='vmeshwire']
        g=local[file][0];blob,v=f.mesh.pack([dict(g,unused=204,corners=g['corners'][:1])]);base=len(v)
        if name=='Root' or 'side_lod1' in name or 'engine_lod1' in name:lines=contours[name]
        elif name=='Baydoor_lod1' or name=='glass_lod1' or '_btn_' in name:lines=[]
        else:
            # Creases only on simplified silhouette, explicitly remove internal
            # triangulation and UV duplicates. Stable part owns its own lines.
            blob2,v2=f.mesh.pack(f.merge(local[file]));bw=f.clean_feature_wire(blob2,0,angle=40)
            ids=np.frombuffer(bw,'<u2',offset=16);lines=v2[ids,:3].reshape(-1,2,3)
            lines=[a for a in lines if np.linalg.norm(a[1]-a[0])>.28]
        vertices={}
        for a in lines:
            for p in a:vertices.setdefault(tuple(p.round(5)),len(vertices))
        extra=np.zeros((len(vertices),8),'<f4');extra[:,:3]=list(vertices) if vertices else np.empty((0,3));extra[:,4]=1
        raw=bytearray(blob);struct.pack_into('<H',raw,14,base+len(extra));raw+=extra.tobytes()
        vname='rpf_wire_'+name+'.vms';lib.children.append(f.folder(vname,f.mesh.Node('VMeshData',bytes(raw))))
        ids=[vertices[tuple(p.round(5))] for line in lines for p in line]
        payload=struct.pack('<II4H',16,f.mesh.crc(vname),base,len(vertices),len(ids),len(vertices))+np.array(ids,'<u2').tobytes()
        part.children.append(f.folder('VMeshWire',f.mesh.Node('VWireData',payload)))
        r,t=tr[file.lower()];world=np.array(lines)@r.T+t if len(lines) else []
        report[name]=dict(edges=len(lines),world=world)
    d.dump(d.OUT/'wire.json',dict(parts=report,pose='flight static; extended button caps belong to their detachable panel, their animated child wires are empty',per_part=True))

def build():
    header,ns=d.tree(d.OUT/'authoring_animated.cmp');before=copy.deepcopy(ns);names=f.component_map(ns)
    tr,_=f.audit.transforms(ns,('Sc_extend wing',0));levels=[f.local_geometry(ns)];atlas_crc=f.mesh.crc(ATLAS)
    # User accepted the former 1776-triangle far proxy as the SECOND LOD.
    # The third is now an independently authored <=500-triangle silhouette.
    # Run outside Blender: the polygon builder uses the host SciPy environment.
    import rh_freighter_min_lod as minimum
    minimum.main()
    distances=[json.loads((minimum.OUT/name).read_text()) for name in ('far_world.json','minimum_world.json')]
    d.dump(d.OUT/'lod_world.json',distances)
    stats=d.read('lod_generation.json')
    stats.update(total=[sum(len(g['corners']) for gs in lv.values() for g in gs) for lv in distances],
        parts=[dict(part=n,level=i+1,triangles=sum(len(g['corners']) for g in gs)) for i,lv in enumerate(distances) for n,gs in lv.items()])
    d.dump(d.OUT/'lod_generation.json',stats)
    for level in distances:
        parts={}
        for file,name in names.items():
            gs=[dict(g,material=g['material'] or atlas_crc,corners=np.array(g['corners'],float)) for g in level[name]]
            r,t=tr[file.lower()];parts[file]=f.base.world(gs,r.T,-r.T@t)
        levels.append(parts)
    f.write_geometry(ns,levels)
    for file in names:f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'MultiLevel'),'Switch2').blob=np.array([0,250,750,10000],'<f4').tobytes()
    anchors=add_damage_points(ns);damages=[];salt=secrets.token_hex(6)
    for zone,gs in d.read('damage_world.json').items():
        gs=d.packed(gs);local=f.base.world(gs,np.eye(3),-anchors[zone]['position']);record=simple(zone,local,salt+'_'+str(len(damages)))
        damages.append(dict(zone=zone,**anchors[zone],**record))
    wire(ns,d.world(ns,('Sc_extend wing',0)));mapping=salt_tree(ns,salt)
    dest=d.ASSETS/'rh_pir_freighter.cmp';dest.write_bytes(f.mesh.write_tree(header,ns))
    # Static viewer copy; animated zero pose and source mechanisms are preserved.
    opened=copy.deepcopy(ns)
    for path,node in f.mesh.walk(opened):
        if path.lower().endswith('/cons/pris'):
            raw=bytearray(node.blob)
            for at in range(0,len(raw),208):
                values=np.frombuffer(raw,'<f4',20,at+128).copy();values[:3]+=values[15:18];raw[at+128:at+208]=values.tobytes()
            node.blob=bytes(raw)
    opened[0].children=[n for n in opened[0].children if n.name.lower()!='animation']
    osalt=secrets.token_hex(6);omapping=salt_tree(opened,osalt)
    (d.OUT/'rh_pir_freighter_review_open.cmp').write_bytes(f.mesh.write_tree(header,opened))
    old=d.hardpoints(before,('Sc_extend wing',0));new=d.hardpoints(ns,('Sc_extend wing',0))
    for k,h in old.items():
        assert np.allclose(new[k]['position'],h['position'],atol=3e-5),k
        assert np.allclose(new[k]['orientation'],h['orientation'],atol=3e-5),k
        assert new[k]['owner']==h['owner'] and new[k]['leaves']==h['leaves'],k
    d.dump(d.OUT/'build.json',dict(salt=salt,resources=mapping,review_salt=osalt,review_resources=omapping,
        damage=damages,hardpoints=len(new),user_hardpoints_preserved=len(old),cmp_sha256=f.digest(dest),
        lod_triangles=[sum(len(g['corners']) for gs in lv.values() for g in gs) for lv in levels],external_materials=True,installed=False))
    print('OFFLINE SHIP ASSEMBLED',dest)

if __name__=='__main__':atlas();build()
