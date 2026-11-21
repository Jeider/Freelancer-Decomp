"""F01 UV/03: shallow hold, native circle motifs, receiving wing slots.

Offline LOD0 only. The latest user instruction replaces the upward fold with
levelling the original swept blade and retracting its inner section.
"""
import copy
import json
import math
import shutil
from pathlib import Path
import numpy as np
import rh_fighter_f01_uv2 as prev
import uv_mesh_seams

model,s,f=prev.model,prev.s,prev.f
old,uv=prev.old,prev.uv
first,body=prev.previous,prev.previous.body
B=first.B
P,R,D,P3,HOLD=prev.P,prev.R,prev.D,prev.P3,first.HOLD
SOURCE=prev.OUT/'geometry.json'
OUT=model.TOPIC/'prototypes/f01_uv_03'
Z0,Z1,HALF=first.Z0,first.Z1,first.HALF
FLOOR=.55
RETRACT=1.35
LEVEL=math.degrees(math.atan(.285))
MOUNT_PROFILE=[(1.28,1.33,.28,.61),(1.54,1.53,.43,.64),
    (1.735,1.63,.56,.66),(1.88,1.72,.60,.69),(2.04,1.78,.64,.71),
    (2.19,model.ENGINE_X,.72,.72),(2.25,model.ENGINE_X,.72,.72)]
REGULAR=model.SOURCE.parent.parent/'rh_fighter/rh_fighter.cmp'
PATCHES=dict(prev.PATCHES)
PATCHES['red_small']=[(R,(.345,.325,.655,.463))]
SLOT=model.clipped_rect(-1.83,1.10,-1.44,-.95,.035)
FRONT_FIELDS=[s.clip_poly(body.FRONT_PANEL,0,-2.67,False),
              s.clip_poly(s.clip_poly(body.FRONT_PANEL,0,-2.48,True),1,-.82,True)]
VENT=s.clip_poly(body.VENT,1,-.80,True)
OUTLINE=body.OUTLINE.copy()
for p in OUTLINE:
    if abs(p[0]-.93)<1e-6:p[:]=[1.30,-1.60]
    if abs(p[0]+.95)<1e-6:p[1]=-1.65


def copy_entry(entry):
    out=copy.deepcopy(entry)
    out['groups']=[dict(g,corners=np.array(g['corners'],float)) for g in out['groups']]
    return out


def corners_only(poly):
    poly=np.asarray(poly,float)
    keep=[]
    for i,(a,b,c) in enumerate(zip(np.roll(poly,1,axis=0),poly,np.roll(poly,-1,axis=0))):
        u=b-a;v=c-b
        if abs(u[0]*v[1]-u[1]*v[0])>1e-9:keep.append(i)
    return poly[keep]


def field_pocket(b,mouth,sign,back,n,mat,lip,lip_depth):
    # These fields are convex. Keep every boundary subdivision from the front
    # triangulation; dropping its midpoints before the hull deformation opens
    # tiny cracks on otherwise shared edges.
    inner=s.offset(mouth,lip);points=s.points(inner,0,sign*back);center=points.mean(0)
    for a,c in zip(points,np.roll(points,-1,axis=0)):b.face([a,c,center],mat,model.PLAIN,n)
    s.link(b,s.points(mouth,0,sign),s.points(inner,0,sign*(1-lip_depth)),D,True)
    s.link(b,s.points(inner,0,sign*(1-lip_depth)),points,D,True)


def flanks():
    s.OBJECTS.clear()
    for sign,label in [(-1,'Port'),(1,'Starboard')]:
        b=B();n=np.array([sign,0,0])
        ls=s.panel(b,OUTLINE,0,sign,n,P,holes=FRONT_FIELDS+[VENT,body.REAR_PANEL,SLOT])
        for h in ls[1:3]:field_pocket(b,h,sign,.86,n,R,.065,.05)
        field_pocket(b,ls[3],sign,.53,n,D,.075,.08)
        field_pocket(b,ls[4],sign,.88,n,R,.055,.045)
        # The receiving pocket is a real closed socket through the old thick
        # flank, not a wing sliding into a solid or an invisible intersection.
        outer_slot=s.offset(SLOT,-.055)
        back=s.panel(b,corners_only(ls[0]),0,sign*.14,-n,D,holes=[outer_slot])
        s.link(b,s.points(ls[0],0,sign*.14),s.points(ls[0],0,sign),P)
        s.link(b,s.points(ls[5],0,sign),s.points(ls[5],0,sign*.061),D,True)
        s.panel(b,ls[5],0,sign*.061,n,D)
        s.link(b,s.points(back[1],0,sign*.14),s.points(back[1],0,sign*.001),P)
        s.panel(b,back[1],0,sign*.001,-n,P)
        inner=s.offset(VENT,.07)
        for y in (-.60,-.16,.28,.72):
            poly=s.clip_poly(s.clip_poly(inner,1,y-.085,True),1,y+.085,False)
            if len(poly)<3:continue
            center=float(poly[:,0].mean());poly[:,0]+=.020*np.sign(poly[:,0]-center)
            outer=np.array([[sign*(.88-.15*(yy-y+.085)/.17),yy,z] for z,yy in poly])
            rear=outer.copy();rear[:,0]-=sign*.075
            b.face(outer,P,model.PLAIN,[sign,1,0]);b.face(rear,D,model.PLAIN,[-sign,-1,0]);s.link(b,outer,rear,D)
        def mapped(v):
            x,y,z=v
            if abs(x)<.062:return [sign*(.24+abs(x)),y,z]
            return [sign*(s.side_x(z,y)-(1-abs(x))),y,z]
        s.add(label+'_carved_flank',b,'hull',True,mapped)
    return copy.deepcopy(s.OBJECTS)


def shallow_hold(source):
    # Remove the entire obsolete sliding-lid receiver, preserving exterior keel
    # triangles and their approved UVs exactly.
    entry=copy_entry(source)
    entry['groups']=[g for g in entry['groups'] if g['material']!=HOLD]
    old_lower=s.SIDE[5:][::-1];new_lower=OUTLINE[len(body.TOP):][::-1]
    for g in entry['groups']:
        t=g['corners'];z=t[...,2]
        t[...,1]+=np.interp(z,new_lower[:,0],new_lower[:,1])-np.interp(z,old_lower[:,0],old_lower[:,1])
        nn=np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3]);nn/=np.linalg.norm(nn,axis=1)[:,None];t[...,3:6]=nn[:,None,:]
    b=B()
    inner=np.array([[-HALF,Z0],[HALF,Z0],[HALF,Z1],[-HALF,Z1]])
    top=np.array([[x,body.roof_y(z),z] for x,z in inner])
    floor=top.copy();floor[:,1]=FLOOR
    b.face(floor,HOLD,model.PLAIN,[0,1,0])
    for a,c,d,e in zip(top,np.roll(top,-1,axis=0),np.roll(floor,-1,axis=0),floor):
        center=(a+c+d+e)/4
        inward=np.array([0,FLOOR,(Z0+Z1)/2])-center;inward[1]=0
        b.face([a,c,d,e],HOLD,model.PLAIN,inward)
    # Underside and exterior thickness of the little tub; no cargo running aft.
    bottom=floor.copy();bottom[:,1]-=.055
    b.face(bottom,P,model.PLAIN,[0,-1,0])
    s.link(b,floor,bottom,D)
    m=old.Mapper('Root shallow cargo')
    for g in b.groups():
        for t in g['corners']:
            if g['material']==D:mat=HOLD
            else:mat=g['material']
            n=old.normal(t);p=t[:,:3]
            if abs(n[1])>.9:
                box=(.02,.02,.98,.98) if mat==HOLD else PATCHES['pale'][0][1]
                prev.fixed(m,t,mat,p[:,[0,2]],(-HALF,Z0),(HALF,Z1),box)
            elif abs(n[0])>.8:
                prev.fixed(m,t,HOLD,p[:,[2,1]],(Z0,FLOOR),(Z1,1.03),(.02,.26,.98,.48))
            else:
                prev.fixed(m,t,HOLD,p[:,[0,1]],(-HALF,FLOOR),(HALF,1.03),(.02,.26,.98,.57))
    entry['groups']+=m.finish()
    return entry


def roof_and_leaves():
    s.OBJECTS.clear();first.new_roof();out=[]
    for raw in s.OBJECTS:
        entry=copy_entry(raw);name=entry['name'];m=old.Mapper(name)
        for g in entry['groups']:
            for t in g['corners']:
                if name=='Sculpted_roof_shoulders':
                    # The new tub itself meets the roof; discard old receiver
                    # walls/ceilings, not merely hide them below a raised floor.
                    if g['material']==D:continue
                    prev.roof(m,t,g['material'])
                elif old.normal(t)[1]<-.8:
                    p=t[:,:3]
                    prev.fixed(m,t,HOLD,np.column_stack((abs(p[:,0]),p[:,2])),
                        (.012,Z0+.016),(.721,Z1-.016),(.04,.02,.348,.98))
                else:
                    p=t[:,:3];n=old.normal(t)
                    if n[1]>.8:
                        prev.fixed(m,t,P,np.column_stack((abs(p[:,0]),p[:,2])),
                            (.012,Z0+.016),(.721,Z1-.016),(.680,.272,.885,.852))
                    else:m.plane(t,'quiet_brown',(100,100))
        entry['groups']=m.finish();out.append(entry)
    return out


def mount_geometry():
    s.OBJECTS.clear()
    for sign,label in [(-1,'Port'),(1,'Starboard')]:
        b=B();a=np.arange(24)*2*np.pi/24;cy=prev.ENGINE_Y;cx=model.ENGINE_X
        # A broad root becomes an annular receiving collar around the actual
        # forward engine shoulder. The old triangular seat is wholly removed.
        def loop(z,x,rx,ry):return np.column_stack((sign*(x+rx*np.cos(a)),cy+ry*np.sin(a),np.full(len(a),z)))
        rings=[loop(*p) for p in MOUNT_PROFILE]
        for aa,cc in zip(rings,rings[1:]):s.link(b,aa,cc,P3)
        b.face(rings[0],P,model.PLAIN,[0,0,-1])
        inn=[loop(2.25,cx,.686,.686),loop(2.18,cx,.627,.627),
             loop(2.04,cx,.487,.487),loop(1.84,cx,.407,.407),loop(1.735,cx,.335,.335)]
        for i in range(len(a)):
            j=(i+1)%len(a);b.face([rings[-1][i],rings[-1][j],inn[0][j],inn[0][i]],P,model.PLAIN,[0,0,1])
        for aa,cc in zip(inn,inn[1:]):s.link(b,aa,cc,D,True)
        b.face(inn[-1],D,model.PLAIN,[0,0,1])
        s.add(label+'_integrated_engine_seat',b,'mount',True)
    return copy.deepcopy(s.OBJECTS)


def mechanism():
    s.OBJECTS.clear()
    for sign,label in [(-1,'Port'),(1,'Starboard')]:
        b=B()
        # Two short C channels lie INSIDE the receiving pocket and run across
        # the hull. Their open channels carry the sliding pivot blocks.
        for zc in (-.55,.64):
            profile=np.array([[zc-.13,-1.425],[zc+.13,-1.425],[zc+.13,-1.315],
                [zc+.095,-1.315],[zc+.095,-1.365],[zc-.095,-1.365],
                [zc-.095,-1.315],[zc-.13,-1.315]])
            # Concave section outward normals, independent of profile centroid.
            area=np.sum(profile[:,0]*np.roll(profile[:,1],-1)-profile[:,1]*np.roll(profile[:,0],-1))
            if area<0:profile=profile[::-1]
            for at,n in [(sign*.245,[-sign,0,0]),(sign*1.92,[sign,0,0])]:s.panel(b,profile,0,at,n,P3)
            for aa,cc in zip(profile,np.roll(profile,-1,axis=0)):
                d=cc-aa
                b.face([[sign*.245,aa[1],aa[0]],[sign*1.92,aa[1],aa[0]],
                        [sign*1.92,cc[1],cc[0]],[sign*.245,cc[1],cc[0]]],P3,model.PLAIN,[0,-d[0],d[1]])
        s.add(label+'_slide_guide',b,'wing guide',True)
        b=B()
        for zc in (-.55,.64):
            # Compact rotating root seats carried by transverse slider blocks.
            poly=np.array([[zc-.078,-1.35],[zc+.078,-1.35],[zc+.078,-1.00],[zc-.078,-1.00]])
            s.prism(b,poly,0,sign*1.89,sign*1.66,P)
        s.add(label+'_slide_carriage',b,'wing carriage',True)
    return copy.deepcopy(s.OBJECTS)


def motions():
    motion=copy.deepcopy(prev.motions())
    for sign,label in [(-1,'Port'),(1,'Starboard')]:
        motion[label+'_swept_wing'].update(pivot=[sign*1.77,-1.02,0],
            angle_degrees=sign*LEVEL,translation=[-sign*RETRACT,0,0],
            turn_start=0,turn_end=.38,slide_start=.38,slide_end=1)
        motion[label+'_slide_carriage'].update(translation=[-sign*RETRACT,0,0],
            turn_start=0,turn_end=.38,slide_start=.38,slide_end=1)
    return motion


def motion_transform(m,phase):
    smooth=lambda x:max(0,min(1,x))**2*(3-2*max(0,min(1,x)))
    if m['kind']=='wing':
        a=m.get('slide_start',0);b=m.get('slide_end',.30);slide=smooth((phase-a)/(b-a))
        a=m.get('turn_start',.25);b=m.get('turn_end',1);turn=smooth((phase-a)/(b-a))
    else:slide=phase;turn=smooth(phase)
    r=first.rot(m['axis'],math.radians(m['angle_degrees'])*turn);p=np.array(m['pivot'])
    return r,p-r@p+np.array(m.get('translation',[0,0,0]))*slide


def flank(m,t,role):
    p=t[:,:3];n=old.normal(t);z=p[:,2];y=p[:,1]
    if role==R:
        if z.mean()<-.85:
            which=int(z.mean()>-2.57)
            m.chart(t,'red_small',np.column_stack((-z,-y)),(.82,.42),('front red pocket',which),True)
        else:
            m.chart(t,'red_small',np.column_stack((-z,-y)),(.86,.38),'rear red pocket',True)
    elif z.min()>-1.88 and z.max()<1.17 and y.max()<-.90:
        m.plane(t,'quiet_brown' if role==D else 'quiet_trim',(100,100))
    elif role==D:m.plane(t,'quiet_brown',(100,100))
    else:first.flank(m,t,role)


def drum(m,t,role):
    p=t[:,:3];n=old.normal(t);cy=prev.CY
    if abs(n[2])>.98 and np.max(abs(p[:,2]-3.095))<2e-5:
        # Native RH fighter maps the lower-right panel02 quarter twice around
        # the disc. Join two quarters into a HALF per well, with the joint at
        # mid-height; no repeated rectangle or stretched red brick substitute.
        for low,high in [(cy-3,cy),(cy,cy+3)]:
            poly=uv.clip(uv.clip(t,1,low,True),1,high,False)
            for j in range(1,len(poly)-1):
                a=poly[[0,j,j+1]].copy();pp=a[:,:3]
                a[:,6]=.501+np.abs(pp[:,0])*.253
                a[:,7]=.501+np.abs(pp[:,1]-cy)*.253
                m.keep(a,R)
        return
    if abs(n[2])>.98 and np.max(abs(p[:,2]-(model.DRUM_REAR-.045)))<2e-5 and p[:,1].mean()<cy-.50:
        # Correct the old oval distortion: atlas and modeled crop have matching
        # aspect ratio. Equal pixel density in both world axes keeps it round.
        box=(.135,.851,.502,.570);w=.72;h=w*abs(box[3]-box[1])/abs(box[2]-box[0]);yy=cy-1.09
        pale=lambda a:prev.fixed(m,a,P,a[:,[0,1]],(-.55,cy-1.56),(.55,cy-.515),(.51,.852,.995,.272))
        prev.clipped_field(m,t,[0,1],(-w/2,yy-h/2,w/2,yy+h/2),P,box,pale);return
    prev.drum(m,t,role)


def engine(m,t,role):
    p=t[:,:3];cx=math.copysign(model.ENGINE_X,float(p[:,0].mean()))
    err,band,co=prev.profile_chart(p,cx,prev.ENGINE_Y,old.ENGINE_PROFILE,.62)
    if err>.001 or np.max(abs(p[:,2]-1.76))<2e-5 or np.max(abs(p[:,2]-3.58))<2e-5:
        prev.engine(m,t,role);return
    lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old.ENGINE_PROFILE,axis=0),axis=1))]
    sector=int(math.floor(float(co[:,0].mean())/(math.pi*.31)))%4
    start=sector*math.pi*.31;end=start+math.pi*.31
    if band<=4:
        prev.fixed(m,t,P3,co,(start,0),(end,lengths[5]),(.008,.509,.426,.704))
    elif 8<=band<=11:
        prev.fixed(m,t,P3,co,(start,lengths[8]),(end,lengths[12]),(.008,.509,.426,.704))
    elif band in (12,14):
        prev.fixed(m,t,D,co,(start,lengths[band]),(end,lengths[band+1]),(.53,.37,.97,.44))
    else:prev.engine(m,t,role)


def mount(m,t,role):
    p=t[:,:3];n=old.normal(t)
    if role==D:m.plane(t,'quiet_brown',(100,100));return
    if role==P:m.plane(t,'pale_edge',(100,100));return
    # Shared longitudinal charts across all blended sections, with the seam
    # below. Angular distance follows the changing center of the fairing.
    profile=np.array(MOUNT_PROFILE)
    cx=np.interp(p[:,2],profile[:,0],profile[:,1])
    theta=np.unwrap(np.arctan2(p[:,1]-prev.ENGINE_Y,abs(p[:,0])-cx)+np.pi/2)
    theta-=math.floor(float(theta.mean())/(2*np.pi))*2*np.pi
    co=np.column_stack((theta*.65,p[:,2]));sector=int(theta.mean()/(np.pi/2))%4
    m.chart(t,'quiet_trim',co,(100,100),('mount profile',sector))


def wing_edges(entry):
    m=old.Mapper(entry['name']);sign=1 if entry['name'].startswith('Starboard') else -1
    # Outline from the accepted blade. Unfold long physical edges, not a world
    # XY projection that makes the atlas run diagonally across the wing edge.
    outline=np.array([[1.77,-.80],[5.08,-3.40],[5.36,-3.28],[5.36,-2.19],[2.46,.86],[1.77,1.02]])
    edges=np.roll(outline,-1,axis=0)-outline;lengths=np.linalg.norm(edges,axis=1);starts=np.r_[0,np.cumsum(lengths)]
    for g in entry['groups']:
        for t in np.asarray(g['corners'],float):
            n=old.normal(t)
            if abs(n[1])>.8 or g['material']==old.WARNING:m.keep(t,g['material']);continue
            p=t[:,:3];q=np.column_stack((sign*p[:,0],p[:,2]));mid=q.mean(0)
            distances=[]
            for a,d,l in zip(outline,edges,lengths):
                at=np.clip((mid-a)@d/(l*l),0,1);distances.append(np.linalg.norm(mid-a-at*d))
            # Internal pocket lips are already represented in the matching
            # underside layout. Only the thin OUTER edge needs this new chart.
            if min(distances)>.045:m.keep(t,g['material']);continue
            i=int(np.argmin(distances));d=edges[i]/lengths[i]
            along=starts[i]+(q-outline[i])@d
            depth=-(p[:,1]+1.02+.285*(q[:,0]-1.77))
            if np.ptp(depth)<1e-6:m.keep(t,g['material']);continue
            prev.fixed(m,t,D,np.column_stack((along,depth)),(starts[i],0),(starts[i+1],.22),(.51,.17,.995,.25))
    e=copy_entry(entry);e['groups']=m.finish();return e


def main():
    assert shutil.disk_usage(model.ROOT).free>3*1024**3
    data=json.loads(SOURCE.read_text(encoding='utf8'));by={e['name']:e for e in data['objects']}
    for ex in data['exports']:assert f.digest(Path(ex['file']))==ex['sha256'],('User-edited CMP: import HPs first',ex['file'])
    for path,digest in data['sources'].items():assert f.digest(Path(path))==digest,path
    assert f.digest(REGULAR)=='cd4c27117eea0559c06a1b33bc9d9a77ea8c676540bf43b55495689720507a37'
    data['sources'][REGULAR.as_posix()]=f.digest(REGULAR)
    uv.PATCHES.update(PATCHES);old.REPORT.clear()
    raw=json.loads(prev.BASE.read_text(encoding='utf8'));raw={e['name']:e for e in raw['objects']}
    changed={e['name']:e for e in flanks()+mount_geometry()+mechanism()}
    for name in ('Armored_transverse_drum','Port_sculpted_engine','Starboard_sculpted_engine'):changed[name]=copy_entry(raw[name])
    mapped={e['name']:e for e in roof_and_leaves()}
    mapped['Root']=shallow_hold(by['Root'])
    for name in ('Port_swept_wing','Starboard_swept_wing'):mapped[name]=wing_edges(by[name])
    objects=[];preserved=[];checks=[]
    for source in data['objects']:
        name=source['name'];cleanup={}
        if name in changed:
            entry=copy_entry(changed[name]);original=entry['groups'];m=old.Mapper(name)
            for g in original:
                for t in g['corners']:
                    if name.endswith('_carved_flank'):flank(m,t,g['material'])
                    elif name.endswith('_sculpted_engine'):engine(m,t,g['material'])
                    elif name=='Armored_transverse_drum':drum(m,t,g['material'])
                    elif name.endswith('_integrated_engine_seat'):mount(m,t,g['material'])
                    else:m.plane(t,'quiet_brown' if g['material']==D else 'quiet_trim',(100,100))
            entry['groups']=m.finish()
            try:entry['groups'],cleanup=uv_mesh_seams.clean(entry['groups'],original,entry['authored_closed'])
            except AssertionError as exc:raise AssertionError((name,exc)) from exc
            assert abs(old.area(entry['groups'])-old.area(original))<max(1e-5,old.area(original)*2e-5),name
        elif name in mapped:
            entry=mapped[name]
            if name.endswith('_BayDoor'):
                entry['groups'],cleanup=uv_mesh_seams.clean(entry['groups'],entry['groups'],True)
        else:entry=copy_entry(source);preserved.append(name)
        objects.append(entry);checks.append(dict(name=name,cleanup=cleanup,triangles=sum(len(g['corners']) for g in entry['groups'])))
    OUT.mkdir(parents=True,exist_ok=True);motion=motions()
    header,_=f.mesh.read_tree(model.SOURCE.read_bytes());exports=[]
    for suffix,mode in [('open',None),('bay_open','door'),('folded','wing')]:
        posed=copy.deepcopy(objects)
        for e in posed:
            if e['name'] in motion and motion[e['name']]['kind']==mode:
                r,t=motion_transform(motion[e['name']],1);e['groups']=f.base.world(e['groups'],r,t)
        ex=model.export_cmp(header,posed,OUT/f'rh_pir_fighter_f01_uv3_{suffix}.cmp',min_cross_area=1e-12)
        ex.update(pose=suffix,static_extended=suffix=='open',bay_open=suffix=='bay_open');first.add_hardpoints(ex);exports.append(ex)
    old_mechanism=data.get('mechanism_source')
    data.update(objects=objects,exports=exports,revision='F01 UV/03',shape_source=SOURCE.as_posix(),shape_source_sha256=f.digest(SOURCE),
        total_triangles=sum(c['triangles'] for c in checks),preserved_objects=preserved,motion=motion,
        blend_basename='rh_pir_fighter_f01_uv3.blend',
        stage='Offline LOD0 prototype: shallow hold, receiving wing sockets, level then retract; static CMP poses, Blender motion.',
        mechanism_source=dict(description='User-selected levelling then inward translation; UV/02 upward fold is superseded.',
            superseded_reference=old_mechanism),
        form_notes=['Native cabin and accepted wing blade geometry preserved.',
            'Local shallow cargo tub under the two roof leaves; large cargo-only metal charts.',
            'Two front red recesses, native half-circle drum motifs and wrapped engine seats.',
            'Wing levels then retracts one inner field into a closed socket; gun-bearing outer fields stay exposed.',
            'Long wing-edge UVs follow the blade perimeter; top/bottom remain matched.'],
        cargo=dict(floor_y=FLOOR,rim_y=first.door_y((Z0+Z1)/2),depth=first.door_y((Z0+Z1)/2)-FLOOR,
                   bounds=[[-HALF,FLOOR,Z0],[HALF,1.03,Z1]],old_floor_y=-.70,old_z_span=[-4.25,2.94]),
        wing_retraction=dict(level_degrees=LEVEL,inward_travel=RETRACT,first_section_outer_x=3.12,
            receiver_back_x=.301,receiver_z=[-1.83,1.10],receiver_y=[-1.44,-.95],
            gun_mount_note='Outer two blade fields stay outside; final weapon HP/loadout not yet authored.'),
        cargo_ray_probes=[[[0,.82,-2.75],[0,-1,0]],[[0,.82,-2.75],[1,0,0]],
                          [[0,.82,-2.75],[-1,0,0]],[[0,.82,-2.75],[0,0,-1]],[[0,.82,-2.75],[0,0,1]]])
    model.dump(OUT/'geometry.json',data)
    model.dump(OUT/'uv_report.json',dict(geometry_sha256=f.digest(OUT/'geometry.json'),object_checks=checks,charts=old.REPORT))
    print(json.dumps(dict(output=str(OUT),triangles=data['total_triangles'],preserved=preserved),indent=2))


if __name__=='__main__':main()
