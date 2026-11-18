"""Author engine wounds from our intact cylinders; repair damage winding and UV.

No imported damaged engine geometry. Reads current user assets, writes local
review assets only. Native materials remain in the user's shared MAT.
"""
import collections
import copy
import json
from pathlib import Path
import secrets
import struct as S
import numpy as np
from scipy.spatial import ConvexHull
from PIL import Image, ImageDraw, ImageFont
import rh_pir_elite_build as b
import rh_concept_b_final_damage as damage
from rh_concept_b_damage_reference import groups
from rh_concept_b_engine_shell import topology
from rh_concept_b_v2_sur import read_hulls
from ship_collision_audit import sur_parts
from preview import render

f=b.f
GAME=Path('D:/Games/FL_MOD')
SOURCE=GAME/'DATA/ships/rheinland/rh_pir_elite'
OUT=b.OUT/'engine_damage_closed'
ASSETS=OUT/'assets'
PANEL=f.mesh.crc('pir_r_panel01_256')
DARK=f.mesh.crc('pir_r_panel01_256D')
BURNT=f.mesh.crc('pir_r_dmg3')
EQUIP=f.mesh.crc('Equip_genD')


def save(path,value):path.write_text(json.dumps(value,default=b.v.hp.serial,ensure_ascii=False,indent=2),encoding='utf-8')
def key(p):return tuple(np.round(p,4))


def split_support(current):
    panel=next(g for g in current if g['material']==PANEL);a=panel['corners'];adj=collections.defaultdict(set)
    for i,t in enumerate(a):
        for p in t[:,:3]:adj[key(p)].add(i)
    ids=set(np.flatnonzero(a[...,1].max(1)>.8).tolist());queue=list(ids)
    while queue:
        for p in a[queue.pop(),:,:3]:
            fresh=adj[key(p)]-ids;ids|=fresh;queue.extend(fresh)
    assert len(ids)==12
    return a[sorted(ids)].copy(),np.delete(a,sorted(ids),axis=0)


def coherent(groups):
    """Weld tiny source seams, orient each closed component, then recompute normals."""
    result=copy.deepcopy(groups);triangles=np.concatenate([g['corners'] for g in result]);canonical={}
    for tri in triangles:
        for v in tri:
            k=key(v[:3]);v[:3]=canonical.setdefault(k,v[:3].copy())
    edges=collections.defaultdict(list)
    for i,t in enumerate(triangles):
        ks=[key(p) for p in t[:,:3]]
        assert len(set(ks))==3,('Degenerate triangle',i)
        for a,c in zip(ks,ks[1:]+ks[:1]):edges[tuple(sorted((a,c)))].append((i,a<c))
    assert all(len(v)==2 for v in edges.values()),collections.Counter(len(v) for v in edges.values())
    adj=collections.defaultdict(list)
    for pair in edges.values():
        (i,a),(j,c)=pair;adj[i].append((j,a==c));adj[j].append((i,a==c))
    flips={};components=[]
    for i in range(len(triangles)):
        if i in flips:continue
        flips[i]=False;queue=[i];component=[]
        while queue:
            n=queue.pop();component.append(n)
            for j,toggle in adj[n]:
                wanted=flips[n]^toggle
                if j in flips:assert flips[j]==wanted,'Nonorientable surface'
                else:flips[j]=wanted;queue.append(j)
        components.append(component)
    for i,flip in flips.items():
        if flip:triangles[i]=triangles[i,[0,2,1]]
    volumes=[]
    for comp in components:
        t=triangles[comp,:,:3];volume=np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6
        assert abs(volume)>1e-7,('Zero-volume component',comp)
        if volume<0:triangles[comp]=triangles[comp][:,[0,2,1]]
        volumes.append(abs(float(volume)))
    n=np.cross(triangles[:,1,:3]-triangles[:,0,:3],triangles[:,2,:3]-triangles[:,0,:3]);length=np.linalg.norm(n,axis=1)
    assert length.min()>1e-8
    triangles[...,3:6]=(n/length[:,None])[:,None,:]
    at=0
    for g in result:
        count=len(g['corners']);g['corners']=triangles[at:at+count].copy();at+=count
    assert not any(topology(triangles).values())
    return result,dict(components=len(components),volumes=volumes,topology=topology(triangles))


def make_engine(current,side):
    support,body=split_support(current)
    nose=body[body[...,2].max(1)<-1.3927].copy();assert len(nose)==30
    frontpoints=body[...,:3].reshape(-1,3)
    frontpoints=frontpoints[abs(frontpoints[:,2]+1.3928)<.00015]
    unique={key(p):p for p in frontpoints};front=np.array(list(unique.values()))
    angles=np.arctan2(front[:,1],front[:,0])%(2*np.pi)
    front=front[np.argsort(angles)];assert len(front)==10
    # Independent authored fracture profiles. Keep our complete front and mount.
    cut=np.array([.68,.32,.58,.91,.60,.45,.22,.48,.82,1.06])
    if side=='starboard':cut=np.array([.48,.76,.54,.26,.44,.82,1.01,.65,.37,.73])
    outer=front.copy();outer[:,2]=cut
    # Subtle folds at the tear; nothing creates the original wing-mount notch.
    bends=np.array([1.0,1.025,.98,1.04,1.0,.98,1.025,1.0,.985,1.02])
    outer[:,:2]*=bends[:,None]
    shoulder=front.copy();shoulder[:,2]=cut-.22
    inner=outer.copy();inner[:,:2]*=.88;inner[:,2]-=.035
    floor=front.copy();floor[:,:2]*=.76;floor[:,2]=-.29
    base=front.copy();base[:,:2]=base[:,:2]*.36+[-.045,.035];base[:,2]=-.29
    core=base.copy();core[:,:2]=core[:,:2]*.9+[.015,-.01]
    core[:,2]=np.array([.015,.09,.035,-.04,-.07,.02,.11,.07,-.015,-.035])
    gs=[dict(material=PANEL,corners=np.concatenate((nose,support)),unused=204)]
    bymat=collections.defaultdict(list)
    def tri(points,uv,mat):
        a=np.zeros((3,8));a[:,:3]=points;a[:,6:8]=uv;bymat[mat].append(a)
    def quad(points,uv,mat):
        for ids in ([0,1,2],[0,2,3]):tri(np.array(points)[ids],np.array(uv)[ids],mat)
    def machinery(points):return np.array(points)[:,:2]*.31+[.25,.255]
    for i in range(10):
        j=(i+1)%10
        # The same continuous strip as our intact barrel, cropped at the rupture.
        uv=lambda p,v:[.998-(p[2]+1.3928)/(1.85+1.3928)*.996,v]
        quad([front[i],front[j],shoulder[j],shoulder[i]],
             [uv(front[i],.860),uv(front[j],.998),uv(shoulder[j],.998),uv(shoulder[i],.860)],PANEL)
        u0=i*.225;u1=(i+1)*.225
        quad([shoulder[i],shoulder[j],outer[j],outer[i]],[[u0,.36],[u1,.36],[u1,.79],[u0,.79]],BURNT)
        quad([outer[i],outer[j],inner[j],inner[i]],[[u0,.79],[u1,.79],[u1,.93],[u0,.93]],BURNT)
        q=np.array([inner[i],inner[j],floor[j],floor[i]])
        # Distinct interior chart: dark machinery, not the exterior's tinted panel.
        quad(q,[[.025+i*.042,.30],[.025+(i+1)*.042,.30],[.025+(i+1)*.042,.48],[.025+i*.042,.48]],EQUIP)
        q=np.array([floor[i],floor[j],base[j],base[i]]);quad(q,machinery(q),EQUIP)
        q=np.array([base[i],base[j],core[j],core[i]]);quad(q,machinery(q),EQUIP)
        center=np.array([-.025,.025,.025]);q=np.array([core[i],core[j],center]);tri(q,machinery(q),EQUIP)
    gs += [dict(material=m,corners=np.array(ts),unused=204) for m,ts in bymat.items()]
    gs,checks=coherent(gs)
    checks.update(source='our intact engine only',nose_triangles=30,mount_triangles=12,
                  tear_z=cut.tolist(),triangles=sum(len(g['corners']) for g in gs),thickness_fraction=.12)
    return gs,checks


def repair_cap(current):
    old=np.concatenate([g['corners'] for g in current]);out,checks=coherent(current)
    # Brown rear plates are pir_r_panel01_256D, with a brown Dc multiplier.
    # Remap each planar patch as a whole to the mechanical quarter of Equip_gen.
    remapped=0
    for g in out:
        if g['material']!=DARK:continue
        patches=collections.defaultdict(list);ts=g['corners']
        for i,t in enumerate(ts):
            n=t[0,3:6];patches[tuple(np.r_[n,np.dot(n,t[0,:3])].round(3))].append(i)
        for ids in patches.values():
            t=ts[ids];n=t[0,0,3:6];axes=np.argsort(abs(n))[:2]
            q=t[...,axes];lo=q.reshape(-1,2).min(0);hi=q.reshape(-1,2).max(0)
            # Uniform scale across the complete patch; no per-triangle resets.
            uv=(q-(lo+hi)*.5)*(.44/max(hi-lo))+[.25,.255]
            ts[ids,:,6:8]=uv
        g['material']=EQUIP;remapped+=len(ts)
    checks.update(before_topology=topology(old),brown_panel_triangles_remapped=remapped,
                  triangles=sum(len(g['corners']) for g in out))
    return out,checks


def cull_render(scene,mats,center,radius,camera,size=650,mode='texture'):
    direction=np.array(camera,float);direction/=np.linalg.norm(direction)
    front=[]
    for g in scene:
        t=g['corners'];n=np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3])
        mask=n@direction>1e-9
        if mask.any():front.append(dict(g,corners=t[mask]))
    return render(front,mats,center,radius,camera,size=size,mode=mode)


def ray_checks(gs):
    """Back-face-aware first-hit check: cavity backing plus upper/lower skin."""
    t=np.concatenate([g['corners'][...,:3] for g in gs]);e1=t[:,1]-t[:,0];e2=t[:,2]-t[:,0]
    def hit(origin,direction):
        h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h);ok=det>1e-8
        inv=np.divide(1,det,out=np.zeros_like(det),where=ok)
        s=origin-t[:,0];u=np.einsum('ij,ij->i',s,h)*inv;q=np.cross(s,e1)
        v=q@direction*inv;distance=np.einsum('ij,ij->i',e2,q)*inv
        return np.any(ok&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(distance>0))
    count=0
    # Every ray through the open aft lip must meet a front-facing solid interior.
    for x in np.linspace(-.52,.52,17):
        for y in np.linspace(-.52,.52,17):
            if x*x+y*y>.50**2:continue
            assert hit(np.array([x,y,3.]),np.array([0.,0.,-1.])),('aft leak',x,y)
            count+=1
    for sign in (-1,1):
        for x in np.linspace(-.50,.50,11):
            for z in np.linspace(-1.30,.0,16):
                assert hit(np.array([x,sign*3.,z]),np.array([0.,-float(sign),0.])),('side leak',sign,x,z)
                count+=1
    return dict(front_facing_rays=count,misses=0)


def inspect_surf(path,gs):
    p=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in gs]);covered=np.zeros(len(p),bool)
    for pid,chunks in sur_parts(path.read_bytes()):
        assert pid==0
        for tag,raw in chunks:
            if tag!=b'surf':continue
            for cid,points in read_hulls(raw):
                hull=ConvexHull(points);covered|=np.all(p@hull.equations[:,:3].T+hull.equations[:,3]<=3e-4,axis=1)
    assert covered.all();return dict(covered_vertices=len(p),uncovered=0)


def main():
    OUT.mkdir(exist_ok=True);ASSETS.mkdir(exist_ok=True)
    model=SOURCE/'rh_pir_elite.cmp';model_hash=f.digest(model)
    nodes=f.mesh.read_tree(model.read_bytes())[1];names=f.component_map(nodes);local=f.local_geometry(nodes)
    transforms,_=f.audit.transforms(nodes);hps=f.hp_world(nodes)
    mats=f.audit.material_table([SOURCE.parent/'rh_pir_playerships.mat'])
    damage.OUT=OUT;salt=secrets.token_hex(6);records={};engines={};sources={str(model):model_hash}
    for zone in ('port_engine','starboard_engine','port_wing','starboard_wing','tail'):
        for ext in ('.3db','.sur'):
            p=SOURCE/('rh_pir_elite_dmg_'+zone+ext);sources[str(p)]=f.digest(p)
    for side in ('port','starboard'):
        owner=f'Rh_{side}_engine_lod1';file=next(k for k,n in names.items() if n==owner)
        gs,checks=make_engine(local[file],side);checks.update(ray_checks(gs))
        r,t=transforms[file.lower()];world=f.base.world(gs,r,t);hp=hps[f'dp{side}_engine']
        hr=np.array(hp['orientation']);ht=np.array(hp['position'])
        cap=f.base.world(world,hr.T,-hr.T@ht)
        records[side+'_engine']=(cap,checks)
        engines[side]=dict(healthy=local[file],damaged=gs,world=world)
    for zone in ('port_wing','starboard_wing','tail'):
        path=SOURCE/('rh_pir_elite_dmg_'+zone+'.3db');sources[str(path)]=f.digest(path)
        records[zone]=repair_cap(groups(path))
    report={}
    for zone,(gs,checks) in records.items():
        name='rh_pir_elite_dmg_'+zone;info=damage.write_simple(name,gs)
        path=OUT/'damage'/(name+'.3db');header,ns=f.mesh.read_tree(path.read_bytes())
        mapping=b.salt_tree(ns,salt+'_'+zone)
        assert not any('/material library' in p.lower() or '/texture library' in p.lower()
                       for p,n in f.mesh.walk(ns))
        target=ASSETS/path.name;target.write_bytes(f.mesh.write_tree(header,ns))
        target.with_suffix('.sur').write_bytes(path.with_suffix('.sur').read_bytes())
        decoded=groups(target);ts=np.concatenate([g['corners'] for g in decoded])
        assert not any(topology(ts).values()),(zone,topology(ts))
        assert np.isfinite(ts).all()
        for g in decoded:
            assert g['material'] in mats and g['material']!=DARK
            assert 'metal' not in mats[g['material']]['texture'].lower()
        checks['decoded_topology']=topology(ts);checks['collision']=inspect_surf(target.with_suffix('.sur'),decoded)
        report[zone]=dict(checks=checks,resources=mapping,sha256=f.digest(target),sur_sha256=f.digest(target.with_suffix('.sur')))
    # Inspect the actual exported meshes in engine-local space, not authoring arrays.
    for side in engines:
        gs=groups(ASSETS/f'rh_pir_elite_dmg_{side}_engine.3db');hp=hps[f'dp{side}_engine']
        world=f.base.world(gs,np.array(hp['orientation']),np.array(hp['position']))
        file=next(k for k,v in names.items() if v==f'Rh_{side}_engine_lod1');r,t=transforms[file.lower()]
        engines[side]['damaged']=f.base.world(world,r.T,-r.T@t);engines[side]['world']=world
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    sheet=Image.new('RGB',(1950,1400),'#101c26');draw=ImageDraw.Draw(sheet)
    cameras=[(-1,.7,1.3),(-1,-.8,1.2),(.12,.12,1.8)]
    for row,side in enumerate(('port','starboard')):
        gs=engines[side]['damaged'];ps=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in gs]);center=(ps.min(0)+ps.max(0))*.5
        radius=np.linalg.norm(ps-center,axis=1).max()*1.04
        for col,cam in enumerate(cameras):
            im=cull_render(gs,mats,center,radius,cam);sheet.paste(im,(650*col,700*row+45))
            draw.text((650*col+15,700*row+12),side+' / '+['сверху','снизу','внутренность'][col]+' / culling ON',font=font,fill='white')
    sheet.save(OUT/'engine_views.png')
    tail_old=groups(SOURCE/'rh_pir_elite_dmg_tail.3db');tail=groups(ASSETS/'rh_pir_elite_dmg_tail.3db')
    sheet=Image.new('RGB',(1400,760),'#101c26');draw=ImageDraw.Draw(sheet)
    # Reverse side of the upper fracture: this is where the brown panel exists.
    # Looking from below shows the already mechanical cavity and hides the error.
    ps=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in tail]);top=ps[ps[:,1]>1.5]
    center=(top.min(0)+top.max(0))*.5;radius=np.linalg.norm(top-center,axis=1).max()*1.08
    for col,gs in enumerate((tail_old,tail)):
        sheet.paste(cull_render(gs,mats,center,radius,(-.6,1.,1.1),size=700),(700*col,50))
        draw.text((700*col+20,15),['До: коричневая панель','После: механизмы и правильные грани'][col],font=font,fill='white')
    sheet.save(OUT/'tail_mapping.png')
    utr,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    scene=[g for file,gs in local.items() if '_engine_' not in names[file].lower() and names[file]!='Rh_tail_lod1' for g in f.base.world(gs,*utr[file.lower()])]
    for side in engines:scene+=engines[side]['world']
    hp=hps['dptail'];scene+=f.base.world(tail,np.array(hp['orientation']),np.array(hp['position']))
    ps=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in scene]);center=(ps.min(0)+ps.max(0))*.5;radius=np.linalg.norm(ps-center,axis=1).max()
    for title,cam in [('ship_above',(-1,.7,1)),('ship_below',(-1,-.85,1))]:cull_render(scene,mats,center,radius,cam,size=1100).save(OUT/(title+'.png'))
    assert all(f.digest(Path(p))==h for p,h in sources.items())
    manifest=dict(salt=salt,source_cmp=str(model),source_cmp_sha256=model_hash,source_hashes=sources,
        shared_mat_sha256=f.digest(SOURCE.parent/'rh_pir_playerships.mat'),parts=report,
        files={p.name:dict(sha256=f.digest(p),bytes=p.stat().st_size) for p in ASSETS.iterdir()},
        installed=False,game_launched=False,cmp_modified=False)
    save(OUT/'build.json',manifest)
    print(json.dumps({k:v['checks'] for k,v in report.items()},indent=2))


if __name__=='__main__':main()
