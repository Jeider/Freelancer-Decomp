"""Export/check only the offline far-LOD revision. No DATA/source integration."""
import copy, json, secrets, struct, sys
import numpy as np
from PIL import Image, ImageDraw
import rh_freighter_final as d
from rh_pir_elite_build import salt_tree
from rh_freighter_final_preview import view
from preview import render
f=d.f
OUT=d.OUT/'lod_refinement'
ATLAS='rh_pir_freighter_projection_lod'


def wire_lines(ns):
    libs={f.mesh.crc(p.split('/')[-2]):f.audit.decode(n.blob)[0] for p,n in f.mesh.walk(ns) if p.lower().endswith('/vmeshdata')}
    tr,_=f.audit.transforms(ns,('Sc_extend wing',0));out={}
    for file,name in f.component_map(ns).items():
        raw=f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'VMeshWire'),'VWireData').blob
        _,crc,bias,nv,ni,total=struct.unpack_from('<II4H',raw);ids=np.frombuffer(raw,'<u2',offset=16)
        r,t=tr[file.lower()];out[name]=libs[crc][ids+bias,:3].reshape(-1,2,3)@r.T+t
    return out


def add_roof_wire(ns):
    from rh_freighter_min_lod import roof_dividers
    before=wire_lines(ns);names=f.component_map(ns);file=next(k for k,v in names.items() if v=='Root')
    tr,_=f.audit.transforms(ns,('Sc_extend wing',0));r,t=tr[file.lower()]
    world=np.concatenate((before['Root'],roof_dividers()));local=(world-t)@r
    keys={}
    for p in local.reshape(-1,3):keys.setdefault(tuple(p.round(5)),len(keys))
    first=f.local_geometry(ns,0)[file][0];blob,v=f.mesh.pack([dict(first,unused=204,corners=first['corners'][:1])]);base=len(v)
    extra=np.zeros((len(keys),8),'<f4');extra[:,:3]=list(keys);extra[:,4]=1
    raw=bytearray(blob);struct.pack_into('<H',raw,14,base+len(extra));raw+=extra.tobytes()
    vname='rpf_roof_dividers.vms';f.mesh.child(ns[0],'VMeshLibrary').children.append(f.folder(vname,f.mesh.Node('VMeshData',bytes(raw))))
    ids=[keys[tuple(p.round(5))] for p in local.reshape(-1,3)]
    payload=struct.pack('<II4H',16,f.mesh.crc(vname),base,len(keys),len(ids),len(keys))+np.array(ids,'<u2').tobytes()
    f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'VMeshWire'),'VWireData').blob=payload
    after=wire_lines(ns)
    for name,a in before.items():assert np.allclose(a,after[name][:len(a)],atol=2e-5),name
    d.dump(OUT/'wire.json',dict(parts={k:dict(edges=len(v),world=v) for k,v in after.items()},added_roof_edges=len(roof_dividers()),
         existing_side_wire_preserved=True,static_extended=True,part_ownership_preserved=True))


def named(ns,lv):
    names=f.component_map(ns)
    return {names[k]:v for k,v in f.local_geometry(ns,lv).items()}


def signature(ns,lv):
    return {n:[(g['material'],g['corners'].tobytes()) for g in gs] for n,gs in named(ns,lv).items()}


def export():
    src=d.ASSETS/'rh_pir_freighter.cmp';header,ns=d.tree(src);before=copy.deepcopy(ns)
    levels=[json.loads((OUT/name).read_text()) for name in ('far_world.json','minimum_world.json')];names=f.component_map(ns)
    tr,_=f.audit.transforms(ns,('Sc_extend wing',0));lib=f.mesh.child(ns[0],'VMeshLibrary')
    replaced=[]
    for level,data in enumerate(levels,1):
        for file,name in names.items():
            r,t=tr[file.lower()];gs=[dict(g,material=g['material'] or f.mesh.crc(ATLAS),corners=np.array(g['corners'])) for g in data[name]]
            gs=f.base.world(gs,r.T,-r.T@t)
            ref=f.mesh.child(f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'MultiLevel'),'Level'+str(level)),'VMeshPart')
            old=f.mesh.child(ref,'VMeshRef');replaced.append(struct.unpack_from('<I',old.blob,4)[0])
            blob,v=f.mesh.pack(f.merge(gs));vname='rpf_lod'+str(level)+'_'+name+'.vms'
            lib.children.append(f.folder(vname,f.mesh.Node('VMeshData',blob)))
            old.blob=f.fresh_ref(vname,blob,v)
    add_roof_wire(ns)
    used={struct.unpack_from('<I',n.blob,4)[0] for p,n in f.mesh.walk(ns) if p.lower().endswith(('/vmeshref','/vwiredata'))}
    lib.children=[n for n in lib.children if f.mesh.crc(n.name) in used]
    salt=secrets.token_hex(6);mapping=salt_tree(ns,salt)
    target=OUT/'rh_pir_freighter.cmp';target.write_bytes(f.mesh.write_tree(header,ns))
    _,ns=d.tree(target)
    assert signature(before,0)==signature(ns,0)
    leaves=lambda n:{p:n.blob.hex() for p,n in f.mesh.walk([n])}
    for tag in ('Animation','Cons'):
        sub=lambda a:f.mesh.child(a[0],tag) if tag=='Animation' else f.mesh.child(f.mesh.child(a[0],'Cmpnd'),tag)
        assert leaves(sub(before))==leaves(sub(ns))
    oldhp=d.hardpoints(before,('Sc_extend wing',0));newhp=d.hardpoints(ns,('Sc_extend wing',0))
    assert oldhp.keys()==newhp.keys()
    for k,h in oldhp.items():
        assert h['leaves']==newhp[k]['leaves'] and h['owner']==newhp[k]['owner']
        assert np.allclose(h['position'],newhp[k]['position'],atol=1e-6)
    def wires(a):
        libs={f.mesh.crc(p.split('/')[-2]):n.blob for p,n in f.mesh.walk(a) if p.lower().endswith('/vmeshdata')}
        out={}
        for file,name in f.component_map(a).items():
            raw=f.mesh.child(f.mesh.child(f.mesh.child(a[0],file),'VMeshWire'),'VWireData').blob
            crc=struct.unpack_from('<I',raw,4)[0];out[name]=(raw[:4]+raw[8:],libs[crc])
        return out
    for name,record in wires(before).items():
        if name!='Root':assert record==wires(ns)[name],name
    mats=f.audit.material_table([d.MAT,d.ENV,d.ASSETS/'rh_pir_freighter_lods.mat']);maximum=0
    for p,n in f.mesh.walk(ns):
        assert n.name.lower() not in ('texture library','material library')
        if p.lower().endswith('/vmeshdata'):
            vs,gs,ids=f.audit.decode(n.blob);assert np.isfinite(vs).all() and len(vs)<65536 and len(ids)<65536
            maximum=max(maximum,len(vs));at=0
            for mid,lo,hi,num,_ in gs:
                assert mid in mats and num%3==0
                ii=ids[at:at+num]+lo;assert ii.min()>=lo and ii.max()<=hi<len(vs);at+=num
    for level,data in enumerate(levels,1):
        expected={n:d.packed(gs) for n,gs in data.items()};actual=d.world(ns,('Sc_extend wing',0),level)
        for name in expected:
            for g in expected[name]:
                mid=g['material'] or f.mesh.crc(ATLAS);other=next(a for a in actual[name] if a['material']==mid)
                assert np.allclose(g['corners'],other['corners'],atol=3e-5),(level,name)
    opened=copy.deepcopy(ns)
    for p,n in f.mesh.walk(opened):
        if p.lower().endswith('/cons/pris'):
            raw=bytearray(n.blob)
            for at in range(0,len(raw),208):
                vs=np.frombuffer(raw,'<f4',20,at+128).copy();vs[:3]+=vs[15:18];raw[at+128:at+208]=vs.tobytes()
            n.blob=bytes(raw)
    opened[0].children=[n for n in opened[0].children if n.name.lower()!='animation']
    osalt=secrets.token_hex(6);omap=salt_tree(opened,osalt)
    (OUT/'rh_pir_freighter_review_open.cmp').write_bytes(f.mesh.write_tree(header,opened))
    counts=lambda a:[sum(len(g['corners']) for gs in named(a,lv).values() for g in gs) for lv in range(3)]
    report=dict(source=str(src),source_sha256=f.digest(src),cmp_sha256=f.digest(target),before=counts(before),after=counts(ns),
                lod0_exact=True,second_lod_previous_1776=True,hardpoints=len(newhp),native_rig_animation_bytes_exact=True,
                existing_wire_lines_preserved=True,roof_wire_dividers_added=True,
                damage_and_collision='existing files unchanged',materials='existing external libraries; atlas unchanged',
                max_vertices=maximum,salt=salt,resources=mapping,review_salt=osalt,review_resources=omap,installed=False)
    d.dump(OUT/'validation.json',report)
    print('PASS',report['before'],'->',report['after'],flush=True)


def preview():
    mats=f.audit.material_table([d.MAT,d.ENV,d.ASSETS/'rh_pir_freighter_lods.mat'])
    _,old=d.tree(d.ASSETS/'rh_pir_freighter.cmp');_,new=d.tree(OUT/'rh_pir_freighter.cmp')
    variants=[(new,0,'LOD0: 26109'),(new,1,'LOD1: 1776'),(new,2,'LOD2: 494')]
    sheet=Image.new('RGB',(1800,1200),'#181d25');draw=ImageDraw.Draw(sheet)
    for col,(ns,lv,label) in enumerate(variants):
        gs=[g for groups in d.world(ns,('Sc_extend wing',0),lv).values() for g in groups]
        for row,cam in enumerate([(1,.65,-1),(1,-.7,1)]):
            sheet.paste(view(gs,mats,cam,600),(col*600,row*600));draw.text((col*600+15,row*600+15),label,fill='white')
    sheet.save(OUT/'comparison.png')
    sheet=Image.new('RGB',(1500,1000),'#181d25');draw=ImageDraw.Draw(sheet)
    for row,(ns,lv,label) in enumerate(variants[1:]):
        gs=[g for groups in d.world(ns,('Sc_extend wing',0),lv).values() for g in groups]
        p=d.points(gs);center=(p.min(0)+p.max(0))/2;radius=np.linalg.norm(p-center,axis=1).max()*1.03
        for col,cam in enumerate([(1,0,0),(0,1,.01),(1,.65,-1)]):
            sheet.paste(render(gs,mats,center,radius,cam,500,'wire'),(col*500,row*500))
            draw.text((col*500+15,row*500+15),label,fill='white')
    sheet.save(OUT/'mesh_comparison.png')
    sheet=Image.new('RGB',(1200,600),'#181d25');draw=ImageDraw.Draw(sheet)
    for col,(pose,label) in enumerate([(None,'Folded'),(('Sc_rh_freighter',1),'Cargo open')]):
        gs=[g for groups in d.world(new,pose,2).values() for g in groups]
        sheet.paste(view(gs,mats,(1,.8,-.6),600),(col*600,0));draw.text((col*600+15,15),label,fill='white')
    sheet.save(OUT/'mechanisms.png')
    sheet=Image.new('RGB',(768,320),'#181d25');draw=ImageDraw.Draw(sheet)
    for col,(ns,lv,label) in enumerate(variants):
        gs=[g for groups in d.world(ns,('Sc_extend wing',0),lv).values() for g in groups]
        for row,cam in enumerate([(1,.65,-1),(1,0,0)]):
            # Same scale; ordinary distant-size render, without upscaling.
            sheet.paste(view(gs,mats,cam,192),(col*256+32,row*160-10))
        draw.text((col*256+20,4),label,fill='white')
    sheet.save(OUT/'distance_comparison.png')
    sheet=Image.new('RGB',(1500,1000),'#181d25');draw=ImageDraw.Draw(sheet)
    colors={'Root':'#b9d5dd','port_engine_lod1':'#ffb567','starboard_engine_lod1':'#ffb567',
            'rh_port_side_lod1':'#73d899','rh_star_side_lod1':'#73d899'}
    allp=np.concatenate([a.reshape(-1,3) for a in wire_lines(new).values() if len(a)])
    center=(allp.min(0)+allp.max(0))/2
    for row,(ns,label) in enumerate([(old,'BEFORE'),(new,'ROOF DIVIDERS')]):
        for col,cam in enumerate([(1,0,0),(.01,1,0),(1,.65,-1)]):
            forward=np.array(cam,float);forward/=np.linalg.norm(forward)
            right=np.cross([0,1,0],forward);right/=np.linalg.norm(right);up=np.cross(forward,right)
            for part,lines in wire_lines(ns).items():
                if not len(lines):continue
                p=lines-center;xy=np.stack((p@right,-p@up),axis=-1)*18+[col*500+250,row*500+250]
                for a,b in xy:draw.line([tuple(a),tuple(b)],fill=colors.get(part,'white'),width=1)
            draw.text((col*500+15,row*500+15),label+' / '+['SIDE','TOP','PERSPECTIVE'][col],fill='white')
    sheet.save(OUT/'wire_comparison.png')
    print('PREVIEWS READY',flush=True)


if __name__=='__main__':
    if '--preview' in sys.argv:preview()
    else:export()
