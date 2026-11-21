"""F01 UV/02 and forward carriage/upward fold, offline LOD0 only.

The alternate elite supplies the Pris -> Rev construction, not foreign meshes.
Native image patches and the accepted F01 surfaces remain the source assets.
"""
import copy
import json
import math
import shutil
from pathlib import Path
import numpy as np
import rh_fighter_f01_uv as previous
import uv_mesh_seams

model,s,f=previous.model,previous.s,previous.f
old,uv=previous.olduv,previous.uv
P,R,D,P3=old.P,old.R,old.BROWN,old.P3
SOURCE=previous.OUT/'geometry.json'
BASE=model.TOPIC/'prototypes/f14_03/geometry.json'
OUT=model.TOPIC/'prototypes/f01_uv_02'
ALT=Path('D:/Games/FL_MOD/DATA/ships/rheinland/rh_elite/rh_alt_elite.cmp')
CY=.5811675034
ENGINE_Y=-1.49195849658
PATCHES=dict(previous.PATCHES)
PATCHES.update({
    'quiet_trim':[(P3,(.008,.509,.426,.704))],
    'quiet_brown':[(D,(.53,.32,.97,.81))],
    'quiet_pale':[(P,(.51,.272,.995,.852))],
    'ring_trim':[(P3,(.008,.514,.425,.699))],
})


def fixed(m,t,mat,co,lo,hi,box):
    m.fixed(t,mat,np.asarray(co),lo,hi,box)


def clipped_field(m,t,axes,rect,mat,box,remainder):
    """One complete service motif, clipped into a larger existing surface."""
    pending=[t]
    for axis,bound,greater in [(axes[0],rect[0],True),(axes[0],rect[2],False),
                               (axes[1],rect[1],True),(axes[1],rect[3],False)]:
        kept=[]
        for poly in pending:
            outside=uv.clip(poly,axis,bound,not greater)
            for j in range(1,len(outside)-1):remainder(outside[[0,j,j+1]])
            inside=uv.clip(poly,axis,bound,greater)
            if len(inside)>2:kept.append(inside)
        pending=kept
    for poly in pending:
        for j in range(1,len(poly)-1):
            tri=poly[[0,j,j+1]]
            fixed(m,tri,mat,tri[:,axes],rect[:2],rect[2:],box)


def profile_chart(p,cx,cy,profile,reference_radius):
    error,band,co=old.profile_uv(p,cx,cy,profile)
    # All bands share the SAME angular coordinate: no resets at a shoulder.
    co[:,0]=old.arc_angle(p,cx,cy)*reference_radius
    return error,band,co


def engine(m,t,role):
    p=t[:,:3];cx=math.copysign(model.ENGINE_X,float(p[:,0].mean()))
    error,band,co=profile_chart(p,cx,ENGINE_Y,old.ENGINE_PROFILE,.62)
    if error>=.001 or np.max(abs(p[:,2]-1.76))<2e-5 or np.max(abs(p[:,2]-3.58))<2e-5:
        # Keep the approved four central armor panels and the native end caps.
        old.engine(m,t,role,ENGINE_Y);return
    lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(old.ENGINE_PROFILE,axis=0),axis=1))]
    sector=int(math.floor(float(co[:,0].mean())/(math.pi*.31)))%4
    start=sector*math.pi*.31;end=start+math.pi*.31
    if band>=16:
        fixed(m,t,D,co,(start,lengths[16]),(end,lengths[-1]),(.53,.32,.97,.81))
    elif band==15:
        fixed(m,t,P3,co,(start,lengths[15]),(end,lengths[16]),(.01,.52,.425,.65))
    elif band in (5,7):
        # A thin physical assembly seam, rather than another bolt-pattern strip.
        fixed(m,t,D,co,(start,lengths[band]),(end,lengths[band+1]),(.53,.37,.97,.40))
    else:
        # A single pale sheet from the forward shoulder to the nozzle collar;
        # raised center armor remains above it, with its accepted mapping.
        fixed(m,t,P,co,(start,0),(end,lengths[15]),PATCHES['pale'][0][1])


def drum(m,t,role):
    p=t[:,:3];n=old.normal(t);z=p[:,2];rad=np.hypot(p[:,0],p[:,1]-CY)
    r=model.RADIUS;front,rear=model.DRUM_FRONT,model.DRUM_REAR
    profile=[(front,r-.115),(front+.025,r-.035),(front+.07,r),(front+.13,r),
        (front+.15,r-.065),(rear-.15,r-.065),(rear-.13,r),(rear-.07,r),
        (rear-.025,r-.035),(rear,r-.115)]
    error,band,co=profile_chart(p,0,CY,profile,r)
    if error<.001 and band!=4:
        # Continuous strip around the profiled rail; one chart across its facets.
        m.chart(t,'ring_trim',co,(3.75,10),('profile rail',band>=5));return
    if rad.min()>r-.225:
        angle=old.arc_angle(p,0,CY)
        if abs(n[2])>.55:
            # Circumferential trim follows the actual rail, not individual triangles.
            co=np.column_stack((angle*(r-.12),rad))
            m.chart(t,'quiet_trim',co,(3.75,10),('annular rim',round(float(z.mean()),3)));return
        sector=int(math.floor(float(angle.mean())/(np.pi/6)))%12
        co=np.column_stack((angle*(r-.015),z))
        family='red' if role==R else 'quiet_brown' if role==D else 'quiet_pale'
        m.chart(t,family,co,(100,100),('barrel armor',sector,role),role==R);return
    if role==old.DARK:m.keep(t,role);return
    face=float(z.mean());xy=np.column_stack((p[:,0],-p[:,1]));sgn=1 if p[:,0].mean()>0 else -1
    if abs(n[2])>.98:
        if abs(face-3.095)<2e-5:
            # One whole quiet field for each well. No mini-tiles across its back.
            m.chart(t,'green_clean',xy,(100,100),('rear well backing',sgn));return
        if abs(face-(rear-.045))<2e-5:
            y=float(p[:,1].mean())
            if y>CY+.73:
                rect=(-.405,CY+1.02,.405,CY+1.69)
                pale=lambda a:fixed(m,a,P,a[:,[0,1]],(-.62,CY+.74),(.62,CY+1.80),(.51,.852,.995,.272))
                clipped_field(m,t,[0,1],rect,P,(.156,.553,.489,.277),pale)
            elif y<CY-.50:
                rect=(-.37,CY-1.46,.37,CY-.73)
                pale=lambda a:fixed(m,a,P,a[:,[0,1]],(-.55,CY-1.56),(.55,CY-.515),(.51,.852,.995,.272))
                clipped_field(m,t,[0,1],rect,P,(.135,.851,.502,.570),pale)
            else:
                fixed(m,t,P3,p[:,[0,1]],(-.44,CY-.49),(.44,CY+.715),(.008,.495,.332,.005))
            return
        if role==R:
            m.chart(t,'red_pair',xy,(100,100),('front red armor',round(face,3)),True);return
        if role==D:
            m.chart(t,'quiet_brown',xy,(100,100),('inset face',round(face,3),sgn));return
        # Pale front crown and rear plate each have a calm common projection.
        # The center spine and the two openings provide the subdivision.
        m.chart(t,'quiet_pale',xy,(3.6,3.6),('drum main face',round(face,3)));return
    # All exposed cutout reveals are dark, including their formerly pale lips.
    # The small outer rims of raised front/back plates use panel03 instead.
    reveal=(z.min()>front+.085 and z.max()<front+.50) or (z.min()>3.09 and z.max()<rear-.088)
    if role==D or reveal:
        m.plane(t,'quiet_brown',(4,4));return
    m.plane(t,'quiet_trim',(3.5,3.5))


def roof(m,t,role):
    p=t[:,:3];n=old.normal(t)
    # The inherited form Builder normalizes metal to its brown semantic role.
    # On this roof only, those faces are the interior ceiling and hold reveals.
    if role==D:m.plane(t,'cargo',(2,2));return
    if role in (previous.HOLD,old.WARNING):previous.map_roof(m,t,role);return
    if abs(n[1])<.2:m.plane(t,'quiet_brown',(3,3));return
    distance=previous.roof_distance(p[:,2])
    if abs(n[0])>.1:
        w=np.array([previous.body.roof_w(z) for z in p[:,2]])
        y=np.array([previous.body.roof_y(z) for z in p[:,2]])
        across=np.hypot(abs(p[:,0])-w,p[:,1]-y)
        m.chart(t,'skin',np.column_stack((distance,across)),(3.2,2),('roof shoulder',int(np.sign(p[:,0].mean()))))
    else:
        # Three large sections, aligned to actual changes in roof height.
        for a,b in [(-4.25,-1.50),(-1.50,-.70),(-.70,2.24)]:
            if a-1e-6<=p[:,2].mean()<=b+1e-6:
                assert p[:,2].min()>=a-1e-6 and p[:,2].max()<=b+1e-6
                fixed(m,t,P,np.column_stack((p[:,0],previous.roof_distance(p[:,2]))),
                    (-1.20,previous.roof_distance(a)),(1.20,previous.roof_distance(b)),(.51,.272,.995,.852))
                break


def receiver(m,t,role,name):
    p=t[:,:3];n=old.normal(t)
    if name=='Tapered_lower_receiver':
        if n[1]<-.45:
            fixed(m,t,P,p[:,[0,2]],(-1.07,1.48),(1.07,3.14),(.51,.272,.995,.852))
        else:m.plane(t,'skin',(3,3))
    elif role==D:m.plane(t,'quiet_brown',(4,4))
    elif n[2]>.9:m.chart(t,'skin',p[:,[0,1]],(100,100),'lower receiver frame')
    else:m.plane(t,'quiet_trim',(3,3))


def engine_seat(m,t,role):
    p=t[:,:3]
    outer=1.64+.32*np.clip((p[:,2]-1.60)/.40,0,1)
    depth=outer-abs(p[:,0])
    if role==D or (.002<depth.max()<.20):m.plane(t,'quiet_brown',(3,3))
    elif depth.max()>.20:m.plane(t,'quiet_trim',(3,3))
    else:m.plane(t,'pale',(3,3))


def remap(entry):
    name=entry['name'];m=old.Mapper(name)
    for g in entry['groups']:
        for t in np.asarray(g['corners'],float):
            if name.endswith('_sculpted_engine'):engine(m,t,g['material'])
            elif name=='Armored_transverse_drum':drum(m,t,g['material'])
            elif name=='Sculpted_roof_shoulders':roof(m,t,g['material'])
            elif name in ('Stern_receiver_fascia','Tapered_lower_receiver'):receiver(m,t,g['material'],name)
            elif name.endswith('_integrated_engine_seat'):engine_seat(m,t,g['material'])
            else:
                # New mechanism: calm pale faces, panel03 outer shoulders,
                # dark contact surfaces. All remain exterior-native materials.
                n=old.normal(t)
                family='quiet_brown' if g['material']==D else 'quiet_trim' if abs(n[1])>.5 else 'pale'
                m.plane(t,family,(3.5,3.5))
    return m.finish()


def mechanism():
    s.OBJECTS.clear()
    for sign,label in [(-1,'Port'),(1,'Starboard')]:
        # A real open C guide. Its channel contains a separate sliding member.
        profile=np.array([[1.48,-1.47],[1.72,-1.47],[1.72,-1.385],[1.64,-1.385],
                          [1.64,-1.095],[1.72,-1.095],[1.72,-.99],[1.48,-.99]])
        profile[:,0]*=sign
        if np.sum(profile[:,0]*np.roll(profile[:,1],-1)-profile[:,1]*np.roll(profile[:,0],-1))<0:profile=profile[::-1]
        b=previous.B()
        # Concave C section: outward normals come from each contour edge,
        # never the centroid of the extrusion (which lies outside some walls).
        loops=s.panel(b,profile,2,1.27,[0,0,1],P)
        profile=loops[0]
        if np.sum(profile[:,0]*np.roll(profile[:,1],-1)-profile[:,1]*np.roll(profile[:,0],-1))<0:profile=profile[::-1]
        s.panel(b,profile,2,-1.95,[0,0,-1],P)
        for a,c in zip(profile,np.roll(profile,-1,axis=0)):
            d=c-a
            b.face([[a[0],a[1],-1.95],[c[0],c[1],-1.95],[c[0],c[1],1.27],[a[0],a[1],1.27]],
                P,model.PLAIN,[d[1],-d[0],0])
        s.add(label+'_slide_guide',b,'wing guide')
        b=previous.B()
        profile=np.array([[1.66,-1.365],[1.91,-1.365],[1.91,-1.115],[1.66,-1.115]])
        profile[:,0]*=sign;s.prism(b,profile,2,1.12,-1.08,D)
        # Two compact solid yokes carry the wing's longitudinal rotation axis.
        for a,bz in [(-.75,-.48),(.54,.81)]:
            poly=np.array([[1.81,-1.34],[2.015,-1.34],[2.015,-1.02],[1.81,-1.02]])
            poly[:,0]*=sign;s.prism(b,poly,2,bz,a,P)
        s.add(label+'_slide_carriage',b,'wing carriage')
    return copy.deepcopy(s.OBJECTS)


def motions():
    out={n:copy.deepcopy(v) for n,v in previous.motions().items() if v['kind']=='door'}
    for sign,label in [(-1,'Port'),(1,'Starboard')]:
        out[label+'_swept_wing']=dict(kind='wing',pivot=[sign*1.90,-1.13,0],axis=[0,0,1],
            angle_degrees=sign*100,translation=[0,0,-.80],slide_end=.38,turn_start=.38,
            contacts=[label+'_slide_carriage'])
        out[label+'_slide_carriage']=dict(kind='wing',pivot=[0,0,0],axis=[0,0,1],angle_degrees=0,
            translation=[0,0,-.80],slide_end=.38,turn_start=.38,
            contacts=[label+'_swept_wing'])
    return out


def motion_transform(m,phase):
    smooth=lambda x: max(0,min(1,x))**2*(3-2*max(0,min(1,x)))
    if m['kind']=='wing':
        slide=smooth(phase/m.get('slide_end',.30));start=m.get('turn_start',.25)
        turn=smooth((phase-start)/(1-start))
    else:slide=phase;turn=smooth(phase)
    angle=math.radians(m['angle_degrees'])*turn;axis=np.array(m['axis'],float);axis/=np.linalg.norm(axis)
    x,y,z=axis;k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    r=np.eye(3)+math.sin(angle)*k+(1-math.cos(angle))*(k@k)
    p=np.array(m['pivot']);delta=np.array(m.get('translation',[0,0,0]))*slide
    return r,p+delta-r@p


def main():
    assert shutil.disk_usage(model.ROOT).free>3*1024**3
    data=json.loads(SOURCE.read_text(encoding='utf8'));base=json.loads(BASE.read_text(encoding='utf8'))
    source_by_name={e['name']:e for e in data['objects']};raw={e['name']:e for e in base['objects']}
    # The user's open model is authoritative. Do not silently discard manual HPs.
    for ex in data['exports']:
        assert f.digest(Path(ex['file']))==ex['sha256'],('Edited CMP: import user hardpoints before rebuilding',ex['file'])
    assert f.digest(ALT)=='f77b661900c72dadc5bf779505108f28b7804ae2b9abdfc45b205bb8806a6c99'
    data['sources'][ALT.as_posix()]=f.digest(ALT)
    for path,digest in data['sources'].items():assert f.digest(Path(path))==digest,path
    uv.PATCHES.update(PATCHES);old.REPORT.clear()
    previous.s.OBJECTS.clear();previous.new_roof()
    rawroof=copy.deepcopy(next(e for e in previous.s.OBJECTS if e['name']=='Sculpted_roof_shoulders'))
    changes={'Sculpted_roof_shoulders':rawroof}
    for name in ('Port_sculpted_engine','Starboard_sculpted_engine','Armored_transverse_drum',
                 'Stern_receiver_fascia','Tapered_lower_receiver'):changes[name]=copy.deepcopy(raw[name])
    for name in ('Port_integrated_engine_seat','Starboard_integrated_engine_seat'):
        changes[name]=previous.refit_engine_seat(raw[name])
    added=mechanism();objects=[];checks=[];preserved=[]
    for original in data['objects']+added:
        name=original['name']
        if name.endswith('_covered_root'):continue
        entry=copy.deepcopy(changes.get(name,original))
        do_remap=name in changes or name.endswith(('_slide_guide','_slide_carriage'))
        groups=[dict(g,corners=np.array(g['corners'],float)) for g in entry['groups']]
        cleanup={}
        if do_remap:
            mapped=remap(dict(entry,groups=groups))
            try:mapped,cleanup=uv_mesh_seams.clean(mapped,groups,entry['authored_closed'])
            except AssertionError as exc:raise AssertionError((name,exc)) from exc
            assert abs(old.area(mapped)-old.area(groups))<max(1e-5,old.area(groups)*2e-5),name
            entry['groups']=mapped
        else:preserved.append(name)
        objects.append(entry)
        checks.append(dict(name=name,remapped=do_remap,cleanup=cleanup,
            triangles=sum(len(g['corners']) for g in entry['groups'])))
    motion=motions();OUT.mkdir(parents=True,exist_ok=True)
    header,_=f.mesh.read_tree(model.SOURCE.read_bytes());exports=[]
    for suffix,mode in [('open',None),('bay_open','door'),('folded','wing')]:
        posed=copy.deepcopy(objects)
        for e in posed:
            e['groups']=[dict(g,corners=np.asarray(g['corners'],float)) for g in e['groups']]
            if e['name'] in motion and motion[e['name']]['kind']==mode:
                r,t=motion_transform(motion[e['name']],1);e['groups']=f.base.world(e['groups'],r,t)
        ex=model.export_cmp(header,posed,OUT/f'rh_pir_fighter_f01_uv2_{suffix}.cmp',min_cross_area=1e-12)
        ex.update(pose=suffix,static_extended=suffix=='open',bay_open=suffix=='bay_open')
        previous.add_hardpoints(ex);exports.append(ex)
    data.update(objects=objects,exports=exports,revision='F01 UV/02',shape_source=SOURCE.as_posix(),
        shape_source_sha256=f.digest(SOURCE),total_triangles=sum(c['triangles'] for c in checks),
        blend_basename='rh_pir_fighter_f01_uv2.blend',motion=motion,preserved_objects=preserved,
        stage='Offline LOD0 UV and forward carriage/upward folding study. Static CMP poses; animation in Blender.',
        mechanism_source=dict(path=ALT.as_posix(),sha256=f.digest(ALT),
            actual='Rh_alt_elite Pris carrier -> Rev wing, +100 degrees from flight to folded. Original Pris travels laterally.',
            adaptation='User requested forward travel, then upward fold: -0.80 Z on a modeled C guide, followed by 100 degrees about longitudinal axis.'),
        form_notes=['Accepted main form/cabin/engines preserved; only the old wing carrier is replaced.',
            'One continuous chart across engine profile sections; panel03 drum rails and roof shoulders.',
            'Two complete native hatch motifs on rear spine; dark walls on real recesses.',
            'Whole wing above/below UV retained; sequential forward slide then upward fold.'])
    model.dump(OUT/'geometry.json',data)
    model.dump(OUT/'uv_report.json',dict(geometry_sha256=f.digest(OUT/'geometry.json'),
        source_sha256=f.digest(SOURCE),object_checks=checks,charts=old.REPORT))
    print(json.dumps(dict(output=str(OUT),triangles=data['total_triangles'],preserved=preserved),indent=2))


if __name__=='__main__':main()
