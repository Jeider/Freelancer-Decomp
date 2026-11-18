"""Static unfolded outer contours; no vents, panel borders or mesh diagonals."""
import collections
import hashlib
import json
import struct as S
import numpy as np
import rh_concept_b_v2 as v
f,OUT=v.f,v.OUT


def vertex_key(p):return tuple(round(float(x),4) for x in p)
def authored_contours(pieces):
    """Continuous principal hull lines. No visibility-clipped loose fragments."""
    lines=[]
    def line(a,b):
        if np.linalg.norm(np.array(a)-b)>.0001:lines.append([np.array(a),np.array(b)])
    def loop(points):
        for a,b in zip(points,np.roll(points,-1,axis=0)):line(a,b)
    root=pieces['Root'];shift=np.array(json.loads((OUT/'build.json').read_text())['center_shift_native'])
    body=np.concatenate([np.array(g['corners'])[...,:3] for g in root[:3]])
    # Trace matching corners of the solid body's transverse hull sections.
    # Front/back loops close the outline; intermediate station rings are omitted.
    lo,hi=body[...,2].min(),body[...,2].max()
    zs=[lo+.00001,* (np.array([-5.30,-4.45,-3.20,-2.10155,-.1,2.135,4.627])+shift[2]),hi-.00001]
    rings=[]
    for z in zs:
        points=[]
        for t in body:
            for a,b in zip(t,np.roll(t,-1,axis=0)):
                if abs(a[2]-b[2])<1e-9:continue
                ratio=(z-a[2])/(b[2]-a[2])
                if 0<=ratio<=1:points.append(a+(b-a)*ratio)
        p=np.array(points);assert len(p)>2,z
        x0,y0=p[:,:2].min(0);x1,y1=p[:,:2].max(0)
        bottom=p[p[:,1]<y0+.0001];top=p[p[:,1]>y1-.0001]
        left=p[p[:,0]<x0+.0001];right=p[p[:,0]>x1-.0001]
        ring=np.array([[bottom[:,0].min(),y0,z],[bottom[:,0].max(),y0,z],
            [x1,right[:,1].min(),z],[x1,right[:,1].max(),z],
            [top[:,0].max(),y1,z],[top[:,0].min(),y1,z],
            [x0,left[:,1].max(),z],[x0,left[:,1].min(),z]])
        rings.append(ring)
    loop(rings[0]);loop(rings[-1])
    for a,b in zip(rings,rings[1:]):
        for p,q in zip(a,b):line(p,q)
    # Whole external C frame; tail hatch/pylons and seam between breakable and
    # surviving pieces do not get their own internal lines.
    poly=f.b.old.yz([[214,16],[148,16],[95,48],[95,124],[123,153],[207,153],
                    [207,133],[140,133],[116,112],[116,59],[154,36],[214,36]])
    sides=[np.column_stack((np.full(len(poly),x),poly))+shift for x in (-1.32,1.32)]
    for p in sides:loop(p)
    for i in (0,1,2,3,4,5):line(sides[0][i],sides[1][i])
    # The drum needs its outline only: no slots, centre rings or support spokes.
    center=f.b.old.point(0,[175,86])+shift;angle=(np.arange(20)+.5)*2*np.pi/20
    yz=center[1:]+2.01*np.column_stack((np.cos(angle),np.sin(angle)))
    rims=[np.column_stack((np.full(20,x),yz)) for x in (-1.04,1.04)]
    for p in rims:loop(p)
    for i in (0,5,10,15):line(rims[0][i],rims[1][i])
    for name,gs in pieces.items():
        p=np.concatenate([np.array(g['corners'])[...,:3].reshape(-1,3) for g in gs])
        if '_engine_' in name.lower():
            # Simple complete barrel, excluding nozzle/collar subdivision lines.
            low,high=p.min(0),p.max(0);c=(low+high)/2;angle=np.arange(10)*2*np.pi/10
            xy=c[:2]+(high[:2]-low[:2])/2*np.column_stack((np.cos(angle),np.sin(angle)))
            ends=[np.column_stack((xy,np.full(10,z))) for z in (low[2],high[2])]
            for q in ends:loop(q)
            for i in (0,2,5,7):line(ends[0][i],ends[1][i])
        elif '_wing_' in name.lower():
            from scipy.spatial import ConvexHull
            # Thin wing planform, without doubled upper/lower skin outlines.
            q=np.unique(np.round(p[:,[0,2]],5),axis=0);q=q[ConvexHull(q).vertices]
            loop(np.column_stack((q[:,0],np.full(len(q),p[:,1].mean()),q[:,1])))
    return lines


def main():
    pieces=json.loads((OUT/'wire_pieces.json').read_text());groups=[]
    for name,gs in pieces.items():
        if '_glass_' in name.lower() or 'upperarm' in name.lower() or name.lower().startswith('baydoor'):continue
        if '_tail_' in name.lower():gs=gs[:1]
        if name=='Root':gs=gs[:6]
        groups.extend(dict(g,corners=np.array(g['corners'])) for g in gs)
    kept=set();positions={}
    for a,b in authored_contours(pieces):
        ka,kb=vertex_key(a),vertex_key(b)
        positions[ka]=a;positions[kb]=b
        if ka!=kb:kept.add(tuple(sorted((ka,kb))))
    changed=True
    while changed:
        changed=False;adj=collections.defaultdict(set)
        for a,b in kept:adj[a].add(b);adj[b].add(a)
        for point,neighbours in adj.items():
            if len(neighbours)!=2:continue
            a,b=sorted(neighbours);u=positions[a]-positions[point];w=positions[b]-positions[point]
            if u@w/np.linalg.norm(u)/np.linalg.norm(w)>-.99995:continue
            kept.remove(tuple(sorted((a,point))));kept.remove(tuple(sorted((b,point))))
            kept.add(tuple(sorted((a,b))));changed=True;break
    # Valid native triangle VMesh backing; wire-only vertices appended after it.
    blob,vertices=f.mesh.pack(f.merge(groups));base=len(vertices)
    keys=sorted({key for e in kept for key in e});lookup={key:i for i,key in enumerate(keys)}
    extra=np.zeros((len(keys),8),'<f4');extra[:,:3]=[positions[k] for k in keys];extra[:,4]=1
    blob=bytearray(blob);S.pack_into('<H',blob,14,base+len(extra));blob+=extra.tobytes();blob=bytes(blob)
    indices=[lookup[k] for e in sorted(kept) for k in e]
    name='rh_b_v2_unfolded_outer_wire_'+hashlib.sha256(blob).hexdigest()[:16]+'.vms'
    wire=S.pack('<II4H',16,f.mesh.crc(name),base,len(keys),len(indices),len(keys))+np.array(indices,'<u2').tobytes()
    header,nodes=f.mesh.read_tree(v.DEST.read_bytes())
    library=f.mesh.child(nodes[0],'VMeshLibrary')
    library.children=[n for n in library.children if not n.name.startswith('rh_b_v2_unfolded_outer_wire_')]
    library.children.append(f.folder(name,f.mesh.Node('VMeshData',blob)))
    for file,partname in f.component_map(nodes).items():
        part=f.mesh.child(nodes[0],file);part.children=[n for n in part.children if n.name.lower()!='vmeshwire']
        if partname=='Root':part.children.append(f.folder('VMeshWire',f.mesh.Node('VWireData',wire)))
    v.DEST.write_bytes(f.mesh.write_tree(header,nodes))
    v.dump('wire_manifest.json',dict(source='LOD1 closed outer forms; no equipment pylons or drum spokes',
        pose='unfolded; baked in Root',edges=len(kept),vertices=len(keys),
        method='continuous principal contours traced from solid LOD forms; intermediate cross-sections omitted',
        coplanar_diagonals_removed=True,straight_segments_merged=True,
        lines=[[positions[a],positions[b]] for a,b in sorted(kept)]))
    print('OUTER WIRE',len(kept),'edges',len(keys),'vertices',flush=True)


if __name__=='__main__':main()
