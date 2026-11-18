"""Audit current Rheinland rooms, material images, usage and existing geometry."""
import collections,io,re,subprocess
from native_common import *

BATCH=ROOT/'out/base_interiors/rheinland_batch'
MODELS=['rh_battleship_bar','rh_berlin_bar','rh_bremen_station_bar','rh_stuttgart_bar',
        'rh_bizmark_equip','rh_berlin_equip','rh_stuttgart_equip',
        'rh_depot_deck','rh_battleship_deck']

def ini(path):
    sections=[];current=None
    for line in path.read_text(encoding='latin1').splitlines():
        line=line.split(';')[0].strip()
        if line.startswith('['):current=[line.strip('[]').lower(),collections.defaultdict(list)];sections.append(current)
        elif '=' in line and current:
            k,v=line.split('=',1);current[1][k.strip().lower()].append(v.strip())
    return sections
def path_data(rel):return GAME/'DATA'/rel.replace('\\','/')
def scene(rel):
    cache=BATCH/'scenes'/(Path(rel.replace('\\','/')).stem.lower()+'.json')
    if not cache.exists():
        p=subprocess.run([str(ROOT/'out/base_interiors/tool_cache/scene_read.exe'),str(path_data(rel))],capture_output=True)
        if p.returncode:dump(cache,dict(entities={},parse_error=p.stderr.decode('latin1'),script=rel))
        else:dump(cache,json.loads(p.stdout))
    return json.loads(cache.read_text())
def transforms(root):
    pending=[];result={'Root':(np.eye(3),np.zeros(3))};kinds={}
    for kind in child(child(root,'Cmpnd'),'Cons').children:
        size={'Fix':176,'Rev':208,'Pris':208,'Sphere':212}.get(kind.name)
        assert size,kind.name
        for off in range(0,len(kind.blob),size):
            raw=kind.blob[off:off+size];parent=text(raw[:64]);name=text(raw[64:128])
            pos=np.array(S.unpack_from('<3f',raw,128));rot=np.array(S.unpack_from('<9f',raw,140 if kind.name=='Fix' else 152)).reshape(3,3).T
            pending.append((parent,name,rot,pos));kinds[name]=kind.name
    while pending:
        progress=False
        for parent,name,rot,pos in pending[:]:
            if parent not in result:continue
            r,p=result[parent];result[name]=(rot@r,pos@r+p)
            pending.remove(next(x for x in pending if x[1]==name));progress=True
        assert progress
    return result,kinds

def audit(selected_models=None):
    from PIL import Image,ImageDraw
    BATCH.mkdir(exist_ok=True)
    petal={}
    for line in (GAME/'DATA/petaldb.ini').read_text().splitlines():
        if '=' not in line or ',' not in line:continue
        k,v=line.split('=',1)
        if k.strip() not in ('room','prop'):continue
        name,rel=v.strip().split(',',1);petal[name.strip().lower()]=rel.strip().replace('\\','/')
    usage=[]
    for kind,base in ini(GAME/'DATA/UNIVERSE/universe.ini'):
        if kind!='base' or not base['nickname'] or not base['nickname'][0].lower().startswith('rh_'):continue
        for k,room in ini(path_data(base['file'][0])):
            if k!='room' or room['nickname'][0].lower() not in ('bar','equipment','deck','shipdealer'):continue
            rel=room['file'][0];sections=ini(path_data(rel));info=next(v for k,v in sections if k=='room_info')
            scripts=info['set_script']+[v.split(',')[-1].strip() for v in info['scene']]
            models=set()
            for script in scripts:
                for e in (scene(script).get('entities') or {}).values():
                    template=e.get('template_name','').lower()
                    if template in petal:models.add(petal[template])
                if scene(script).get('parse_error'):
                    raw=path_data(script).read_bytes().lower()
                    # Inventory only: exact NUL-terminated template literals in
                    # compiled scripts. Never use these as a scene transform.
                    for template,model in petal.items():
                        if template.encode()+b'\0' in raw:models.add(model)
            usage.append(dict(base=base['nickname'][0],room=room['nickname'][0],ini=rel,scripts=scripts,models=sorted(models)))
    dump(BATCH/'room_usage.json',usage)
    for name in (selected_models or MODELS):
        dest=BATCH/name;dest.mkdir(exist_ok=True);texdir=dest/'textures';texdir.mkdir(exist_ok=True)
        source=GAME/'DATA/BASES/RHEINLAND'/(name+'.cmp');raw=source.read_bytes();root=read_tree(raw)[1][0]
        textures={}
        for t in child(root,'Texture library').children:
            payload=next((x.blob for x in t.children if x.name in ('MIPS','MIP0')),None)
            if payload:
                file=texdir/(sha(t.name.encode())[:12]+'.png');im=Image.open(io.BytesIO(payload));im.save(file)
                textures[t.name.lower()]=dict(path=str(file),size=im.size,sha256=sha(payload))
        mats={}
        for m in child(root,'Material library').children:
            props={}
            for n in m.children:
                if n.name.endswith('_name') or n.name=='Type':props[n.name]=text(n.blob)
                elif len(n.blob) in (4,12,16):props[n.name]=list(S.unpack('<'+'f'*(len(n.blob)//4),n.blob))
            props['name']=m.name;props['textures']={k:textures.get(v.lower()) for k,v in props.items() if k.endswith('_name')}
            mats[str(crc(m.name))]=props
        trans,kinds=transforms(root);batches=[];areas=collections.defaultdict(float)
        for part in get_parts(root):
            rot,pos=trans[part['name']]
            for group in part['groups']:
                v=group['corners'].copy();v[:,:,:3]=v[:,:,:3]@rot+pos;v[:,:,3:6]=v[:,:,3:6]@rot
                area=np.linalg.norm(np.cross(v[:,1,:3]-v[:,0,:3],v[:,2,:3]-v[:,0,:3]),axis=1)*.5
                n=v[:,:,3:6];flat=(np.min(np.einsum('tij,tkj->tik',n,n),axis=(1,2))>.999)
                areas[str(group['material'])]+=float(area[flat].sum())
                batches.append(dict(part=part['name'],joint=kinds.get(part['name'],'Root'),material=str(group['material']),vertices=v.reshape(-1,v.shape[-1]).tolist(),stride=v.shape[-1],triangles=len(v)))
        uses=[u for u in usage if any(Path(m).stem.lower()==name for m in u['models'])]
        model=dict(source=str(source),sha256=sha(raw),materials=mats,textures=textures,batches=batches,uses=uses)
        dump(dest/'source_scene.json',model)
        used=sorted(set(b['material'] for b in batches),key=lambda k:areas[k],reverse=True)
        w=1000;cell=250;h=((len(used)+3)//4)*280
        sheet=Image.new('RGB',(w,h),(27,31,37));draw=ImageDraw.Draw(sheet)
        for i,key in enumerate(used):
            m=mats[key];x=i%4*cell;y=i//4*280;t=m['textures'].get('Dt_name')
            if t:
                im=Image.open(t['path']).convert('RGB');im.thumbnail((244,240));sheet.paste(im,(x+(250-im.width)//2,y))
            draw.text((x+4,y+242),m['name'][:32],fill='white');draw.text((x+4,y+257),f'{key} flat area {areas[key]:.1f}',fill='lightblue')
        sheet.save(dest/'material_sheet.jpg')
        print(name,'triangles',sum(b['triangles'] for b in batches),'materials',len(used),'active uses',len(uses),flush=True)
    print('Other active RH room models:',sorted({m for u in usage for m in u['models'] if Path(m).stem.lower() not in MODELS+['rh_bizmark_bar']}))

if __name__=='__main__':audit(sys.argv[1:] or None)
