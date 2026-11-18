"""Offline RH B assembly from the user's frozen hardpoint-edited CMP."""
import copy
import hashlib
import json
import re
from pathlib import Path
import struct as S
import numpy as np
from scipy.spatial import ConvexHull
import rh_concept_b_final as f
import rh_concept_b_final_damage as damage
import rh_concept_b_hp_prototype as hp
from rh_concept_b_engine_shell import rebuild_engines
from rh_concept_b_tail_prototype import ORIGINAL,ORIGINAL_HASH,world_parts

OUT=f.OUT.parent/'final_v2'
DEST=OUT/'rh_concept_b.cmp'
SOURCE=OUT/'user_source.cmp'
PANEL=hp.PANEL
ZONES={'Rh_port_wing_lod1':'PortWing','Rh_starboard_wing_lod1':'StarboardWing',
       'Rh_port_engine_lod1':'PortEngine','Rh_starboard_engine_lod1':'StarboardEngine',
       'Rh_tail_lod1':'Tail'}


def dump(name,data):
    (OUT/name).write_text(json.dumps(data,default=hp.serial,indent=2),encoding='utf8')


def rotation(axis,angle):
    a=np.array(axis,float);a/=np.linalg.norm(a);x,y,z=a
    cross=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)*np.cos(angle)+(1-np.cos(angle))*np.outer(a,a)+np.sin(angle)*cross


def fold_rest(nodes):
    records={};rev=f.mesh.child(f.mesh.child(f.mesh.child(nodes[0],'Cmpnd'),'Cons'),'Rev')
    raw=bytearray(rev.blob)
    for at in range(0,len(raw),208):
        name=f.mesh.string(raw[at+64:at+128])
        if '_wing_' not in name.lower():continue
        v=np.frombuffer(raw,'<f4',20,at+128);offset=float(f.FOLD)
        v[6:15]=(rotation(v[15:18],offset)@v[6:15].reshape(3,3)).ravel()
        v[18:20]-=offset;records[name.lower()]=offset
    rev.blob=bytes(raw)
    scripts=f.mesh.child(f.mesh.child(nodes[0],'Animation'),'Script');channels=0
    for script in scripts.children:
        for joint in script.children:
            child=f.mesh.string(f.mesh.child(joint,'Child name').blob).lower()
            if child not in records:continue
            frames=f.mesh.child(f.mesh.child(joint,'Channel'),'Frames')
            values=np.frombuffer(frames.blob,'<f4').reshape(-1,2).copy()
            values[:,1]-=records[child];frames.blob=values.tobytes();channels+=1
    return dict(wing_rest_degrees=62,rebased_channels=channels)


def hull_group(points,material=PANEL):
    h=damage.sur.make_hull(points,0)
    tris=[]
    for face in h.faces:
        p=h.points[face];n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n)
        axes=np.argsort(abs(n))[:2]
        t=np.zeros((3,8));t[:,:3]=p;t[:,3:6]=n
        t[:,6:8]=.55+(p[:,axes]-.5*(p[:,axes].max(0)+p[:,axes].min(0)))*.08
        tris.append(t)
    return dict(material=material,corners=np.array(tris),unused=204)


def clip_polygon(poly,axis,bound,greater):
    return np.array(damage.sur.clip(np.array(poly),axis,bound,greater))


def solid_frame_polygon(poly,shift):
    b=f.b.Builder();b.part='tail';b.sharp_solid(np.array(poly),-1.32,1.32)
    return f.base.world(b.groups(),np.eye(3),shift)


def solid_lod(nodes,local,shift,sides=20):
    tr,_=f.audit.transforms(nodes);names=f.component_map(nodes);result={};pieces={}
    for file,groups in local.items():
        name=names[file];world=f.base.world(groups,*tr[file.lower()]);allp=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in world])
        chunks=[]
        if name=='Root':
            # Fill technological recesses with a small number of coherent solids.
            # Retain the large negative space of the authored C frame.
            for lo,hi in ((-5.7,-2.1014),(-2.1016,-.0999),(-.1001,6.501)):
                clipped=f.clip_groups(f.clip_groups(world,2,lo+shift[2],True),2,hi+shift[2],False)
                if lo>-.2:
                    # The forward tip of the upper C frame overlaps this Z
                    # range. It must not stretch the body hull up to the frame.
                    clipped=f.clip_groups(clipped,1,3.6001+shift[1],False)
                    clipped=f.clip_groups(f.clip_groups(clipped,0,-2.0501,True),0,2.0501,False)
                pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in clipped])
                chunks.append(hull_group(pts))
            pixels=[[214,16],[148,16],[95,48],[95,124],[123,153],[207,153],
                    [207,133],[140,133],[116,112],[116,59],[154,36],[214,36]]
            poly=f.b.old.yz(pixels)
            for bound,greater in ((f.TAIL_CUT,False),(f.TAIL_TOP,True)):
                cut=clip_polygon(poly,0,bound,greater)
                chunks.extend(solid_frame_polygon(cut,shift))
            center=f.b.old.point(0,[175,86])+shift
            angle=(np.arange(sides)+.5)*2*np.pi/sides
            yz=center[1:]+2.01*np.column_stack((np.cos(angle),np.sin(angle)))
            pts=np.concatenate([np.column_stack((np.full(sides,x),yz)) for x in (-1.04,1.04)])
            chunks.append(hull_group(pts))
            # Three low-detail structural spokes, without drum-face recesses.
            for pix0,pix1 in (([175,49],[175,35]),([175,122],[175,135]),([139,86],[110,86])):
                b=f.b.Builder();b.part='tail';b.beam(f.b.old.point(0,pix0),f.b.old.point(0,pix1),.40,.48)
                chunks.extend(f.base.world(b.groups(),np.eye(3),shift))
        elif '_tail_' in name.lower():
            # Main upright/hatch and each native pylon remain separate solids.
            middle=allp[abs(allp[:,0])<1.321]
            chunks.append(hull_group(middle))
            source=json.loads((f.OUT.parent/'tail_prototype_01/prototype_data.json').read_text())
            for entry in source['objects'][1:]:
                points=np.concatenate([np.array(g['corners'])[...,:3].reshape(-1,3) for g in entry['groups']])+shift
                chunks.append(hull_group(points))
        elif '_engine_' in name.lower():
            # Entire external envelope; nozzle/old wing notch cannot make wire lines.
            r,t=tr[file.lower()]
            pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in groups])
            pts=pts[pts[:,1]<.751]
            chunks.append(hull_group(pts@r.T+t))
        elif '_glass_' in name.lower() or name.lower().startswith('baydoor'):
            chunks=world
        else:chunks=[hull_group(allp)]
        pieces[file]=chunks
        r,t=tr[file.lower()];result[file]=f.base.world(chunks,r.T,-r.T@t)
    return result,pieces


def add_chin(local,root,shift):
    assert f.digest(ORIGINAL)==ORIGINAL_HASH
    original=world_parts(ORIGINAL)[1]['Root'];selected=[]
    for g in original:
        if g['material']!=PANEL:continue
        a=g['corners'];keep=(a[...,2].max(1)<-4.79)&(a[...,1].min(1)<-1.742)
        if keep.any():selected.append(dict(g,corners=a[keep].copy()))
    chin=f.clip_groups(selected,1,-1.741818,False)
    added=f.base.world(chin,np.eye(3),shift+np.array([0,.591818,2.7]))
    local[root]=f.merge(local[root]+added)
    return dict(original_triangles=sum(len(g['corners']) for g in chin),
                original_uv_preserved=True,weapon05_06_positions_preserved=True)


def unique_damage(nodes,descriptions):
    names=f.component_map(nodes);changes=[]
    for file,name in names.items():
        if name not in ZONES:continue
        part=f.mesh.child(nodes[0],file)
        fixed=f.mesh.child(f.mesh.child(part,'Hardpoints'),'Fixed')
        node=f.mesh.child(fixed,'DpBreak');new='DpRHB'+ZONES[name]+'Debris';node.name=new
        desc=next(d for d in descriptions if d['part']==name);desc['debris_hardpoint']=new
        changes.append(dict(owner=name,before='DpBreak',after=new))
    return changes


def write_config(descriptions):
    damage.OUT=OUT
    damage.config(descriptions)
    path=OUT/'shiparch_fragment.ini'
    sections=re.split(r'(?=^\[)',path.read_text(),flags=re.M)
    by_part={d['part'].lower():d for d in descriptions}
    for i,section in enumerate(sections):
        if not section.lower().startswith('[collisiongroup]'):continue
        part=re.search(r'^obj\s*=\s*(.+)$',section,re.M).group(1).strip().lower()
        d=by_part[part]
        sections[i]=re.sub(r'^group_dmg_hp\s*=.*$',
            'group_dmg_hp = '+d['debris_hardpoint'],section,flags=re.M)
    ini=''.join(sections)
    ini=re.sub(r'^material_library\s*=.*rh_concept_b_lods\.mat\s*\n','',ini,flags=re.M|re.I)
    path.write_text(ini,encoding='utf8')


def build():
    meta=json.loads((OUT/'input_manifest.json').read_text())
    assert f.digest(SOURCE)==meta['source_sha256']
    header,nodes=f.mesh.read_tree(SOURCE.read_bytes());names=f.component_map(nodes)
    initial_hp=hp.hardpoint_records(nodes);local=f.local_geometry(nodes)
    root=next(k for k,n in names.items() if n=='Root')
    shift=np.array(json.loads((f.OUT/'assembly.json').read_text())['center_shift_native'])
    engines=rebuild_engines(local);chin=add_chin(local,root,shift)
    # Damage geometry is generated in the unfolded frame, before changing rest pose.
    damage.OUT=OUT
    (OUT/'assembly.json').write_bytes((f.OUT/'assembly.json').read_bytes())
    descriptions=damage.damage(nodes);renamed=unique_damage(nodes,descriptions)
    write_config(descriptions)
    dump('damage_manifest.json',descriptions)
    solid,pieces=solid_lod(nodes,local,shift,20)
    distant,_=solid_lod(nodes,local,shift,12)
    f.write_geometry(nodes,[local,solid,distant])
    # Freeze an explicit unfolded assembly for static SUR and root-space wire.
    unfolded=copy.deepcopy(nodes)
    (OUT/'unfolded_reference.cmp').write_bytes(f.mesh.write_tree(header,unfolded))
    rig=fold_rest(nodes)
    DEST.write_bytes(f.mesh.write_tree(header,nodes))
    dump('geometry.json',{names[k]:[dict(g,corners=g['corners']) for g in gs] for k,gs in local.items()})
    dump('solid_geometry.json',{names[k]:[dict(g,corners=g['corners']) for g in gs] for k,gs in solid.items()})
    dump('wire_pieces.json',{names[k]:[dict(g,corners=g['corners']) for g in gs] for k,gs in pieces.items()})
    # Equipment hardpoints are byte-preserved locally; only the requested damage names change.
    after=hp.hardpoint_records(nodes)
    for old in initial_hp:
        if old['name'].lower().startswith('dp'):continue
        new=next(p for p in after if p['owner']==old['owner'] and p['name']==old['name'])
        assert old==new,old['name']
    assert len({p['name'].lower() for p in after})==len(after)
    before_tr,_=f.audit.transforms(unfolded)
    open_tr,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    folded_tr,_=f.audit.transforms(nodes,('Sc_extend wing',1))
    rest_tr,_=f.audit.transforms(nodes)
    for file in names:
        assert np.allclose(before_tr[file.lower()][0],open_tr[file.lower()][0],atol=2e-6)
        assert np.allclose(rest_tr[file.lower()][0],folded_tr[file.lower()][0],atol=2e-6)
    report=dict(cmp=str(DEST),cmp_sha256=f.digest(DEST),source_sha256=meta['source_sha256'],
       engines=engines,chin=chin,rig=rig,damage_names=renamed,hardpoint_nodes=after,
       hardpoints=f.hp_world(nodes),hardpoints_unfolded=f.hp_world(unfolded),
       lod_triangles=[sum(len(g['corners']) for gs in lv.values() for g in gs) for lv in (local,solid,distant)],
       sources=meta,center_shift_native=shift,scope='offline only; user CMP and game untouched')
    dump('build.json',report)
    print('V2 GEOMETRY',report['lod_triangles'],'unique HP',len(after),flush=True)


if __name__=='__main__':build()
