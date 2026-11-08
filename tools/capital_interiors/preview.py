"""Render the actual depot CMP for camera/occlusion inspection (software rasterizer).

This is an asset preview, not a screenshot of the game renderer.
"""
from pathlib import Path
import io
import math
import struct
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_station_lods as utf
from prepare import GAME, OUT


def model(path, materials=()):
    root = utf.read_tree(path.read_bytes())[1][0]
    lib = {utf.crc(n.name): utf.child(n, 'VMeshData').blob
           for n in utf.child(root, 'VMeshLibrary').children}
    transforms = {'Root': (np.eye(3), np.zeros(3))}
    compound = utf.child(root, 'Cmpnd')
    fix = utf.child(utf.child(compound, 'Cons'), 'Fix').blob
    for off in range(0, len(fix), 176):
        parent = fix[off:off+64].split(b'\0')[0].decode()
        name = fix[off+64:off+128].split(b'\0')[0].decode()
        pos = np.array(struct.unpack_from('<3f', fix, off+128))
        mat = np.array(struct.unpack_from('<9f', fix, off+140)).reshape(3,3)
        pm, pp = transforms[parent]
        transforms[name] = (mat @ pm, pos @ pm + pp)
    textures = {}
    mats = {}
    for material_root in [root] + [utf.read_tree(p.read_bytes())[1][0] for p in materials]:
      try:
        for tex in utf.child(material_root, 'Texture library').children:
            try:
                textures[tex.name.lower()] = np.array(Image.open(io.BytesIO(utf.child(tex, 'MIPS').blob)).convert('RGB'))
            except (StopIteration, OSError):
                pass
        for mat in utf.child(material_root, 'Material library').children:
            try:
                name = utf.child(mat, 'Dt_name').blob.split(b'\0')[0].decode().lower()
                mats[utf.crc(mat.name)] = textures.get(name)
            except StopIteration:
                pass
      except StopIteration:
        pass
    batches = []
    for part in compound.children:
        if part.name == 'Cons':
            continue
        name = utf.child(part, 'Object name').blob.split(b'\0')[0].decode()
        if name not in transforms:
            continue # Preview only: rotating gun proxies have no rigid Fix frame.
        filename = utf.child(part, 'File name').blob.split(b'\0')[0].decode()
        meshpart = utf.child(root, filename)
        try:
            ref = utf.child(utf.child(meshpart, 'VMeshPart'), 'VMeshRef').blob
        except StopIteration:
            ref = utf.child(utf.child(utf.child(utf.child(meshpart, 'MultiLevel'), 'Level0'), 'VMeshPart'), 'VMeshRef').blob
        key = struct.unpack_from('<I', ref, 4)[0]
        sv, nv, si, ni, sg, ng = struct.unpack_from('<6H', ref, 8)
        blob = lib[key]
        _, _, groups, indices, fvf, vertices = struct.unpack_from('<II4H', blob)
        assert fvf == 0x112, hex(fvf)
        ib = 16 + 12*groups
        vb = ib + 2*indices
        v = np.frombuffer(blob, dtype='<f4', count=vertices*8, offset=vb).reshape(-1,8)
        all_indices = np.frombuffer(blob, dtype='<u2', count=indices, offset=ib)
        mat, pos = transforms[name]
        offset = si
        for g in range(sg, sg+ng):
            material, start, _, count, _ = struct.unpack_from('<I4H', blob, 16+12*g)
            corners = v[all_indices[offset:offset+count].astype('int32') + start + sv].copy()
            corners[:,:3] = corners[:,:3] @ mat + pos
            batches.append((corners.reshape(-1,3,8), mats.get(material)))
            offset += count
    return batches


def render(batches, pos, forward, path):
    width, height = 800, 450
    zbuf = np.full((height,width), np.inf)
    rgb = np.zeros((height,width,3), dtype=np.uint8)
    rgb[:] = [13,20,34]
    forward = np.array(forward, dtype=float)
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0,1,0]); right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    basis = np.array([right, up, forward]).T
    # Freelancer's fovh is a horizontal HALF angle.
    focal = width/2/math.tan(math.radians(28))
    for triangles, tex in batches:
        for triangle in triangles:
            cam = (triangle[:,:3] - pos) @ basis
            polygon = [np.r_[p,uv] for p,uv in zip(cam,triangle[:,6:8])]
            clipped = []
            for a,b in zip(polygon, polygon[1:]+polygon[:1]):
                if a[2] >= .3:
                    clipped.append(a)
                if (a[2] >= .3) != (b[2] >= .3):
                    clipped.append(a+(b-a)*((.3-a[2])/(b[2]-a[2])))
            for k in range(1,len(clipped)-1):
                p = np.array([clipped[0],clipped[k],clipped[k+1]])
                q = p[:,:2]/p[:,2,None]*[focal,-focal]+[width/2,height/2]
                lo = np.maximum(np.floor(q.min(axis=0)).astype(int),[0,0])
                hi = np.minimum(np.ceil(q.max(axis=0)).astype(int),[width-1,height-1])
                if np.any(lo>hi):
                    continue
                x,y = np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
                a,b,c = q
                den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den)<1e-8:
                    continue
                w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
                w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
                w2=1-w0-w1
                iz=w0/p[0,2]+w1/p[1,2]+w2/p[2,2]
                mask=(w0>=0)&(w1>=0)&(w2>=0)&(iz>0)
                depth=1/np.maximum(iz,1e-12)
                region=np.s_[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
                mask &= depth<zbuf[region]
                if not mask.any():
                    continue
                if tex is None:
                    color=np.full((*x.shape,3),135,dtype=np.uint8)
                else:
                    uv=(w0[:,:,None]*p[0,3:]/p[0,2]+w1[:,:,None]*p[1,3:]/p[1,2]+w2[:,:,None]*p[2,3:]/p[2,2])/np.maximum(iz[:,:,None],1e-12)
                    color=tex[(np.mod(uv[:,:,1],1)*tex.shape[0]).astype(int).clip(0,tex.shape[0]-1),
                              (np.mod(uv[:,:,0],1)*tex.shape[1]).astype(int).clip(0,tex.shape[1]-1)]
                rgb[region][mask]=color[mask]
                zbuf[region][mask]=depth[mask]
    Image.fromarray(rgb).save(path)


if __name__ == '__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    batches=model(GAME/'DATA/BASES/RHEINLAND/rh_depot_deck.cmp')
    for name,mesh,material in [
        ('train','SHIPS/UTILITY/FREIGHT_TRAIN/train_consist.cmp','SHIPS/UTILITY/utility_misc.mat'),
        ('cruiser','SHIPS/LIBERTY/LI_CRUISER/li_cruiser.cmp','SHIPS/LIBERTY/li_capships.mat')]:
        ship=model(GAME/'DATA'/mesh,[GAME/'DATA'/material])
        positions=np.concatenate([a[0][:,:,:3].reshape(-1,3) for a in ship])
        lo,hi=positions.min(0),positions.max(0)
        center=(lo+hi)*.5
        distance=max(160,max((hi[2]-lo[2])*.5,(hi[1]-lo[1])*.9)*3.2)
        offset=np.array([-8+distance,2.7,0])-center
        for triangles,_ in ship:
            triangles[:,:,:3]+=offset
        render(batches+ship,[-8,2.7,0],[1,0,0],OUT/(name+'.png'))
    print('Rendered depot with actual train and cruiser meshes:',OUT)
