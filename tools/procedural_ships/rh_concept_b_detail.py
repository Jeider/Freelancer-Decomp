"""Concept B revision 02: art-led LOD0 geometry, articulated elbow wings, offline only."""
import argparse
import copy
import hashlib
import json
import math
import struct as S
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import rh_concept_b as previous
from rh_redesign_paths import CONCEPT_B_DETAIL, CONCEPTS

mesh, audit, base, common = previous.mesh, previous.audit, previous.base, previous.common
PANEL, METAL, DARK, GRILL = previous.PANEL, previous.METAL, previous.DARK, previous.GRILL
PANEL1, UV, RED = previous.PANEL1, previous.UV, previous.RED
OUT = CONCEPT_B_DETAIL
DEST = OUT / 'rh_concept_b_lod0.cmp'
INITIAL_BUDGET = 1514 * 3  # Superseded: user permits more LOD0 detail; native format limits remain mandatory.
STRUCT = mesh.crc('pir_r_panel01_256D')
INNER_DARK = mesh.crc('pir_r-dark gray')
ROOT_PIVOT = np.array([2.12, -1.05, 1.90])
ELBOW = np.array([3.47, -1.05, 1.90])
ARM_ANGLE, PANEL_ANGLE = np.radians([78., 12.])


class Builder(previous.Builder):
    allow_bay_metal = False

    def face(self, points, material=PANEL, uvbox=UV, normal=None, uv=None):
        if material in (METAL, DARK) and not self.allow_bay_metal:
            material, uvbox = STRUCT, previous.PLAIN_UV
        return super().face(points, material, uvbox, normal, uv)

    def prism(self, poly, low, high, axis=0, bevel=.065, material=PANEL, rim=METAL):
        """Beveled convex plate, specified in the two axes perpendicular to extrusion."""
        poly = np.asarray(poly, float)
        center = poly.mean(0)
        small = center+(poly-center)*(1-bevel)
        inset = min((high-low)*.25, .065)
        axes = [i for i in range(3) if i != axis]
        rings = []
        for d, shape in ((low, small), (low+inset, poly), (high-inset, poly), (high, small)):
            p = np.zeros((len(poly), 3))
            p[:, axis] = d
            p[:, axes] = shape
            rings.append(p)
        center3 = np.concatenate(rings).mean(0)
        for a, b in zip(rings, rings[1:]):
            for i in range(len(poly)):
                j = (i+1) % len(poly)
                q = np.array([a[i], a[j], b[j], b[i]])
                self.face(q, rim, UV, q.mean(0)-center3)
        normal = np.zeros(3)
        normal[axis] = 1
        self.face(rings[0], material, UV, -normal)
        self.face(rings[-1], material, UV, normal)

    def bar(self, a, b, width, depth, material=PANEL):
        """Beveled rectangular link with a visible broad face and a narrow chamfer."""
        a, b = np.array(a, float), np.array(b, float)
        direction = mesh.unit(b-a)
        u = mesh.unit(np.cross(direction, [1, 0, 0] if abs(direction[0]) < .9 else [0, 1, 0]))
        v = np.cross(direction, u)
        tmp = Builder()
        length = np.linalg.norm(b-a)
        tmp.prism([[-width/2, -depth/2], [width/2, -depth/2], [width/2, depth/2], [-width/2, depth/2]],
                  0, length, axis=2, material=material, rim=material)
        r = np.column_stack((u, v, direction))
        for g in base.world(tmp.groups(), r, a):
            self.tris[g['material']].extend(g['corners'])

    def ring(self, center, outer, inner, low, high, sides=16, axis=0, material=PANEL, buried_inner=False):
        center = np.array(center, float)
        axes = [i for i in range(3) if i != axis]
        rings = []
        angles = (np.arange(sides)+.5)*2*np.pi/sides
        for d, radius in ((high, outer), (high, inner), (low, inner), (low, outer)):
            p = np.tile(center, (sides, 1))
            p[:, axis] += d
            p[:, axes[0]] += np.cos(angles)*radius
            p[:, axes[1]] += np.sin(angles)*radius
            rings.append(p)
        for k, (a, b) in enumerate(zip(rings, rings[1:]+rings[:1])):
            if buried_inner and k == 1:
                continue
            for i in range(sides):
                j = (i+1) % sides
                q = np.array([a[i], a[j], b[j], b[i]])
                normal = q.mean(0)-center
                if k in (0, 2):
                    normal[:] = 0
                    normal[axis] = 1 if k == 0 else -1
                else:
                    normal[axis] = 0
                    if k == 1:
                        normal = -normal
                self.face(q, material, UV, normal)

    def bolt(self, center, radius=.065, axis=0, side=1):
        center = np.array(center, float)
        axes = [i for i in range(3) if i != axis]
        a = np.tile(center, (6, 1))
        angles = np.arange(6)*np.pi/3
        a[:, axes[0]] += radius*np.cos(angles)
        a[:, axes[1]] += radius*np.sin(angles)
        c = a.copy()
        c[:, axis] += side*.035
        normal = np.zeros(3);normal[axis] = side
        self.face(c, PANEL, UV, normal)
        for i in range(6):
            j=(i+1)%6
            q=np.array([a[i],a[j],c[j],c[i]])
            self.face(q,METAL,UV,q.mean(0)-(a.mean(0)+c.mean(0))/2)

    def louver(self, x, y, z, half_length, side, height=.14):
        # Broad horizontal blade with a sloping lip, raised from the dark backing.
        cross=np.array([[x,y-height/2],[x+side*.075,y-height*.30],
                        [x+side*.075,y+height*.25],[x,y+height/2]])
        a=np.column_stack((cross,np.full(4,z-half_length)))
        c=np.column_stack((cross,np.full(4,z+half_length)))
        self.face(a,PANEL,UV,[0,0,-1]);self.face(c,PANEL,UV,[0,0,1])
        center=(a.mean(0)+c.mean(0))/2
        for i in range(4):
            j=(i+1)%4
            q=np.array([a[i],a[j],c[j],c[i]])
            self.face(q,PANEL,UV,q.mean(0)-center)

    def socket(self, center, normal, radius=.15):
        # A real recessed circular fitting, aligned to its sloped armor panel.
        n=mesh.unit(np.array(normal,float))
        u=mesh.unit(np.cross([1,0,0] if abs(n[0])<.9 else [0,1,0],n))
        v=np.cross(n,u)
        r=np.column_stack((u,v,n))
        tmp=Builder()
        tmp.ring([0,0,0],radius,radius*.65,0,.035,sides=16,axis=2,material=STRUCT)
        angles=np.arange(16)*np.pi/8
        tmp.face(np.column_stack((radius*.65*np.cos(angles),radius*.65*np.sin(angles),np.full(16,.003))),
                 INNER_DARK,UV,[0,0,1])
        for g in base.world(tmp.groups(),r,np.array(center,float)):
            self.tris[g['material']].extend(g['corners'])


def mirrored_x(v, side):
    p = np.array(v, float)
    p[0] *= side
    return p


def frame_geometry(b):
    c = np.array([1.8, 4.65])
    outer = np.array([[5.15, 3.1], [5.15, 6.15], [3.8, 7.65], [-.15, 7.65],
                      [-1.60, 6.1], [-1.60, 3.1], [-.1, 1.60], [3.8, 1.60]])
    inner = c+(outer-c)*.715
    # Each armor sector has its own end face and chamfers; a continuous dark core joins them.
    for i in range(8):
        j = (i+1) % 8
        p = np.array([outer[i], outer[j], inner[j], inner[i]])
        mid = p.mean(0)
        p = mid+(p-mid)*.98
        b.prism(p, -.80, .80, material=PANEL, rim=PANEL)
        # Small burgundy repair plates at opposing ends, following the actual armor plane.
        if i in (0, 4):
            pc = mid+(p-mid)*np.array([.80, .70])
            for side in (-1, 1):
                q = np.column_stack((np.full(4, side*.807), pc))
                b.face(q, PANEL, RED, [side, 0, 0])
        for side in (-1,1):
            for yz in (p[0]*.14+mid*.86,p[1]*.14+mid*.86):
                b.bolt([side*.813,*yz],.045,side=side)
    center = np.array([0, 1.8, 4.65])
    for angle in (0, np.pi/2, np.pi, 3*np.pi/2):
        v = np.array([0, np.cos(angle), np.sin(angle)])
        b.bar(center+v*1.25, center+v*2.65, .43, .45, METAL)
    # Thick layered hub, inner dark face, broad relief louvers, restrained fasteners.
    b.radial(center, [(-.70, 1.40), (-.52, 1.56), (.52, 1.56), (.70, 1.40)], 32, cap=METAL)
    for side in (-1, 1):
        b.ring(center, 1.42, 1.19, *sorted([side*.70, side*.79]), sides=32)
        for y in (-.84, -.42, 0, .42, .84):
            half = math.sqrt(1.17**2-y*y)*.91
            b.louver(side*.795, center[1]+y, center[2], half, side, .17)
        for angle in np.arange(8)*np.pi/4:
            b.bolt([side*.80, center[1]+1.30*np.cos(angle), center[2]+1.30*np.sin(angle)], .055, side=side)
    # Rear rim clamp and top radiator fins from the concept.
    for z in (1.66, 7.60):
        b.prism([[1.37, z-.35], [2.02, z-.35], [2.12, z+.30], [1.30, z+.30]], -.90, .90)
        for side in (-1, 1):
            b.radial([0, 1.72, z], [(side*.91, .23), (side*.98, .20)] if side>0 else
                     [(side*.98, .20), (side*.91, .23)], 16, cap=METAL)
    for z in np.linspace(3.65, 5.45, 4):
        b.beam([-.66, 5.17, z], [.66, 5.17, z], .12, .12, METAL)


def engine_geometry(b, side):
    c = (side*1.73, -1.95, 0)
    b.radial(c, [(2.20, .61), (2.40, .80), (5.45, .80), (5.65, .69)], 24, axis=2, cap=GRILL)
    # Raised retaining bands on the barrel; the middle skin remains a broad quiet surface.
    for z in (2.65, 5.12):
        b.ring(c, .845, .795, z-.07, z+.07, sides=24, axis=2, material=METAL, buried_inner=True)
    # Open nozzle with a dark inner throat and recessed grill.
    b.ring(c, .71, .52, 5.63, 5.94, sides=24, axis=2, material=PANEL)
    a=(np.arange(24)+.5)*np.pi/12
    b.face(np.column_stack((c[0]+.515*np.cos(a),c[1]+.515*np.sin(a),np.full(24,5.62))),
           GRILL,(0,0,1,1),[0,0,1])
    b.prism([[side*1.35, 3.0], [side*2.12, 3.0], [side*2.12, 4.65], [side*1.35, 4.65]],
            -1.25, -1.10, axis=1, material=PANEL)


def body_geometry(b, original):
    sections = [(-1.95, 1.04, -1.55, .70), (-.40, 1.43, -1.65, 1.50),
                (1.45, 1.55, -1.65, 2.35), (3.50, 1.15, -1.55, 2.35)]
    b.loft(sections, omit_top=True)
    b.face([[-.728, .70, -1.95], [.728, .70, -1.95], [1.001, 1.50, -.40], [-1.001, 1.50, -.40]],
           PANEL, UV, [0, 1, 0])
    b.face([[-1.085, 2.35, 1.45], [1.085, 2.35, 1.45], [.805, 2.35, 3.50], [-.805, 2.35, 3.50]],
           PANEL, RED, [0, 1, 0])
    for side in (-1, 1):
        b.socket([side*.52,1.145,-1.10],[0,1,-.80/1.55],.145)
        b.face([[side*.74, 1.50, -.40], [side*1.001, 1.50, -.40],
                [side*1.085, 2.35, 1.45], [side*.74, 2.35, 1.45]], PANEL, UV, [0, 1, 0])
        # Layered lower cheek armor, separated from the large inset vent above.
        b.prism([[-1.40, -1.30], [-.15, -1.30], [.14, -.75], [.14, .68], [-1.40, 1.10]],
                *sorted([side*1.28, side*1.57]), material=PANEL)
        b.face([[side*1.578, -1.28, -.70], [side*1.578, -.24, -.70],
                [side*1.578, -.24, .12], [side*1.578, -1.28, .12]], PANEL, RED, [side, 0, 0])
        b.prism([[-.06, -.05], [1.24, -.05], [1.24, 1.62], [-.06, 1.62]],
                *sorted([side*1.45, side*1.61]), material=METAL)
        for y in (.16, .44, .72, 1.0):
            b.louver(side*1.62, y, .78, .70, side, .15)
        # Heavy diagonal shoulder support, with actual circular pivot bosses.
        b.prism([[-1.03, 1.18], [-.94, 1.98], [2.63, 3.16], [2.88, 2.68]],
                *sorted([side*1.60, side*1.85]), material=PANEL, rim=PANEL)
        for y, z, radius in ((-.78, 1.62, .34), (2.53, 2.79, .29)):
            b.radial([0, y, z], [(side*1.86, radius), (side*1.97, radius*.85)] if side>0 else
                     [(side*1.97, radius*.85), (side*1.86, radius)], 24, cap=METAL)
            b.bolt([side*1.982,y,z],radius*.26,side=side)
        # Open neck: heavier rails and an X brace instead of a cut-down slab.
        for y in (-1.27, .18):
            b.bar([side*.76, y, -3.85], [side*.84, y+.12, -1.83], .20, .20)
        b.beam([side*.77, -1.18, -3.70], [side*.83, .20, -1.92], .15, .15, METAL)
        b.beam([side*.77, .14, -3.70], [side*.83, -1.15, -1.92], .15, .15, METAL)
        for z, y in ((-3.72, -.57), (-1.92, -.47)):
            b.radial([0, y, z], [(side*.88, .24), (side*.96, .20)] if side>0 else
                     [(side*.96, .20), (side*.88, .24)], 16, cap=METAL)
        # Short reinforcing rim at the lower belly, following the torso silhouette.
        b.bar([side*1.18, -1.46, -.68], [side*1.24, -1.46, 2.55], .16, .18, METAL)
    cabin=common.cockpit(original)
    for g in cabin:
        if g['material'] in (METAL,DARK):
            # Keep the original cabin geometry/normals/UVs, replace only the interior
            # material ID that conflicts with the user's new global convention.
            g['material']=INNER_DARK
    return cabin+b.groups()


def arm_geometry(b, side):
    root, elbow = mirrored_x(ROOT_PIVOT, side), mirrored_x(ELBOW, side)
    # Bearing runs fore/aft: its visible end disks describe the true folding axis.
    for center, radius in ((root, .40), (elbow, .34)):
        b.radial(center, [(-.53, radius*.88), (-.42, radius), (.43, radius), (.53, radius*.88)],
                 24, axis=2, cap=METAL)
    b.bar(root, elbow, .48, .58, PANEL)


def wing_geometry(b, side):
    poly = np.array([[3.51, .91], [5.94, 1.00], [6.23, 1.27], [6.18, 2.82], [5.96, 3.01], [3.51, 2.93]])
    poly[:, 0] *= side
    b.prism(poly, -1.24, -.87, axis=1, bevel=.055, material=PANEL, rim=PANEL)
    # A broad upper armor skin and a distinct end cap, not a thin aircraft wing.
    panel = np.array([[3.72, 1.10], [5.79, 1.18], [5.82, 2.79], [3.72, 2.74]])
    panel[:, 0] *= side
    b.prism(panel, -.872, -.81, axis=1, bevel=.045, material=PANEL, rim=METAL)
    # Empty weapon socket, left separate from the gun model.
    center = [side*4.90, -.78, 1.95]
    b.ring(center, .27, .14, 0, .035, sides=12, axis=1, material=METAL)
    b.face([[side*4.52, -.775, 1.56], [side*5.28, -.775, 1.56],
            [side*5.28, -.775, 2.34], [side*4.52, -.775, 2.34]], PANEL, common.SERVICE_UV, [0, 1, 0])
    for x in (3.85, 5.72):
        for z in (1.30, 2.62):
            b.bolt([side*x, -.80, z], .045, axis=1)


def door_geometry(b, side):
    p = np.array([[side*.015, 1.50, -.40], [side*.74, 1.50, -.40],
                  [side*.74, 2.35, 1.45], [side*.015, 2.35, 1.45]])
    b.face(p, PANEL, UV, [0, 1, 0])
    b.allow_bay_metal=True
    b.face(p-[0, .065, 0], METAL, UV, [0, -1, 0])
    b.allow_bay_metal=False
    for i in range(4):
        j = (i+1) % 4
        q = np.array([p[i], p[j], p[j]-[0,.065,0], p[i]-[0,.065,0]])
        b.face(q, METAL, UV, q.mean(0)-(p.mean(0)-[0,.03,0]))
    # Low raised inset follows the roof slope, leaving a fine border.
    q = p.mean(0)+(p-p.mean(0))*.82+[0,.018,0]
    b.face(q, PANEL, RED, [0,1,0])
    b.socket([side*.38,1.732,.10],[0,1,-.85/1.85],.13)


def design(part, original):
    name = part.lower()
    b = Builder()
    side = -1 if '_port_' in name or 'baydoor01' in name else 1
    if name.startswith('rh_elite_'):
        return body_geometry(b, original)
    if '_tail_' in name:
        frame_geometry(b)
    elif '_engine_' in name:
        engine_geometry(b, side)
    elif '_upperarm_' in name:
        arm_geometry(b, side)
    elif '_wing_' in name:
        wing_geometry(b, side)
    elif name.startswith('baydoor'):
        door_geometry(b, side)
    else:
        return original
    return b.groups()


def str64(s):
    return s.encode('ascii').ljust(64, b'\0')


def make_rev(parent, name, origin, axis, maximum):
    return str64(parent)+str64(name)+S.pack('<20f', *origin, 0,0,0, *np.eye(3).ravel(), *axis, 0, maximum)


def animated_angles(fold):
    # The elbow starts first, then the heavy root link follows. Both settle vertically.
    def smooth(t):
        t=np.clip(t,0,1)
        return float(t*t*(3-2*t))
    return ARM_ANGLE*smooth((fold-.06)/.94), PANEL_ANGLE*smooth(fold/.72)


def relocate_and_rig(nodes):
    # Start from native names, retaining the gameplay animation entry points.
    previous.relocate(nodes)
    root = nodes[0]
    cmpnd = mesh.child(root, 'Cmpnd')
    cons = mesh.child(cmpnd, 'Cons')
    rev = mesh.child(cons, 'Rev')
    arm_names = {}
    for side, label in ((-1,'port'),(1,'starboard')):
        file_name = f'Rh_{label}_upperarm_concept_b.3db'
        object_name = f'Rh_{label}_upperarm'
        wing_object = f'Rh_{label}_wing_lod1'
        template = next(n for n in root.children if f'Rh_{label}_wing_' in n.name)
        new = copy.deepcopy(template)
        new.name = file_name
        new.children = [n for n in new.children if n.name.lower() != 'hardpoints']
        root.children.append(new)
        entry = mesh.Node('Part_'+object_name)
        max_index=max(S.unpack('<I', mesh.child(n,'Index').blob)[0] for n in cmpnd.children if n.name != 'Cons')
        entry.children=[mesh.Node('File name',file_name.encode()+b'\0'),mesh.Node('Object name',object_name.encode()+b'\0'),
                        mesh.Node('Index',S.pack('<I',max_index+1))]
        cmpnd.children.append(entry)
        arm_names[wing_object.lower()] = object_name
        rev.blob += make_rev('Root',object_name,mirrored_x(ROOT_PIVOT,side),[0,0,side],ARM_ANGLE)
    for n in cons.children:
        size = 176 if n.name.lower()=='fix' else 208
        data=bytearray(n.blob)
        for at in range(0,len(data),size):
            name=mesh.string(data[at+64:at+128]).lower()
            f=np.frombuffer(data,'<f4',(size-128)//4,at+128)
            side=-1 if '_port_' in name or 'baydoor01' in name else 1
            if '_engine_' in name:
                f[:3]=[side*1.73,-1.95,4.10]
            elif '_tail_' in name:
                f[:3]=[0,1.8,4.65]
            elif '_wing_' in name:
                data[at:at+64]=str64(arm_names[name])
                f[:3]=mirrored_x(ELBOW-ROOT_PIVOT,side)
                f[3:6]=0
                f[6:15]=np.eye(3).ravel()
                f[15:18]=[0,0,side]
                f[18:20]=[0,PANEL_ANGLE]
            elif 'baydoor' in name:
                f[:3]=[side*.74,1.5,-.4]
                f[15:18]=mesh.unit(np.array([0,.85,1.85]))*(-side)
        n.blob=bytes(data)
    # Replace every native wing channel, including launch/keep/reset variants, and
    # add its parent link channel. No gameplay trigger or duration is invented.
    scripts=mesh.child(mesh.child(root,'Animation'),'Script')
    channel_count=0
    for script in scripts.children:
        added=[]
        for joint in list(script.children):
            child=mesh.string(mesh.child(joint,'Child name').blob).lower()
            if child not in arm_names:
                continue
            channel=mesh.child(joint,'Channel')
            header=mesh.child(channel,'Header')
            frames_node=mesh.child(channel,'Frames')
            count,interval,kind=S.unpack('<IfI',header.blob)
            assert kind==1
            if interval<0:
                values=np.frombuffer(frames_node.blob,'<f4').reshape(count,2)
                times, angles=values[:,0],values[:,1]
            else:
                times=np.arange(count)*interval
                angles=np.frombuffer(frames_node.blob,'<f4')
            # Extra keys preserve source holds while making the elbow articulation visible.
            if times[-1] <= 10:
                ts=sorted(set(float(x) for a,c in zip(times,times[1:]) for x in np.linspace(a,c,17)))
            else:
                ts=times.tolist()  # Native force-extend sentinel interval.
            values=[animated_angles(float(np.interp(t,times,angles))/1.17808997631073) for t in ts]
            parent_joint=copy.deepcopy(joint)
            parent_joint.name='Joint map '+str(len(script.children)+len(added))
            mesh.child(parent_joint,'Child name').blob=arm_names[child].encode()+b'\0'
            mesh.child(parent_joint,'Parent name').blob=b'Root\0'
            mesh.child(joint,'Parent name').blob=arm_names[child].encode()+b'\0'
            for dest,index in ((joint,1),(parent_joint,0)):
                ch=mesh.child(dest,'Channel')
                mesh.child(ch,'Header').blob=S.pack('<IfI',len(ts),-1,1)
                mesh.child(ch,'Frames').blob=np.asarray([[t,v[index]] for t,v in zip(ts,values)],'<f4').tobytes()
                channel_count+=1
            added.append(parent_joint)
        script.children.extend(added)
    transforms,_=audit.transforms(nodes)
    for p,n in mesh.walk(nodes):
        if '/hardpoints/' not in p.lower() or not p.lower().endswith('/position'):
            continue
        part=p.split('/')[2].lower()
        hp=p.split('/')[-2].lower()
        side=-1 if '_port_' in part else 1
        target=None
        if '_wing_' in part:
            if hp.startswith('hpweapon'):target=[side*4.90,-.74,1.95]
            elif hp.startswith(('hpcontrail','hpdocklight')):target=[side*6.12,-1.02,2.8]
        elif '_engine_' in part:
            if hp.startswith('hpengine'):target=[side*1.73,-1.95,5.95]
            elif hp.startswith('hprunninglight'):target=[side*1.73,-1.95,2.2]
            elif hp.startswith('hpmass'):target=[side*1.73,-1.95,4.1]
        elif part.startswith('rh_elite_'):
            target={'dpport_wing':mirrored_x(ROOT_PIVOT,-1),'dpstarboard_wing':ROOT_PIVOT,
                    'dpport_engine':[-1.73,-1.95,4.1],'dpstarboard_engine':[1.73,-1.95,4.1],
                    'hpweapon03':[-.62,1.2,-1.1],'hpweapon04':[.62,1.2,-1.1]}.get(hp)
        if target is not None:
            r,t=transforms[part]
            n.blob=np.asarray(r.T@(np.asarray(target)-t),'<f4').tobytes()
    return channel_count


def evaluate_pose(nodes, phase=1, door=0):
    """Assemble LOD0 with angles sampled from the actual CMP channels."""
    posed=copy.deepcopy(nodes)
    data={p.lower():n.blob for p,n in mesh.walk(nodes)}
    values={}
    for p,b in data.items():
        if not p.endswith('/channel/header'):
            continue
        f=phase if '/sc_extend wing/' in p else door if '/sc_open baydoor/' in p else None
        if f is None:continue
        count,interval,kind=S.unpack('<IfI',b)
        assert interval==-1 and kind==1
        frames=np.frombuffer(data[p.rsplit('/',1)[0]+'/frames'],'<f4').reshape(count,2)
        child=mesh.string(data[p.rsplit('/channel/',1)[0]+'/child name']).lower()
        values[child]=float(np.interp(f*frames[-1,0],frames[:,0],frames[:,1]))
    for p,n in mesh.walk(posed):
        if not p.lower().endswith('/cons/rev'):continue
        data=bytearray(n.blob)
        for at in range(0,len(data),208):
            name=mesh.string(data[at+64:at+128]).lower()
            f=np.frombuffer(data,'<f4',20,at+128)
            angle=values.get(name,0)
            x,y,z=mesh.unit(f[15:18].astype(float))
            cross=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
            rotation=np.eye(3)*np.cos(angle)+(1-np.cos(angle))*np.outer([x,y,z],[x,y,z])+np.sin(angle)*cross
            f[6:15]=(rotation@f[6:15].reshape(3,3)).ravel()
        n.blob=bytes(data)
    return common.scene(posed,1,0)  # Zero values in native open/rest channels; uses posed constructs.


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    src=base.SOURCE.read_bytes()
    header,nodes=mesh.read_tree(src)
    before={p:n.blob for p,n in mesh.walk(nodes)}
    original_transforms,_=audit.transforms(nodes)
    libs={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    channels=relocate_and_rig(nodes)
    # This revision contains a single LOD, deliberately no derived distant meshes.
    for part in nodes[0].children:
        ml=next((n for n in part.children if n.name.lower()=='multilevel'),None) if part.blob is None else None
        if ml:
            ml.children=[n for n in ml.children if not n.name.lower().startswith('level') or n.name.lower()=='level0']
            mesh.child(ml,'Switch2').blob=S.pack('<2f',0,1000000)
    transforms,_=audit.transforms(nodes)
    library=mesh.child(nodes[0],'VMeshLibrary')
    wires,report,cockpit_expected={},[],None
    for p,n in list(mesh.walk(nodes)):
        if not p.lower().endswith('/vmeshref'):continue
        part=p.split('/')[2]
        assert '/level0/' in p.lower()
        if '_upperarm_' in part.lower():
            old=[]
        else:
            r,t=original_transforms[part.lower()]
            old=base.world(audit.extract(n.blob,libs),r,t)
        new=previous.merge(design(part,old))
        report.append(dict(part=part,triangles=sum(len(g['corners']) for g in new),groups=len(new)))
        if '_glass_' in part.lower():continue
        if part.lower().startswith('rh_elite_'):cockpit_expected=common.cockpit(old)
        r,t=transforms[part.lower()]
        blob,vertices=mesh.pack(base.world(new,r.T,-r.T@t))
        name='rh_b2_'+hashlib.sha256((p+hashlib.sha256(blob).hexdigest()).encode()).hexdigest()[:16]+'.vms'
        entry=mesh.Node(name)
        entry.children=[mesh.Node('VMeshData',blob)]
        library.children.append(entry)
        n.blob=mesh.make_ref(n.blob,name,blob,vertices)
        wires[part]=(blob,mesh.crc(name))
    triangles=sum(r['triangles'] for r in report)
    print('LOD0 triangles:',triangles,'(initial art budget:',INITIAL_BUDGET,'; now native limits only)',report,flush=True)
    for p,n in mesh.walk(nodes):
        part=p.split('/')[2] if len(p.split('/'))>2 else ''
        if p.lower().endswith('/vwiredata') and part in wires:
            blob,crc=wires[part]
            n.blob=previous.feature_wire(blob,crc)
    # Discard unreferenced old VMesh data so the single-LOD prototype stays self-contained.
    used={S.unpack_from('<I',n.blob,4)[0] for p,n in mesh.walk(nodes) if p.lower().endswith(('/vmeshref','/vwiredata'))}
    library.children=[n for n in library.children if mesh.crc(n.name) in used]
    output=mesh.write_tree(header,nodes)
    _,decoded=mesh.read_tree(output)
    flat={p:n.blob for p,n in mesh.walk(decoded)}
    dl={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(decoded) if p.lower().endswith('/vmeshdata')}
    material_table=audit.material_table([audit.DATA/p for p in base.ROW['materials']]+[base.SOURCE])
    max_vertices,max_indices,max_draw_triangles=0,0,0
    for mid,(vertices,groups,indices) in dl.items():
        assert len(vertices)<=65535 and len(indices)<=65535 and len(groups)<=65535
        max_vertices=max(max_vertices,len(vertices));max_indices=max(max_indices,len(indices))
        at=0
        for _,start,end,count,_ in groups:
            assert count%3==0 and 0<=start<=end<len(vertices)
            ids=indices[at:at+count]+start
            assert len(ids)==count and ids.min()>=start and ids.max()<=end
            assert count//3<=65535
            max_draw_triangles=max(max_draw_triangles,count//3)
            at+=count
        assert at==len(indices)
    for p,b in flat.items():
        if p.lower().endswith('/vmeshref'):
            groups=audit.extract(b,dl)
            if '/rh_elite_' in p.lower():
                expected=copy.deepcopy(cockpit_expected)
                for g in expected:
                    if g['material'] in (METAL,DARK):g['material']=INNER_DARK
                for g in previous.merge(expected):
                    a=next(a for a in groups if a['material']==g['material'])
                    assert np.array_equal(a['corners'][:len(g['corners'])].astype('<f4'),g['corners'].astype('<f4'))
            for g in groups:
                assert np.isfinite(g['corners']).all()
                assert np.allclose(np.linalg.norm(g['corners'][...,3:6],axis=-1),1,atol=1e-5)
                mat=material_table[g['material']]
                if 'metal' in mat['texture'].lower() or mat['name'].lower().startswith('metal'):
                    assert '/baydoor' in p.lower(), ('Forbidden exterior metal material',p,mat['name'])
        if '/hpcockpit/' in p.lower() or '/hppilot/' in p.lower() or ('/rh_glass_' in p.lower() and '/switch2' not in p.lower()):
            assert b==before[p],p
    poses=[evaluate_pose(decoded,float(t)) for t in np.linspace(0,1,41)]
    for pose in poses:
        assert np.isfinite(np.concatenate([g['corners'] for g in pose])).all()
    assert base.SOURCE.read_bytes()==src
    DEST.write_bytes(output)
    stats=dict(source=str(base.SOURCE),source_sha256=hashlib.sha256(src).hexdigest(),
               output_sha256=hashlib.sha256(output).hexdigest(),concept=str(CONCEPTS/'rh_concept_B.png'),
               initial_art_budget=INITIAL_BUDGET,art_budget='relaxed by user; retain native DX/index limits',
               triangles=triangles,lods=[0],parts=report,wing_channels=channels,sampled_poses=41,
               directx_format_checks=dict(index_format='D3DFMT_INDEX16',limit=65535,max_vertices_per_vmesh=max_vertices,
                    max_indices_per_vmesh=max_indices,max_triangles_per_draw=max_draw_triangles),
               metal_texture_policy='only baydoor interior; zero exterior references',
               cockpit='original vertex/normal/UV records preserved',
               cockpit_material_changes='metal03D/metal03DK replaced with pir_r-dark gray; geometry unchanged',
               wing_rig='two revolute joints per side; 78-degree root link plus 12-degree elbow; native script names/times',
               limitations=['offline prototype, not installed','SUR, damage caps and distant LODs deferred',
                            'textures reused from original; final art-directed UV pass deferred'])
    (OUT/'checks.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
    return decoded


def export(nodes):
    mats=audit.material_table([audit.DATA/p for p in base.ROW['materials']]+[base.SOURCE])
    opened,folded=evaluate_pose(nodes,1),evaluate_pose(nodes,0)
    base.export_obj(OUT/'rh_concept_b_open.obj',opened,mats)
    base.export_obj(OUT/'rh_concept_b_folded.obj',folded,mats)
    # Explicitly retain the object/parent hierarchy for a Blender mechanical rig.
    names={}
    for p,n in mesh.walk(nodes):
        if '/cmpnd/' in p.lower() and p.lower().endswith('/file name'):
            entry=next(x for x in mesh.child(nodes[0],'Cmpnd').children if x.name==p.split('/')[-2])
            names[mesh.string(n.blob)]=mesh.string(mesh.child(entry,'Object name').blob)
    joints={'Root':dict(parent=None,origin=[0,0,0],rotation=np.eye(3).tolist(),axis=[0,0,1])}
    for p,n in mesh.walk(nodes):
        if '/cmpnd/cons/' not in p.lower():continue
        rev=p.lower().endswith('/rev');size=208 if rev else 176
        for at in range(0,len(n.blob),size):
            parent=mesh.string(n.blob[at:at+64]);name=mesh.string(n.blob[at+64:at+128])
            f=np.frombuffer(n.blob,'<f4',(size-128)//4,at+128).astype(float)
            joints[name]=dict(parent=parent,origin=f[:3].tolist(),rotation=f[6:15 if rev else 12].reshape(3,3).tolist() if rev else f[3:12].reshape(3,3).tolist(),
                              axis=f[15:18].tolist() if rev else [0,0,1])
    libs={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    objects=[]
    for p,n in mesh.walk(nodes):
        if not p.lower().endswith('/vmeshref'):continue
        part=p.split('/')[2]
        objects.append(dict(name=names[part],file=part,joint=joints[names[part]],
            groups=[dict(material=g['material'],corners=g['corners'].tolist()) for g in audit.extract(n.blob,libs)]))
    animation=[]
    for p,n in mesh.walk(nodes):
        if '/sc_extend wing/' not in p.lower() or not p.lower().endswith('/channel/frames'):continue
        flat={q.lower():v.blob for q,v in mesh.walk(nodes)}
        name=mesh.string(flat[p.lower().rsplit('/channel/',1)[0]+'/child name'])
        animation.append(dict(object=name,keys=np.frombuffer(n.blob,'<f4').reshape(-1,2).tolist()))
    export=dict(objects=objects,animation=animation,materials={str(k):dict(name=v['name'],texture=v['texture'].rsplit('.',1)[0]+'.png' if v['image'] else None,
                  colour=v['colour'].tolist()) for k,v in mats.items() if k in {g['material'] for g in opened}},
                concept=str(CONCEPTS/'rh_concept_B.png'),initial_art_budget=INITIAL_BUDGET)
    (OUT/'blender_scene.json').write_text(json.dumps(export,separators=(',',':')),encoding='utf8')
    # Quick real-mesh renders allow proportion review before the Blender presentation.
    for m in mats.values():
        if m['image']:m['image']=m['image'].resize((512,512))
    points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in opened+folded])
    center=(points.min(0)+points.max(0))/2
    radius=np.linalg.norm(points-center,axis=1).max()
    for name,sc in (('model',opened),('folded',folded)):
        audit.render(sc,mats,center,radius,(1,.62,-1.15),1100,'clay').save(OUT/(name+'_clay.jpg'),quality=95)
        audit.render(sc,mats,center,radius,(1,.62,-1.15),1100,'texture').save(OUT/(name+'_texture.jpg'),quality=95)
    (OUT/'README.txt').write_text(
        'RH CONCEPT B — revision 02. Только первый LOD (Level0).\n'
        'Пользователь снял художественный потолок 4542 треугольника; 16-битные ограничения CMP/DirectX соблюдены. Числа — checks.json.\n'
        'Исходная кабина сохранена. Рама, барабан с жалюзи, броня, двигатели и ферма переработаны по арту.\n'
        'Крылья используют два шарнира на сторону: плечо 78°, локоть 12°. Родные имена анимационных скриптов сохранены.\n'
        'Metal/metal03 только внутри baydoor. У исходной кабины заменены только старые metal ID, вершины/нормали/UV сохранены.\n'
        'rh_concept_b_lod0.cmp — модель; OBJ — открытая/сложенная позы; blender_scene.json — меши, иерархия и ключи.\n'
        'rh_concept_b_rigged.blend — сцена с шарнирами; geometry_open.png — геометрия; wing_mechanism.mp4 — анимация.\n'
        'У материалов Blender переключатель Texture blend: 0 — обзор геометрии, 1 — исходная текстура.\n'
        'Пушки отдельные. В игре не установлено. Дальние LOD, SUR, damage caps и финальная UV-развёртка отложены.\n',encoding='utf8')
    print('Exported:',OUT,flush=True)


def package():
    with zipfile.ZipFile(OUT/'rh_concept_b_revision_02.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in OUT.iterdir():
            if p.is_file() and p.suffix not in ('.zip','.blend1'):
                z.write(p,p.name)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--package-only',action='store_true')
    args=parser.parse_args()
    if args.package_only:package()
    else:export(build())
