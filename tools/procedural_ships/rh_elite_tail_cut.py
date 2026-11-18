"""Correction: the hidden aft carrier is part of the detachable tail, offline."""
import copy
import collections
import json
import secrets
import struct
import sys
import numpy as np
import rh_elite_torn_damage as d
from rh_pir_elite_refine_damage import decoded_wire

OLD=d.OUT
OUT=OLD.parent/'damage_05'
LOW,HIGH=-.78,3.30


def configure():
    d.OUT=OUT;d.ASSETS=OUT/'assets'


def prepare():
    old=json.loads((OLD/'export.json').read_text())
    assert d.f.digest(OLD/'assets/rh_pir_elite.cmp')==old['cmp_sha256'],'User CMP edits must be preserved'
    OUT.mkdir(exist_ok=True);(OUT/'assets').mkdir(exist_ok=True)
    data=json.loads((OLD/'input.json').read_text());parts=data['parts'];root=d.r.flatten_groups(parts['Root'])
    data['base_parts']=copy.deepcopy(parts)
    comp=next(c for c in d.r.components(root) if c['triangles']==395)
    data['frame_source']=d.prev.m.take(root,comp);data['root_without_frame']=d.prev.m.without(root,[comp])
    data['split_height']=[LOW,HIGH]
    d.save('input.json',data)
    d.save('damage_world.json',json.loads((OLD/'damage_world.json').read_text()))
    d.save('damage_geometry_check.json',json.loads((OLD/'damage_geometry_check.json').read_text()))
    sources=json.loads((OLD/'source_manifest.json').read_text());sources['files'][str(OLD/'assets/rh_pir_elite.cmp')]=old['cmp_sha256']
    sources['correction']='Move rear upright from Root to Tail and open its center on damage'
    d.save('source_manifest.json',sources)
    print('PREPARED tail ownership correction',flush=True)


def wire():
    data=json.loads((OUT/'input.json').read_text());ns=d.r.load(d.SOURCE)[1]
    tr,_=d.f.audit.transforms(ns,('Sc_extend wing',0));lines=decoded_wire(ns,tr)
    root=[];moved=[]
    for a,c in lines['Root']:
        cuts=[0.,1.]
        if abs(c[1]-a[1])>1e-9:cuts+=[v for v in ((LOW-a[1])/(c[1]-a[1]),(HIGH-a[1])/(c[1]-a[1])) if 0<v<1]
        cuts=sorted(cuts)
        for lo,hi in zip(cuts,cuts[1:]):
            p=a+(c-a)*lo;q=a+(c-a)*hi;mid=(p+q)/2
            target=moved if LOW<mid[1]<HIGH and mid[2]>7.0 and max(abs(p[0]),abs(q[0]))<.521 else root
            target.append([p,q])
    assert moved,'No rear frame wire transferred'
    data['wire_override']={'Root':root,'Rh_tail_lod1':list(lines['Rh_tail_lod1'])+moved}
    data['ownership_split']['wire_segments_transferred']=len(moved);d.save('input.json',data)


def check():
    from scipy.spatial import ConvexHull
    d.validate()
    source=d.r.load(OLD/'assets/rh_pir_elite.cmp')[1];after=d.r.load(d.ASSETS/'rh_pir_elite.cmp')[1]
    assert d.r.hp_bytes(source)==d.r.hp_bytes(after),'Hardpoints changed'
    data=json.loads((OUT/'input.json').read_text());parts=d.r.world(after)
    key=lambda mid,t:(mid,tuple(np.round(t,5).ravel()))
    available=collections.Counter(key(g['material'],t) for g in parts['Root'] for t in g['corners'])
    protected=d.r.flatten_groups(data['root_without_frame'])
    assert all(available[key(g['material'],t)] for g in protected for t in g['corners'])
    old=json.loads((OLD/'review_data.json').read_text())['damage'];new=json.loads((OUT/'review_data.json').read_text())['damage']
    for zone in d.ZONES:
        if zone=='tail':continue
        for a,c in zip(old[zone],new[zone]):assert a['material']==c['material'] and np.array_equal(a['corners'],c['corners'])
    # Test collision after removal of Tail and its equipment, plus the surviving
    # damage SUR. Split the two outer cheeks so convexification cannot close it.
    coll=json.loads((OUT/'collision_check.json').read_text());exclude={d.f.mesh.crc('Rh_tail_lod1'),d.f.mesh.crc('HpMount')}
    exclude|={d.f.mesh.crc(h['name']) for h in coll['equipment'] if h['owner']=='Rh_tail_lod1'}
    hulls=[]
    for pid,chunks in d.sur_parts((d.ASSETS/'rh_pir_elite.sur').read_bytes()):
        if pid!=d.f.mesh.crc('Root'):continue
        for tag,blob in chunks:
            if tag==b'surf':hulls += [p for client,p in d.read_hulls(blob) if client not in exclude]
    hp=d.world_hp(after)['dptail'];hr,ht=np.array(hp['orientation']),np.array(hp['position'])
    for _,chunks in d.sur_parts((d.ASSETS/'rh_pir_elite_dmg_tail.sur').read_bytes()):
        for tag,blob in chunks:
            if tag==b'surf':hulls += [p@hr.T+ht for _,p in d.read_hulls(blob)]
    eq=[ConvexHull(p).equations for p in hulls]
    def hit(p,direction,limit):
        for q in eq:
            lo,hi=0.,limit;start=q[:,:3]@p+q[:,3];slope=q[:,:3]@direction
            for a,b in zip(start,slope):
                if abs(b)<1e-10:
                    if a>1e-5:hi=-1;break
                elif b>0:hi=min(hi,-a/b)
                else:lo=max(lo,-a/b)
            if hi>=lo:return True
        return False
    rays=[]
    for x in (-.35,0,.35):
        for y in (.25,1.65,2.25):
            assert not hit(np.array([x,y,10.]),np.array([0,0,-1.]),2.02),(x,y,'collision blocks hole')
            rays.append([x,y])
    stats=dict(cmp_sha256=d.f.digest(d.ASSETS/'rh_pir_elite.cmp'),all_hp_bytes_unchanged_from_damage04=True,
        protected_root_triangles=sum(len(g['corners']) for g in protected),other_four_wounds_unchanged=True,
        opening_collision_rays_clear=rays,frame_transfer=data['ownership_split'])
    d.save('tail_transfer_check.json',stats)
    print('TAIL TRANSFER VERIFIED: intact HPs, protected Root, unchanged four wounds, clear SUR opening',flush=True)


def editor():
    from PIL import Image,ImageDraw
    from preview import render
    header,ns=d.r.load(d.ASSETS/'rh_pir_elite.cmp');parts=d.r.world(ns);names=d.f.component_map(ns)
    wound=d.r.flatten_groups(json.loads((OUT/'review_data.json').read_text())['damage']['tail'])
    root=d.f.merge(parts['Root']+wound);tailfile=next(k for k,v in names.items() if v=='Rh_tail_lod1')
    rootfile=next(k for k,v in names.items() if v=='Root');cmpnd=d.f.mesh.child(ns[0],'Cmpnd')
    ns[0].children.remove(d.f.mesh.child(ns[0],tailfile))
    cmpnd.children=[n for n in cmpnd.children if n.name=='Cons' or d.f.mesh.string(d.f.mesh.child(n,'Object name').blob)!='Rh_tail_lod1']
    blob,verts=d.f.mesh.pack(root);vn='tail_only_review.vms';lib=d.f.mesh.child(ns[0],'VMeshLibrary')
    lib.children.append(d.f.folder(vn,d.f.mesh.Node('VMeshData',blob)))
    ref=d.f.mesh.child(d.f.mesh.child(d.f.mesh.child(d.f.mesh.child(d.f.mesh.child(ns[0],rootfile),'MultiLevel'),'Level0'),'VMeshPart'),'VMeshRef')
    ref.blob=d.f.fresh_ref(vn,blob,verts)
    tr,_=d.f.audit.transforms(ns,('Sc_extend wing',0));fixed=b''
    for file,name in d.f.component_map(ns).items():
        if name=='Root':continue
        rot,t=tr[file.lower()];fixed+=d.owner_bytes('Root')+d.owner_bytes(name)+np.r_[t,rot.ravel()].astype('<f4').tobytes()
    d.f.mesh.child(cmpnd,'Cons').children=[d.f.mesh.Node('Fix',fixed)];ns[0].children=[n for n in ns[0].children if n.name!='Animation']
    used={struct.unpack_from('<I',n.blob,4)[0] for p,n in d.f.mesh.walk(ns) if p.lower().endswith(('/vmeshref','/vwiredata'))}
    lib.children=[n for n in lib.children if d.f.mesh.crc(n.name) in used]
    salt=secrets.token_hex(6);resources=d.b.salt_tree(ns,salt);dest=OUT/'rh_pir_elite_tail_damage_open.cmp'
    dest.write_bytes(d.f.mesh.write_tree(header,ns))
    loaded=d.r.world(d.r.load(dest)[1],None);assert 'Rh_tail_lod1' not in loaded
    for name,gs in loaded.items():
        expected=root if name=='Root' else parts[name]
        for a,c in zip(d.f.merge(gs),d.f.merge(expected)):assert a['material']==c['material'] and np.allclose(a['corners'],c['corners'],atol=4e-6)
    d.save('tail_editor_check.json',dict(sha256=d.f.digest(dest),salt=salt,resources=resources,reopened=True))
    sheet=Image.new('RGB',(1700,850));draw=ImageDraw.Draw(sheet)
    for i,folder in enumerate((OLD,OUT)):
        sheet.paste(Image.open(folder/'tail_rear.png'),(850*i,0));draw.text((20+850*i,20),'BEFORE' if i==0 else 'AFTER - REAR CARRIER DETACHES',fill='white')
    sheet.save(OUT/'tail_comparison.png')
    print('TAIL-ONLY EDITOR CMP and matched comparison ready',flush=True)


def main():
    configure();action=sys.argv[1]
    if action=='prepare':prepare()
    elif action=='export':wire();d.export()
    elif action=='check':check()
    elif action=='editor':editor()
    else:getattr(d,action)()


if __name__=='__main__':main()
