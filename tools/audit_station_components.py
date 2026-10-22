"""Read-only inventory, placement counts and mesh diagnostics for station parts."""
import collections
import hashlib
import json
import math
import re
import struct as S
from pathlib import Path
from repair_panel_normals import leaves,triangles,face_normal
from generate_station_lods import crc

DATA=Path('D:/games/FL_MOD/DATA')
OUT=Path('bin/station_component_audit')
skipped=[]


def sections(path):
    if not path.exists():skipped.append(str(path));return []
    raw=path.read_bytes()
    if raw.startswith(b'BINI'):skipped.append('BINI: '+str(path));return []
    result=[];current=None
    for line in raw.decode('cp1251',errors='replace').splitlines():
        line=line.split(';',1)[0].strip()
        if not line:continue
        if line.startswith('[') and line.endswith(']'):
            current={'section':line[1:-1].lower(),'values':collections.defaultdict(list)};result.append(current)
        elif current is not None and '=' in line:
            key,value=line.split('=',1);current['values'][key.strip().lower()].append(value.strip())
    return result


def val(section,key,default=''):return section['values'].get(key,[default])[-1]
def rel(value):return value.strip().replace('\\','/').lower()


def configuration():
    config=sections(Path('D:/games/FL_MOD/bin/Freelancer.ini'))
    files=collections.defaultdict(list)
    for s in config:
        if s['section']=='data':
            for k,vs in s['values'].items():files[k].extend(vs)
    solars={};equipment={};loadouts={};references=collections.defaultdict(list)
    for kind,destination in (('solar',solars),('equipment',equipment),('loadouts',loadouts)):
        for name in files[kind]:
            for s in sections(DATA/rel(name)):
                nick=val(s,'nickname').lower()
                if not nick:continue
                destination[nick]=s
                model=rel(val(s,'da_archetype'))
                if model.startswith('solar/') and model.endswith(('.3db','.cmp')):
                    references[model].append(dict(nickname=nick,config=rel(name),lodranges=val(s,'lodranges')))
    worlds={}
    for name in files['universe']:
        universe=DATA/rel(name)
        for s in sections(universe):
            if s['section']=='system' and val(s,'file'):
                path=universe.parent/rel(val(s,'file'))
                worlds[val(s,'nickname').lower()]=[x for x in sections(path) if x['section']=='object']
    uses=collections.defaultdict(collections.Counter);roots=collections.Counter();attached=collections.Counter()
    def add_equipment(nick,system,depth=0):
        if depth>8:return
        s=equipment.get(nick.lower())
        if not s:return
        model=rel(val(s,'da_archetype'))
        if model in references:uses[model][system]+=1;attached[model]+=1
        sub=loadouts.get(val(s,'loadout').lower())
        if sub:
            for e in sub['values'].get('equip',[]):add_equipment(e.split(',')[0].strip(),system,depth+1)
    for system,objects in worlds.items():
        for obj in objects:
            arch=solars.get(val(obj,'archetype').lower())
            if not arch:continue
            model=rel(val(arch,'da_archetype'))
            if model in references:uses[model][system]+=1;roots[model]+=1
            loadout=loadouts.get(val(obj,'loadout',val(arch,'loadout')).lower())
            if loadout:
                for e in loadout['values'].get('equip',[]):add_equipment(e.split(',')[0].strip(),system)
    return references,uses,roots,attached,len(worlds)


def diagnostics(blob):
    flags,primitive,groups,index_count,fvf,vertex_count=S.unpack_from('<II4H',blob)
    expected=16+12*groups+2*index_count+32*vertex_count
    padding=0
    if expected<len(blob)<=expected+3 and not any(blob[expected:]):
        padding=len(blob)-expected;blob=blob[:expected]
    h,ds,groups=triangles(blob)
    vertices=[v for cs in groups for v in cs]
    pos=[S.unpack_from('<3f',v) for v in vertices]
    lo=[min(p[k] for p in pos) for k in range(3)];hi=[max(p[k] for p in pos) for k in range(3)]
    degenerate=opposed=bad_length=invalid=0;duplicates=0;seen=set()
    for (material,_,_),cs in zip(ds,groups):
        for i in range(0,len(cs),3):
            face=cs[i:i+3];normal=face_normal(face)
            if normal is None:degenerate+=1
            key=(material,min(tuple(face),tuple(face[1:]+face[:1]),tuple(face[2:]+face[:2])))
            if key in seen:duplicates+=1
            seen.add(key)
            dots=[]
            for v in face:
                values=S.unpack('<8f',v)
                if not all(math.isfinite(x) for x in values):invalid+=1
                n=values[3:6];length=math.sqrt(sum(x*x for x in n))
                if length<.5 or length>1.5:bad_length+=1
                if length>1.e-8 and normal:dots.append(sum(x*y for x,y in zip(normal,n))/length)
            if len(dots)==3 and max(dots)<-.25:opposed+=1
    used=set();offset=16+12*h[2]
    for g in range(h[2]):
        _,vertex_lo,vertex_hi,count,_=S.unpack_from('<I4H',blob,16+12*g)
        used.update(i+vertex_lo if h[0]&1 else i for i in S.unpack_from('<'+'H'*count,blob,offset))
        offset+=2*count
    return dict(vertices=h[-1],triangles=h[3]//3,groups=h[2],materials=len({d[0] for d in ds}),
                unique_attributes=len(set(vertices)),unused_vertices=h[-1]-len(used),
                identical_vertex_records=len(used)-len(set(vertices)),padding_bytes=padding,
                bounds=[lo,hi],degenerate_triangles=degenerate,duplicate_triangles=duplicates,
                opposed_normal_triangles=opposed,bad_normal_corners=bad_length,nonfinite_corners=invalid)


def inspect_model(path):
    ns=leaves(path.read_bytes())[1]
    meshes={crc(p.split('/')[-2]):(p,b) for p,_,b in ns if p.lower().endswith('/vmeshdata')}
    refs=[(p,b) for p,_,b in ns if p.lower().endswith('/vmeshref')]
    near=[(p,b) for p,b in refs if '/level0/' in p.lower() or '/multilevel/' not in p.lower()]
    totals=collections.Counter();names=[];details=[];errors=[];unique=set()
    for p,ref in near:
        if len(ref)!=60:errors.append('Unexpected reference size: '+p);continue
        key=S.unpack_from('<I',ref,4)[0]
        if key not in meshes:errors.append('Missing CRC '+hex(key));continue
        mp,blob=meshes[key];h=S.unpack_from('<II4H',blob)
        vs,vc,ix,ic,fg,gc=S.unpack_from('<6H',ref,8)
        if vs+vc>h[-1] or ix+ic>h[3] or fg+gc>h[2]:errors.append('Reference bounds: '+p)
        totals.update(vertices=vc,triangles=ic//3,groups=gc)
        names.append(mp.split('/')[-2])
        if key in unique:continue
        unique.add(key)
        if h[4]==0x112:
            try:details.append(dict(mesh=mp,**diagnostics(blob)))
            except Exception as e:errors.append(str(e)+': '+mp)
    lods=collections.defaultdict(set)
    for p,b in refs:
        m=re.search(r'(?i)(.*)/multilevel/level(\d+)/',p)
        if m:lods[m[1]].add(int(m[2]))
    levels=min((len(v) for v in lods.values()),default=1)
    if any('/multilevel/' not in p.lower() for p,b in refs):levels=1
    custom=bool(names) and any(not n.lower().startswith('data.solar.') for n in names)
    # Mesh-name convention is evidence of authorship, not proof of original provenance.
    return dict(custom_name=custom,internal_names=names,lod_count=levels,parts=len(near),
                **totals,diagnostics=details,errors=errors)


def main():
    references,uses,roots,attached,worlds=configuration();results=[]
    for name,refs in references.items():
        path=DATA/name
        if not path.exists():skipped.append(str(path));continue
        try:
            r=inspect_model(path)
            r.update(file=name,references=refs,placements=sum(uses[name].values()),
                     root_placements=roots[name],attachments=attached[name],
                     systems=dict(uses[name]),near_vertex_load=r.get('vertices',0)*sum(uses[name].values()))
            results.append(r)
        except Exception as e:skipped.append(name+': '+str(e))
    OUT.mkdir(parents=True,exist_ok=True)
    report=dict(models=results,active_systems=worlds,skipped=skipped,
                counts_note='Static placements + default/object loadouts in active universe systems; excludes mission spawns, encounters and visibility. Not a GPU profile.')
    (OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    custom=[r for r in results if r['custom_name'] and r['lod_count']==1]
    for r in sorted(custom,key=lambda r:r['near_vertex_load'],reverse=True)[:45]:
        bugs={k:sum(d.get(k,0) for d in r['diagnostics']) for k in ('degenerate_triangles','duplicate_triangles','opposed_normal_triangles','bad_normal_corners')}
        print(Path(r['file']).name,r.get('vertices',0),'v',r.get('triangles',0),'tri',r.get('groups',0),'groups',r['placements'],'uses', 'or_hq',r['systems'].get('or_hq',0),'ku_tgk',r['systems'].get('ku_tgk',0),bugs,flush=True)
    print('SYSTEMS',worlds,'MODELS',len(results),'CUSTOM SINGLE LOD',len(custom),'SKIPPED',len(skipped))
    print('TOWERS')
    for r in results:
        if 'control_tower' in r['file']:print(r['file'],r.get('vertices'),r['lod_count'],r['custom_name'],r['internal_names'])


if __name__=='__main__':main()
