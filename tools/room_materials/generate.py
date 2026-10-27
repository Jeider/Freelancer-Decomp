"""Generate room/character material sidecars; never modify models, UVs, THNs or diffuse.

Normal maps are conservative band-limited estimates, not recovered geometry.
Material semantics come from names/asset family, never from a dark-pixel=metal rule.
Requires numpy/Pillow (the existing asteroid_normals venv can be used).
"""
import argparse
import collections
import hashlib
import io
import json
import mmap
import struct
from pathlib import Path

import numpy as np
from PIL import Image
from profile_scope import scope_flag, normal_scale

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/room_materials'
DEST = OUT / 'assets/DATA_EXTRA/ROOM_MATERIALS'


def entries(path):
    """UTF leaf index: texture payloads remain on disk during the catalog pass."""
    with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as raw:
        if raw[:4] != b'UTF ': return []
        h = struct.unpack_from('<14I', raw)
        tree, strings, payload = h[2], h[6], h[9]
        result = []
        def walk(offset, parent):
            while True:
                at = tree + offset
                sibling, name, flags = struct.unpack_from('<3I', raw, at)
                begin = strings + name
                key = raw[begin:raw.find(b'\0', begin)].decode('latin1')
                full = parent + (key,)
                child = struct.unpack_from('<I', raw, at+16)[0]
                if flags & 16:
                    if child: walk(child, full)
                else:
                    size = struct.unpack_from('<I', raw, at+28)[0]
                    start = payload + child
                    assert 0 <= start <= start+size <= len(raw)
                    result.append((full, start, size, raw[start:start+size] if size < 4096 else None))
                if not sibling: break
                offset = sibling
        walk(0, ())
        return result


def read(ref):
    path, offset, size = ref
    with path.open('rb') as f:
        f.seek(offset)
        return f.read(size)


def classify(material, texture, source):
    name = (material+' '+texture).lower()
    if any(x in name for x in ('glass','window','sky','cloud','holo','smoke','news','exit','mission',
                               'lamp','light','flare','screen','monitor','horizon','planet','sun','starfield')):
        # Eyes often include "shiny", not "light"; original highlight layer is preserved.
        return None
    if 'eye' in name and not any(x in name for x in ('eyebrows','eyebrow_','lid','lash')):
        return ('eye', 0., .20, 1., 0.)
    if 'characters' in source.lower():
        if any(x in name for x in ('head','face','hand','skin')) and not any(x in name for x in ('hair','helmet')):
            return ('skin', .30, .58, .55, 1.)
        if 'teeth' in name: return ('teeth', 0., .42, .35, 0.)
        return ('cloth', .45, .84, .22, 0.)
    if any(x in name for x in ('poster','picture','pic-','banner','decal')): return None
    if any(x in name for x in ('metal','steel','chrome','pipe','rail')): return ('metal', .65, .46, .60, 0.)
    if any(x in name for x in ('cloth','textile','carpet','fabric')): return ('cloth', .55, .87, .20, 0.)
    if any(x in name for x in ('floor','granite','marble','table','wood')): return ('finish', .65, .58, .45, 0.)
    return ('interior', .60, .72, .30, 0.)


def packed_dds(data):
    """Linear RGBA8: normal XY, roughness, skin mask. Filter all mip levels."""
    h, w, _ = data.shape
    levels = []
    while True:
        levels.append(np.rint(np.clip(data[:, :, [2,1,0,3]], 0, 1)*255).astype(np.uint8).tobytes())
        if data.shape[:2] == (1,1): break
        nh, nw = max(1,data.shape[0]//2), max(1,data.shape[1]//2)
        data = np.stack([np.asarray(Image.fromarray(data[:,:,k]).resize((nw,nh),Image.Resampling.BOX)) for k in range(4)], axis=2)
    header = [124,0x2100F,h,w,w*4,0,len(levels)]+[0]*11
    header += [32,0x41,0,32,0x00ff0000,0x0000ff00,0x000000ff,0xff000000]
    header += [0x401008,0,0,0,0]
    return b'DDS '+struct.pack('<31I',*header)+b''.join(levels)


def derive(blob, role, roughness):
    image = Image.open(io.BytesIO(blob)).convert('RGB')
    # Compact sidecars; faces retain 512, other surfaces 256. Diffuse stays full-res.
    scale = min(1,(512 if role=='skin' else 256)/max(image.size))
    size = tuple(2**max(0,int(np.floor(np.log2(max(1,x*scale))))) for x in image.size)
    image = image.resize(size,Image.Resampling.LANCZOS)
    rgb = np.asarray(image,dtype=np.float32)/255
    lum = rgb @ np.array([.2126,.7152,.0722],np.float32)
    h,w = lum.shape
    spectrum=np.fft.rfft2(np.log1p(lum*4))
    fy=np.fft.fftfreq(h)[:,None];fx=np.fft.rfftfreq(w)[None,:]
    def blur(sigma):
        return np.fft.irfft2(spectrum*np.exp(-2*np.pi*np.pi*sigma*sigma*(fx*fx+fy*fy)),s=lum.shape)
    detail=blur(1.3)-blur(12)
    dx=(np.roll(detail,-1,1)-np.roll(detail,1,1))*.5
    dy=(np.roll(detail,-1,0)-np.roll(detail,1,0))*.5
    slope=np.hypot(dx,dy)
    gain=min(3.,.22/max(float(np.percentile(slope,95)),1e-5))
    atten=np.minimum(1,.35/np.maximum(slope*gain,1e-6))
    nx=-dx*gain*atten;ny=-dy*gain*atten
    if role in ('eye','teeth'): nx*=0;ny*=0
    nz=np.sqrt(1+nx*nx+ny*ny);nx/=nz;ny/=nz
    # Only a small micro-roughness variation; brightness is not a material class.
    rough=np.clip(roughness+np.clip(np.abs(detail)*.12,0,.06)-.015,.18,.95)
    mask=np.ones_like(lum)
    if role=='skin':
        # Suppress the effect in painted hair/mouth shadows; don't recolour the diffuse.
        mask=np.clip(lum/.12,0,1)
    packed=np.stack((nx*.5+.5,ny*.5+.5,rough,mask),axis=2).astype(np.float32)
    assert np.isfinite(packed).all()
    return packed_dds(packed),image,packed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root',type=Path,default=Path('D:/games/FL_MOD'))
    args=parser.parse_args();game=args.game_root.resolve()
    DEST.mkdir(parents=True,exist_ok=True)
    materials=[];textures=collections.defaultdict(list);file_hashes={};skipped=[]
    files=sorted(p for folder in ('BASES','CHARACTERS') for p in (game/'DATA'/folder).rglob('*')
                 if p.suffix.lower() in ('.cmp','.dfm','.3db','.mat','.txm'))
    for path in files:
        indexed=entries(path);mats=collections.defaultdict(dict)
        rel=path.relative_to(game).as_posix()
        for parts,offset,size,small in indexed:
            low=[x.lower() for x in parts]
            if 'material library' in low:
                k=low.index('material library')
                if len(parts)==k+3 and small is not None:
                    mats[parts[k+1]][parts[-1].lower()]=small
            if 'texture library' in low and parts[-1].lower() in ('mips','mip0'):
                k=low.index('texture library')
                if len(parts)==k+3:textures[parts[k+1].lower()].append((path,offset,size))
        for name,props in mats.items():
            texture=props.get('dt_name',b'').split(b'\0')[0].decode('latin1')
            kind=props.get('type',b'').split(b'\0')[0].decode('latin1')
            if not texture or not kind:continue
            profile=classify(name,texture,rel)
            if profile:materials.append((name,texture,path,profile,kind))
        if indexed:file_hashes[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
    print(f'Catalog: {len(files)} files, {len(materials)} eligible materials, {len(textures)} texture names',flush=True)
    keys={};generated={};records=[];previews=0
    for i,(name,texture,path,profile,kind) in enumerate(materials):
        refs=textures.get(texture.lower(),[])
        local=[r for r in refs if r[0]==path]
        refs=local or refs
        if not refs:
            skipped.append(dict(material=name,reason='diffuse not in base/character libraries'));continue
        blob=read(refs[0]);sha=hashlib.sha256(blob).hexdigest()
        if not local and any(hashlib.sha256(read(r)).hexdigest()!=sha for r in refs[1:]):
            skipped.append(dict(material=name,reason='ambiguous external texture'));continue
        key=(name+'|'+texture).lower()
        role,normal,rough,spec,skin=profile
        old_token=hashlib.sha256((sha+repr(profile)+'v1').encode()).hexdigest()[:32]+'.dds'
        token=hashlib.sha256((sha+repr(profile)+'v2').encode()).hexdigest()[:32]+'.dds'
        definition=(token,normal_scale(name,texture,normal),rough,spec,scope_flag(path.as_posix(),name,role))
        if keys.get(key) is not None and keys[key][:4]==definition[:4]:
            # A shared character/environment material keeps the milder scope.
            definition=(*definition[:4],max(keys[key][4],definition[4]))
        if key in keys and keys[key]!=definition:
            keys[key]=None;skipped.append(dict(material=name,reason='conflicting material identity'));continue
        if key in keys and keys[key] is None:continue
        if token not in generated:
            try:
                if (DEST/token).exists():
                    dds=(DEST/token).read_bytes()
                    assert dds[:4]==b'DDS '
                    original=packed=None
                elif (DEST/old_token).exists():
                    original=None
                    # Our own uncompressed BGRA8 format; avoid Pillow's slow
                    # generic DDS bit-mask decoder for thousands of sidecars.
                    raw=(DEST/old_token).read_bytes()
                    h,w=struct.unpack_from('<II',raw,12)
                    old=np.frombuffer(raw,dtype=np.uint8,count=h*w*4,offset=128).reshape(h,w,4)
                    scale=min(1,(512 if role=='skin' else 256)/max(w,h))
                    nh,nw=max(1,int(h*scale)),max(1,int(w*scale))
                    packed=old.reshape(nh,h//nh,nw,w//nw,4).mean(axis=(1,3),dtype=np.float32)[:,:,[2,1,0,3]]/255
                    dds=packed_dds(packed)
                else:dds,original,packed=derive(blob,role,rough)
            except (OSError,ValueError) as error:
                skipped.append(dict(material=name,reason=str(error)));continue
            (DEST/token).write_bytes(dds)
            generated[token]=dict(bytes=len(dds),sha256=hashlib.sha256(dds).hexdigest(),role=role,source=sha)
            if original is not None and previews<12 and ('trent' in texture.lower() or 'kusari' in texture.lower() or 'male1_head' in texture.lower()):
                preview=OUT/'previews';preview.mkdir(exist_ok=True)
                original.save(preview/f'{previews}_diffuse.png')
                Image.fromarray(np.rint(packed[:,:,:3]*255).astype(np.uint8)).save(preview/f'{previews}_packed.png')
                previews+=1
        keys[key]=definition
        records.append(dict(material=name,texture=texture,source=path.relative_to(game).as_posix(),role=role,map=token,type=kind))
        if i%200==0:print(f'{i}/{len(materials)} materials; {len(generated)} maps',flush=True)
    lines=[]
    for key,value in sorted(keys.items()):
        if value is None:continue
        token,normal,rough,spec,skin=value
        if any(c in key for c in '\r\n\t') or len(key)>1400:continue
        lines.append(f'{normal:.4f} {rough:.4f} {spec:.4f} {skin:.4f} {token} {key}')
    (DEST/'profiles.txt').write_bytes(('\n'.join(lines)+'\n').encode('latin1'))
    used={value[0] for value in keys.values() if value is not None}
    generated={key:value for key,value in generated.items() if key in used}
    report=dict(game=str(game),profiles=len(lines),maps=generated,materials=records,skipped=skipped,
                source_files=file_hashes,source_files_unchanged=True,total_map_bytes=sum(x['bytes'] for x in generated.values()))
    (OUT/'generation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(f'Generated {len(lines)} profiles, {len(generated)} maps, {report["total_map_bytes"]/1048576:.1f} MiB; skipped {len(skipped)}. Originals unchanged.',flush=True)


if __name__=='__main__':main()
