"""F01-inspired center body on the retained F14 UV/01 assembly. Offline LOD0."""
import copy
import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path
import numpy as np
import rh_fighter_f14_form as model
import rh_fighter_f14_detail as s

f=model.f
SOURCE=model.TOPIC/'prototypes/f14_uv_01/geometry.json'
ART=model.TOPIC/'concepts/round_01/rh_fighter_F01_sheet.png'
OUT=model.TOPIC/'prototypes/f01_body_01'
P,R,D=model.P,model.R,model.D
B=model.B

# F01: low forward deck, a rising diagonal shoulder and a taller aft block.
# The original lower chine and front interface retain the accepted attachments.
TOP=np.array([[-4.25,.40],[-3.94,.64],[-1.85,.66],[-1.50,.66],
              [-.70,1.42],[1.30,1.42],[2.24,.82]])
OUTLINE=np.concatenate((TOP,s.SIDE[5:]))
FRONT_PANEL=np.array([[-4.03,.28],[-1.80,.43],[-.98,-1.12],[-3.79,-1.50]])
VENT=np.array([[-1.30,.43],[-.55,1.22],[.89,1.22],[.18,-.76],[-.72,-.96]])
REAR_PANEL=np.array([[1.14,1.23],[1.96,.95],[1.88,-.20],[.55,-.76]])
ROOF=np.array([[-4.25,.72],[-3.94,1.00],[-1.85,1.02],[-1.50,1.02],
               [-.70,1.86],[1.30,1.86],[2.24,1.55]])


def roof_y(z):return float(np.interp(z,ROOF[:,0],ROOF[:,1]))
def roof_w(z):return float(np.interp(z,ROOF[:,0],[.91,.99,1.08,1.08,1.17,1.19,1.22]))


def cut(poly,axis,value,greater):return s.clip_poly(poly,axis,value,greater)


def flank(sign):
    b=B();n=np.array([sign,0,0]);front=sign*1.
    loops=s.panel(b,OUTLINE,0,front,n,P,holes=[FRONT_PANEL,VENT,REAR_PANEL])
    s.pocket(b,loops[1],0,front,sign*.86,n,R,P,.075,.055)
    s.pocket(b,loops[2],0,front,sign*.53,n,D,D,.075,.08)
    s.pocket(b,loops[3],0,front,sign*.88,n,R,P,.055,.045)
    s.panel(b,loops[0],0,sign*.14,-n,D)
    s.link(b,s.points(loops[0],0,sign*.14),s.points(loops[0],0,front),P)
    # Four thick sloping louvres span the well and enter its side walls.
    # Their shadow and thickness are authored geometry, not grille artwork.
    inner=s.offset(VENT,.07)
    for y in (-.60,-.16,.28,.72):
        poly=cut(cut(inner,1,y-.085,True),1,y+.085,False)
        if len(poly)<3:continue
        center=float(poly[:,0].mean());poly[:,0]+=.020*np.sign(poly[:,0]-center)
        outer=np.array([[sign*(.88-.15*(yy-y+.085)/.17),yy,z] for z,yy in poly])
        back=outer.copy();back[:,0]-=sign*.075
        b.face(outer,P,model.PLAIN,[sign,1,0]);b.face(back,D,model.PLAIN,[-sign,-1,0]);s.link(b,outer,back,D)
    def mapped(v):
        x,y,z=v;return [sign*(s.side_x(z,y)-(1-abs(x))),y,z]
    name=('Port' if sign<0 else 'Starboard')+'_carved_flank'
    s.add(name,b,'hull',True,map_point=mapped)


def roof():
    b=B()
    stations=sorted(set(ROOF[:,0])|{-3.94,-.40,-.28,.30,.37,.80,.87,1.14})
    for sign in (-1,1):
        for a,z in zip(stations,stations[1:]):
            ya=float(np.interp(a,TOP[:,0],TOP[:,1]));yz=float(np.interp(z,TOP[:,0],TOP[:,1]))
            b.face([[sign*s.side_x(a,ya),ya,a],[sign*s.side_x(z,yz),yz,z],
                    [sign*roof_w(z),roof_y(z),z],[sign*roof_w(a),roof_y(a),a]],P,model.PLAIN,[sign,1,0])
            b.face([[sign*.74,roof_y(a),a],[sign*roof_w(a),roof_y(a),a],
                    [sign*roof_w(z),roof_y(z),z],[sign*.74,roof_y(z),z]],P,model.PLAIN,[0,1,0])
        # Native moving lid needs a continuous open channel, including under
        # the higher aft tier. Its path and surrounding hold remain unchanged.
        for a,z in zip(stations,stations[1:]):
            if a>=-3.94 and z<=-.40:
                b.face([[sign*.74,roof_y(a),a],[sign*.74,roof_y(z),z],
                        [sign*.74,.65+.087487*(z+3.94),z],
                        [sign*.74,.65+.087487*(a+3.94),a]],D,model.PLAIN,[-sign,0,0])
    # Solid forward crosspiece and stepped aft bridge. Three rectangular
    # recessed fields articulate the raised F01 deck, without modeled fasteners.
    for a,z in zip(stations,stations[1:]):
        if a>=-3.94 and z<=-.40:continue
        ya,yz=roof_y(a),roof_y(z)
        lo=-.74;hi=.74
        pocket=any(a>=aa-1e-6 and z<=zz+1e-6 for aa,zz in [(-.28,.30),(.37,.80),(.87,1.14)])
        thickness=.21 if pocket else .08
        b.face([[lo,ya-thickness,a],[hi,ya-thickness,a],[hi,yz-thickness,z],[lo,yz-thickness,z]],D,model.PLAIN,[0,-1,0])
        if pocket:
            # Backing sits above the original lid envelope throughout its sweep.
            b.face([[-.63,ya-.15,a],[.63,ya-.15,a],[.63,yz-.15,z],[-.63,yz-.15,z]],D,model.PLAIN,[0,1,0])
            for sign in (-1,1):
                b.face([[sign*.74,ya,a],[sign*.74,yz,z],[sign*.63,yz,z],[sign*.63,ya,a]],P,model.PLAIN,[0,1,0])
                b.face([[sign*.63,ya,a],[sign*.63,yz,z],[sign*.63,yz-.15,z],[sign*.63,ya-.15,a]],D,model.PLAIN,[-sign,0,0])
            for zz,yy,sgn in [(a,ya,1),(z,yz,-1)]:
                b.face([[-.63,yy,zz],[.63,yy,zz],[.63,yy-.15,zz],[-.63,yy-.15,zz]],D,model.PLAIN,[0,0,sgn])
        else:
            b.face([[lo,ya,a],[hi,ya,a],[hi,yz,z],[lo,yz,z]],P,model.PLAIN,[0,1,0])
    # Close exposed lips at the cargo opening; the nose transition is retained.
    for z,sgn in [(-3.94,1),(-.40,-1)]:
        y=roof_y(z)
        bottom=1.18 if z==-.40 else y-.08
        b.face([[-.74,y,z],[.74,y,z],[.74,bottom,z],[-.74,bottom,z]],P,model.PLAIN,[0,0,sgn])
    s.add('Sculpted_roof_shoulders',b,'hull',False)


def provisional_uv(entry):
    """Give each structural region a readable native patch for CMP inspection.

    Form is the deliverable: this is not the final small-patch UV layout.
    """
    for g in entry['groups']:
        a=g['corners']
        for t in a:
            p=t[:,:3];n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-12)
            if entry['name'].endswith('_carved_flank') and abs(n[0])>.70:
                co=p[:,[2,1]]
                center=co.mean(0)
                if g['material']==R:
                    rect=FRONT_PANEL if center[0]<-.85 else REAR_PANEL
                    box=(.345,.325,.655,.463)
                else:
                    rect=OUTLINE if g['material']==P else VENT
                    box=(.510,.272,.995,.852)
                lo=rect.min(0);hi=rect.max(0)
                t[:,6:8]=np.array(box[:2])+(co-lo)/(hi-lo)*np.array([box[2]-box[0],box[3]-box[1]])
            # Other charts are the builder's face-aligned native crops.


def main():
    assert shutil.disk_usage(model.ROOT).free>3*1024**3
    data=json.loads(SOURCE.read_text(encoding='utf8'))
    for p,h in data['sources'].items():assert f.digest(Path(p))==h,p
    assert ART.is_file()
    s.OBJECTS.clear();flank(-1);flank(1);roof()
    replacement={e['name']:e for e in s.OBJECTS}
    for e in replacement.values():provisional_uv(e)
    old=copy.deepcopy(data['objects']);objects=[];preserved={}
    for e in old:
        if e['name'] in replacement:objects.append(replacement[e['name']])
        else:
            objects.append(e);preserved[e['name']]=hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest()
    for e in objects:
        for g in e['groups']:g['corners']=np.array(g['corners'],float)
    OUT.mkdir(parents=True,exist_ok=True)
    header,_=f.mesh.read_tree(model.SOURCE.read_bytes())
    exports=[model.export_cmp(header,objects,OUT/'rh_pir_fighter_f01_body_open.cmp',min_cross_area=1e-12),
             model.export_cmp(header,objects,OUT/'rh_pir_fighter_f01_body_bay_open.cmp',True,min_cross_area=1e-12)]
    data.update(objects=objects,exports=exports,revision='F01 body / 01: stepped hull and oblique louvred well on retained F14 assembly',
        stage='Offline LOD0 shape prototype. New hull UV provisional; native cockpit and retained parts unchanged.',
        shape_source=SOURCE.as_posix(),shape_source_sha256=f.digest(SOURCE),body_art=ART.as_posix(),
        body_art_sha256=f.digest(ART),preserved_objects=preserved,replaced_objects=list(replacement),
        total_triangles=sum(len(g['corners']) for e in objects for g in e['groups']),
        preview_name_prefix='form',position_decimals=9,blend_basename='rh_pir_fighter_f01_body.blend',
        form_notes=['F01 low front deck and tall aft shoulder, adapted around unchanged cargo sweep',
                    'Separate inset forward donor field and rear cheek, replacing the long capsule-shaped well',
                    'Oblique deep ventilation well with four solid inclined vanes per side',
                    'Three real depressed fields in the raised aft deck; no modeled rivets'])
    data['sources'][ART.as_posix()]=f.digest(ART)
    model.dump(OUT/'geometry.json',data)
    model.dump(OUT/'preservation.json',dict(source=SOURCE.as_posix(),source_sha256=f.digest(SOURCE),
        preserved=preserved,replaced=list(replacement),geometry_sha256=f.digest(OUT/'geometry.json'),
        installed=False,game_launched=False))
    for p,h in data['sources'].items():assert f.digest(Path(p))==h,p
    print(json.dumps(dict(output=OUT.as_posix(),triangles=data['total_triangles'],preserved=list(preserved),replaced=list(replacement)),indent=2))


def check():
    data=json.loads((OUT/'geometry.json').read_text(encoding='utf8'))
    source=json.loads(SOURCE.read_text(encoding='utf8'))
    before={e['name']:e for e in source['objects']}
    review=json.loads((OUT/'blender_check.json').read_text(encoding='utf8'))
    assert review['geometry_sha256']==f.digest(OUT/'geometry.json')
    assert review['saved_and_reopened'] and not review['lid_collisions']
    closed={e['name'] for e in data['objects'] if e['authored_closed']}
    for e in data['objects']:
        if e['name'] in data['preserved_objects']:
            assert e==before[e['name']],e['name']
            digest=hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest()
            assert digest==data['preserved_objects'][e['name']]
        else:
            for g in e['groups']:
                assert 'metal' not in data['materials'][str(g['material'])]['texture'].lower()
    for e in review['objects']:
        if e['name'] in closed:
            assert e['nonmanifold_edges']==e['inconsistent_winding_edges']==0
            assert e['signed_volume']>0
    limits=[]
    for exported in data['exports']:
        assert f.digest(Path(exported['file']))==exported['sha256']
        _,tree=f.mesh.read_tree(Path(exported['file']).read_bytes())
        for path,node in f.mesh.walk(tree):
            if path.endswith('/VMeshData'):
                _,_,groups,indices,fvf,vertices=struct.unpack_from('<II4H',node.blob)
                assert max(vertices,indices)<65536 and fvf==0x112
                limits.append(dict(path=path,vertices=vertices,indices=indices))
    for p,h in data['sources'].items():assert f.digest(Path(p))==h,p
    report=dict(status='passed',geometry_sha256=f.digest(OUT/'geometry.json'),
        blend_sha256=f.digest(Path(review['blend'])),preserved_objects=len(data['preserved_objects']),
        replaced_objects=data['replaced_objects'],closed_objects=len(closed),
        native_lid_phases=31,lid_collisions=[],mesh_limits=limits,
        installed=False,game_launched=False)
    model.dump(OUT/'validation.json',report)
    # Replace the obsolete diagnostic from an earlier rejected roof underside.
    model.dump(OUT/'lid_collision_debug.json',[])
    print('F01_BODY_CHECK_OK',data['total_triangles'],'triangles;',len(data['preserved_objects']),'unchanged objects')


if __name__=='__main__':
    check() if '--check' in sys.argv else main()
