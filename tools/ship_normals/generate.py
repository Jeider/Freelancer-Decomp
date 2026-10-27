"""Generate strong ship relief sidecars. Authored darkness is a recess; DATA stays untouched."""
import sys, io, hashlib, json, collections, importlib.util
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from solar_content import HUMAN_LIBRARIES, artificial_material, human_solars
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/room_materials'))
spec=importlib.util.spec_from_file_location('room_normal_generator',ROOT/'tools/room_materials/generate.py')
room=importlib.util.module_from_spec(spec);spec.loader.exec_module(room)
entries,read,packed_dds=room.entries,room.read,room.packed_dds
OUT=ROOT/'src/obj/ship_normals';RAW=OUT/'raw';DEST=OUT/'assets/DATA_EXTRA/SHIP_NORMALS'
GAME=Path('D:/games/FL_MOD')

def derive(blob):
    im=Image.open(io.BytesIO(blob)).convert('RGB')
    scale=min(1.,512/max(im.size));size=tuple(2**max(0,int(np.floor(np.log2(max(1,v*scale))))) for v in im.size)
    im=im.resize(size,Image.Resampling.LANCZOS)
    lum=np.asarray(im,dtype=np.float32)@np.array([.2126,.7152,.0722],np.float32)/255
    h,w=lum.shape;freq=np.fft.rfft2(lum);fy=np.fft.fftfreq(h)[:,None];fx=np.fft.rfftfreq(w)[None,:]
    def blur(s):return np.fft.irfft2(freq*np.exp(-2*np.pi*np.pi*s*s*(fx*fx+fy*fy)),s=lum.shape)
    height=blur(1.0)-.35*blur(24.0) # preserve the artist's broad recesses, suppress pixel/compression noise
    dx=(np.roll(height,-1,1)-np.roll(height,1,1))*.5;dy=(np.roll(height,-1,0)-np.roll(height,1,0))*.5
    gain=min(20.,.55/max(float(np.percentile(np.hypot(dx,dy),95)),.01))
    nx=-dx*gain;ny=-dy*gain;z=np.sqrt(1+nx*nx+ny*ny);nx/=z;ny/=z
    # DXT5nm: independent high-quality alpha X and green Y. Shader reconstructs Z.
    data=np.stack((np.ones_like(nx),ny*.5+.5,np.zeros_like(nx),nx*.5+.5),axis=2).astype(np.float32)
    assert np.isfinite(data).all()
    return packed_dds(data),im,data

def derive_surface(im):
    # Separate BC1 texture keeps the independent DXT5nm green channel intact.
    im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.LANCZOS)
    rgb=np.asarray(im.filter(ImageFilter.GaussianBlur(1.2)),dtype=np.float32)/255
    lum=rgb@np.array([.2126,.7152,.0722],np.float32)
    saturation=(rgb.max(axis=2)-rgb.min(axis=2))/np.maximum(rgb.max(axis=2),.05)
    neutral=1-np.clip((saturation-.08)/.24,0,1)
    # Conservative coverage estimate, not a claim to identify painted grey as bare metal.
    metal=.55*neutral*np.clip((lum-.12)/.40,0,1)*(1-.65*np.clip((lum-.75)/.20,0,1))
    rough=np.clip(.72-.22*metal-.08*lum,.52,.76)
    broad=np.asarray(im.filter(ImageFilter.GaussianBlur(5)),dtype=np.float32)/255
    broad_lum=broad@np.array([.2126,.7152,.0722],np.float32)
    cavity=1-.08*np.clip((broad_lum-lum)/.15,0,1)
    data=np.stack((rough,metal,cavity,np.ones_like(lum)),axis=2)
    return packed_dds(data),im.size

def main():
    RAW.mkdir(parents=True,exist_ok=True);DEST.mkdir(parents=True,exist_ok=True)
    files=sorted(p for p in (GAME/'DATA/SHIPS').rglob('*') if p.suffix.lower() in ('.mat','.cmp','.3db','.txm'))
    solar_models=human_solars(GAME)
    files+=sorted(p for p in (GAME/'DATA/SOLAR').glob('*.mat') if p.name.lower() in HUMAN_LIBRARIES)
    files+=sorted(GAME/'DATA'/p for p in solar_models if (GAME/'DATA'/p).is_file())
    textures=collections.defaultdict(list);materials=[];excluded=set();source_files={};skipped=[]
    for path in files:
        props=collections.defaultdict(dict);indexed=entries(path)
        for parts,off,size,small in indexed:
            low=[x.lower() for x in parts]
            if 'texture library' in low and low[-1] in ('mip0','mips'):textures[parts[-2].lower()].append((path,off,size))
            if 'material library' in low and small is not None:props[parts[-2]][parts[-1].lower()]=small
        blocked='nmd' in path.as_posix().lower() or 'nomad' in path.as_posix().lower()
        for name,p in props.items():
            texture=p.get('dt_name',b'').split(b'\0')[0].decode('latin1')
            label=(name+'|'+texture).lower();kind=p.get('type',b'').split(b'\0')[0].decode('latin1')
            if 'nmd' in label or 'nomad' in label:blocked=True
            if path.relative_to(GAME/'DATA').parts[0].lower()=='solar' and not artificial_material(name,texture):continue
            if not texture or 'Dt' not in kind or 'et_name' in p or any(x in label for x in
                ('nmd','nomad','glass','window','light','engine','glow','screen','cockpit','holo','flame')):continue
            materials.append((name,texture,path))
        if blocked:excluded.add(path.relative_to(GAME/'DATA').as_posix().lower())
    print(f'Catalog: {len(materials)} candidate materials, {len(textures)} textures; {len(excluded)} excluded assets',flush=True)
    families={'ships':{},'solar':{}};maps={};records=[];conflicts=set();surfaces={}
    for name,texture,path in materials:
        rel=path.relative_to(GAME/'DATA').as_posix().lower()
        family=rel.split('/')[0];profiles=families[family]
        if rel in excluded:continue
        key=(name+'|'+texture).lower()
        if (family,key) in conflicts:continue
        refs=[r for r in textures.get(texture.lower(),[]) if r[0].relative_to(GAME/'DATA').parts[0].lower()==family]
        # Embedded CMPs can carry stale copies of common station textures. Human
        # solar libraries hold the remastered authoritative shared panels.
        library_refs=[r for r in refs if r[0].parent==GAME/'DATA/SOLAR' and r[0].name.lower() in HUMAN_LIBRARIES]
        if family=='solar' and library_refs: refs=library_refs
        else: refs=[r for r in refs if r[0]==path] or refs
        if not refs:skipped.append([key,'missing diffuse']);continue
        blob=read(refs[0]);sha=hashlib.sha256(blob).hexdigest()
        if any(hashlib.sha256(read(r)).hexdigest()!=sha for r in refs[1:]):skipped.append([key,'ambiguous diffuse']);continue
        token=hashlib.sha256((sha+'ship-strong-dark-recess-v1').encode()).hexdigest()[:32]+'.dds'
        if key in profiles and profiles[key]!=token:
            conflicts.add((family,key));profiles.pop(key,None);skipped.append([key,'conflicting material']);continue
        if token not in maps:
            try:dds,im,packed=derive(blob)
            except (OSError,ValueError) as error:skipped.append([key,str(error)]);continue
            (RAW/token).write_bytes(dds)
            maps[token]={'source':sha,'width':im.width,'height':im.height,'kind':'normal'}
            if path.relative_to(GAME/'DATA').parts[0].lower()=='ships':
                surface=hashlib.sha256((sha+'ship-matte-surface-v1').encode()).hexdigest()[:32]+'.dds'
                surface_dds,size=derive_surface(im);(RAW/surface).write_bytes(surface_dds)
                maps[surface]={'source':sha,'width':size[0],'height':size[1],'kind':'surface'}
                surfaces[token]=surface
            if len(maps)<=4:
                im.save(OUT/f'preview_{len(maps)}_diffuse.png')
                xy=np.stack((packed[:,:,3]*2-1,packed[:,:,1]*2-1),axis=2)
                n=np.dstack((xy,np.sqrt(np.maximum(0,1-(xy*xy).sum(axis=2)))))
                Image.fromarray(np.rint((n*.5+.5)*255).astype(np.uint8)).save(OUT/f'preview_{len(maps)}_normal.png')
        profiles[key]=token;records.append({'material':key,'model':rel,'map':token})
        for f in (path,refs[0][0]):
            r=f.relative_to(GAME).as_posix()
            if r not in source_files:source_files[r]=hashlib.sha256(f.read_bytes()).hexdigest()
    for family,profiles in families.items():
        (DEST/('profiles.txt' if family=='ships' else 'solar_profiles.txt')).write_bytes(('\n'.join(v+' '+k for k,v in sorted(profiles.items()))+'\n').encode('latin1'))
    (DEST/'excluded_models.txt').write_bytes(('\n'.join(sorted(excluded))+'\n').encode('latin1'))
    (DEST/'human_solars.txt').write_text('\n'.join(sorted(solar_models))+'\n')
    source_files['DATA/SOLAR/solararch.ini']=hashlib.sha256((GAME/'DATA/SOLAR/solararch.ini').read_bytes()).hexdigest()
    used={v for profiles in families.values() for v in profiles.values()};surfaces={k:v for k,v in surfaces.items() if k in used}
    (DEST/'surface_profiles.txt').write_text('\n'.join(k+' '+v for k,v in sorted(surfaces.items()))+'\n')
    used.update(surfaces.values());maps={k:v for k,v in maps.items() if k in used}
    (OUT/'compression.txt').write_text('\n'.join(str(RAW/k)+'|'+str(DEST/k)+'|'+('DXT1' if maps[k]['kind']=='surface' else 'DXT5') for k in sorted(maps))+'\n')
    profile_count=sum(len(p) for p in families.values())
    (OUT/'generation.json').write_text(json.dumps(dict(game=str(GAME),profiles=profile_count,maps=maps,source_files=source_files,
        excluded=sorted(excluded),skipped=skipped,materials=records,surface_maps=surfaces),indent=2))
    print(f'Generated {len(maps)} maps, {profile_count} material profiles; {len(skipped)} skipped.',flush=True)

if __name__=='__main__':main()
