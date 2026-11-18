"""Read-only fighter inventory and offline asset contact sheets for design review."""
import argparse
import collections
import hashlib
import io
import json
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import li_elite as mesh
from preview import render
from rh_redesign_paths import ANALYSIS

GAME = Path('D:/Games/FL_MOD')
DATA = GAME / 'DATA'
OUT = ANALYSIS


def sections(path):
    name, values = '', collections.defaultdict(list)
    for line in path.read_text(encoding='utf-8-sig', errors='replace').splitlines():
        line = line.split(';', 1)[0].strip()
        if line.startswith('[') and line.endswith(']'):
            if name:
                yield name, dict(values)
            name, values = line[1:-1].lower(), collections.defaultdict(list)
        elif '=' in line:
            k, v = line.split('=', 1)
            values[k.strip().lower()].append(v.strip())
    if name:
        yield name, dict(values)


def inventory():
    sources = [p for _, values in sections(GAME/'bin/freelancer.ini') for p in values.get('ships', [])]
    aliases = {}
    for source in sources:
        path = DATA/source
        for section, values in sections(path):
            if section == 'ship':
                aliases[values['nickname'][0].lower()] = dict(values, source=[source])
    models = {}
    excluded = []
    for name, v in aliases.items():
        if v.get('type', [''])[0].upper() != 'FIGHTER':
            continue
        model = v['da_archetype'][0].replace('\\', '/').lower()
        row = models.setdefault(model, dict(model=model, aliases=[], materials=[], classes=[], ids=[]))
        row['aliases'].append(name)
        for value in v.get('material_library', []):
            value = value.replace('\\', '/').lower()
            if value not in row['materials']: row['materials'].append(value)
        row['classes'] += v.get('ship_class', [])
        row['ids'] += v.get('ids_name', [])
    alt = 'ships/rheinland/rh_elite/rh_alt_elite.cmp'
    if alt not in models:
        models[alt] = dict(model=alt, aliases=['rh_alt_elite (reference, not active)'],
                           materials=['ships/rheinland/rh_playerships.mat', 'fx/envmapbasic.mat'], classes=[], ids=[])
    return sorted(models.values(), key=lambda r:r['model']), sources


def material_table(files):
    props, textures = {}, {}
    for path in files:
        if not path.exists(): continue
        _, nodes = mesh.read_tree(path.read_bytes())
        for p, n in mesh.walk(nodes):
            bits = p.split('/')
            if '/material library/' in p.lower():
                props.setdefault(bits[-2], {})[bits[-1].lower()] = n.blob
            if '/texture library/' in p.lower() and bits[-1].lower() in ('mips','mip0'):
                textures[bits[-2].lower()] = n.blob
    result = {}
    for name, p in props.items():
        tex = mesh.string(p.get('dt_name', b'')).lower()
        image = None
        if tex in textures:
            try: image = Image.open(io.BytesIO(textures[tex])).convert('RGB')
            except OSError: pass
        result[mesh.crc(name)] = dict(name=name, texture=tex, image=image,
            colour=np.frombuffer(p.get('dc', struct.pack('<3f', 1,1,1)), '<f4')[:3].astype(float),
            kind=mesh.string(p.get('type', b'')))
    return result


def load(row, pose=None):
    path = DATA/row['model']
    data = path.read_bytes()
    _, nodes = mesh.read_tree(data)
    flat = list(mesh.walk(nodes))
    blobs = {mesh.crc(p.split('/')[-2]): n.blob for p,n in flat if p.lower().endswith('/vmeshdata')}
    libs = {}
    transform, construct_warnings = transforms(nodes, pose)
    mats = material_table([DATA/p for p in row['materials']] + [path])
    scene, parts, lods = [], [], collections.Counter()
    for p,n in flat:
        if not p.lower().endswith('/vmeshref'): continue
        for bit in p.split('/'):
            if bit.lower().startswith('level'): lods[bit.lower()]+=1
        if '/multilevel/' in p.lower() and '/level0/' not in p.lower(): continue
        mid = struct.unpack_from('<I',n.blob,4)[0]
        if mid not in libs: libs[mid] = decode(blobs[mid])
        groups = extract(n.blob, libs)
        part = p.split('/')[2]
        rot, offset = transform.get(part.lower(), (np.eye(3),np.zeros(3)))
        count = sum(len(g['corners']) for g in groups)
        parts.append(dict(name=part, triangles=count,
                          materials=[mats.get(g['material'],{}).get('name',hex(g['material'])) for g in groups]))
        for g in groups:
            if g['material'] not in mats:
                mats[g['material']] = dict(name=hex(g['material']),texture='',image=None,colour=np.ones(3),kind='MISSING')
            g['corners'][...,:3] = g['corners'][...,:3]@rot.T+offset
            g['corners'][...,3:6] = g['corners'][...,3:6]@rot.T
            g['part'] = part
            scene.append(g)
    if not scene: raise ValueError('No Level0 meshes')
    points = np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in scene])
    low, high = points.min(axis=0), points.max(axis=0)
    used = {g['material'] for g in scene}
    stats = dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), triangles=sum(p['triangles'] for p in parts),
                 parts=parts, lod_parts=dict(lods), bounds=[low.tolist(),high.tolist()], dimensions=(high-low).tolist(),
                 material_info=[dict(id=k,**{n:v for n,v in mats[k].items() if n not in ('image','colour')},
                     texture_size=list(mats[k]['image'].size) if mats[k]['image'] else None) for k in sorted(used)],
                 hardpoint_count=sum(p.lower().endswith('/position') and '/hardpoints/' in p.lower() for p,_ in flat),
                 animation_leaves=sum('/animation/' in p.lower() for p,_ in flat),warnings=construct_warnings)
    return scene,mats,stats


def decode(blob):
    flags,primitive,ng,ni,fvf,nv=struct.unpack_from('<II4H',blob)
    if flags!=1 or primitive!=4 or (fvf&0xe)!=2 or not fvf&0x10:
        raise ValueError('Unsupported vertex format '+hex(fvf))
    colours=4*bool(fvf&0x40)+4*bool(fvf&0x80)
    stride=24+colours+sum((8,12,16,4)[(fvf>>(16+2*i))&3] for i in range((fvf>>8)&15))
    at=16+12*ng
    start=at+2*ni
    end=start+nv*stride
    if end>len(blob) or any(blob[end:]):raise ValueError('Non-padding data after vertex array')
    raw=np.frombuffer(blob,'<f4',nv*stride//4,start).reshape(nv,stride//4)
    verts=np.concatenate((raw[:,:6],raw[:,6+colours//4:8+colours//4]),axis=1).astype(float)
    groups=[struct.unpack_from('<I4H',blob,16+12*i) for i in range(ng)]
    return verts,groups,np.frombuffer(blob,'<u2',ni,at).astype(int)


def extract(ref,libs):
    size,mid,start,count,index,nindex,first,ng=struct.unpack_from('<II6H',ref)
    assert size==60
    verts,groups,indices=libs[mid];out=[]
    for mat,low,high,n,unused in groups[first:first+ng]:
        assert n%3==0 and index+n<=len(indices)
        ids=indices[index:index+n].reshape(-1,3)+start+low
        assert ids.min()>=0 and ids.max()<len(verts)
        out.append(dict(material=mat,corners=verts[ids].copy()))
        index+=n
    return out


def transforms(nodes, pose=None):
    data={p.lower():n.blob for p,n in mesh.walk(nodes)}
    names,joints,warnings={},{},[]
    values={}
    if pose is not None:
        script,phase=pose
        for p,b in data.items():
            if '/animation/script/'+script.lower()+'/' in p and p.endswith('/channel/header'):
                count,interval,kind=struct.unpack('<IfI',b)
                if kind!=1 or interval!=-1:raise ValueError('Unsupported animation channel')
                frames=np.frombuffer(data[p.rsplit('/',1)[0]+'/frames'],'<f4').reshape(count,2)
                joint=p.rsplit('/channel/',1)[0]
                values[mesh.string(data[joint+'/child name']).lower()]=float(frames[0 if phase==0 else -1,1])
    for path,blob in data.items():
        if '/cmpnd/' in path and path.endswith('/file name'):
            names[mesh.string(blob).lower()]=mesh.string(data[path.rsplit('/',1)[0]+'/object name']).lower()
        if '/cmpnd/cons/' not in path:continue
        kind=path.rsplit('/',1)[-1];size={'fix':176,'rev':208,'pris':208}.get(kind)
        if size is None:raise ValueError('Unsupported construct '+kind)
        assert len(blob)%size==0
        for at in range(0,len(blob),size):
            parent,name=mesh.string(blob[at:at+64]).lower(),mesh.string(blob[at+64:at+128]).lower()
            f=np.frombuffer(blob,'<f4',(size-128)//4,at+128).astype(float)
            r=f[3:12].reshape(3,3) if kind=='fix' else f[6:15].reshape(3,3)
            value=values.get(name,0)
            if kind=='rev' and value:
                axis=mesh.unit(f[15:18]);x,y,z=axis
                cross=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
                rotation=np.eye(3)*np.cos(value)+(1-np.cos(value))*np.outer(axis,axis)+np.sin(value)*cross
                r=rotation@r
            t=f[:3] if kind=='fix' else f[:3]-r@f[3:6]
            if kind=='pris':t=t+f[15:18]*value
            joints[name]=(parent,r,t)
    resolved={'root':(np.eye(3),np.zeros(3))}
    def resolve(name):
        if name not in resolved:
            if name not in joints:
                if 'none' not in name:raise ValueError('Missing construct for '+name)
                warnings.append('Unbound placeholder '+name+' shown at identity')
                resolved[name]=(np.eye(3),np.zeros(3))
            else:
                parent,r,t=joints[name];pr,pt=resolve(parent);resolved[name]=(pr@r,pr@t+pt)
        return resolved[name]
    return {file:resolve(name) for file,name in names.items()},warnings


def image_for(scene,mats,camera,size=400,mode='texture',bounds=None):
    points = np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in scene])
    low, high = bounds if bounds else (points.min(axis=0),points.max(axis=0))
    center=(low+high)/2
    radius=np.linalg.norm(np.stack([low-center,high-center]),axis=1).max()
    return render(scene,mats,center,radius,camera,size,mode)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');parser.add_argument('--only');parser.add_argument('--fighters',action='store_true');parser.add_argument('--extras',action='store_true')
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    rows,sources=inventory()
    if args.extras:
        known={r['model'] for r in rows}
        by_family={}
        for row in rows:
            if row['model'].startswith('ships/') and row['materials'] and set(row['classes'])&{'0','1'}:
                by_family.setdefault(row['model'].split('/')[1],row['materials'])
        extra=[];seen=set()
        for path in (DATA/'SHIPS').rglob('*.cmp'):
            rel=path.relative_to(DATA).as_posix().lower()
            if rel in known or not any(x in path.stem.lower() for x in ('fighter','elite','star','dragon')):continue
            if any(x in rel for x in ('_bkp','_orig','копия','_init','_pir_','_nmd_','_dmg')):continue
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            if sha in seen:continue
            seen.add(sha)
            extra.append(dict(model=rel,aliases=['inactive asset'],materials=by_family.get(rel.split('/')[1],[]),classes=[],ids=[]))
        rows=sorted(extra,key=lambda r:r['model'])
    excluded=[]
    if args.fighters:
        selected=[]
        for row in rows:
            if set(row['classes'])&{'0','1','4','5','6','7'} or any(x in row['model'] for x in ('rh_alt_elite','ku_blood_dragon','nomad/no_')):
                selected.append(row)
            else:excluded.append(row['model'])
        rows=selected
    if args.only:rows=[r for r in rows if args.only in r['model']]
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',16)
    for row in rows:
        try:
            scene,mats,stats=load(row);row.update(stats)
            if args.render:
                panel=Image.new('RGB',(800,440),(24,29,37));draw=ImageDraw.Draw(panel)
                draw.text((12,6),Path(row['model']).stem+' | '+str(stats['triangles'])+' tris',font=font,fill='white')
                for col,camera in enumerate(((1,.85,-1.4),(-1,.55,1.4))):
                    panel.paste(image_for(scene,mats,camera),(col*400,35))
                target=OUT/(Path(row['model']).stem+('_extra_'+stats['sha256'][:6] if args.extras else '')+'.jpg');panel.save(target,quality=91)
                row['preview']=target.name
            print(Path(row['model']).stem,stats['triangles'],len(stats['parts']),flush=True)
        except Exception as error:
            row['error']=str(error);print('ERROR',row['model'],str(error),flush=True)
    (OUT/('inventory_extra.json' if args.extras else 'inventory_'+args.only+'.json' if args.only else 'inventory.json')).write_text(json.dumps(dict(sources=sources,models=rows,excluded=excluded),indent=2),encoding='utf-8')
    if args.render:
        primary=[r for r in rows if 'preview' in r and not any(x in r['model'] for x in ('_pir_','_nmd_'))]
        for start in range(0,len(primary),8):
            subset=primary[start:start+8];sheet=Image.new('RGB',(1600,440*((len(subset)+1)//2)),(24,29,37))
            for i,row in enumerate(subset):
                if 'preview' in row:sheet.paste(Image.open(OUT/row['preview']),((i%2)*800,(i//2)*440))
            sheet.save(OUT/f'contact_{"extra_" if args.extras else ""}{start//8+1:02}.jpg',quality=92)


if __name__=='__main__':main()
