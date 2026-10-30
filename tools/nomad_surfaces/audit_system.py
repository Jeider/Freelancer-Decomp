"""Read-only solar/material inventory for a system; writes a local JSON report."""
import collections
import functools
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import generate_station_lods as utf
DATA=Path('D:/games/FL_MOD/DATA')

def ini(path):
    sections=[];current=None
    for raw in path.read_text(encoding='cp1251').splitlines():
        line=raw.split(';',1)[0].strip()
        if line.startswith('[') and line.endswith(']'):
            current=(line[1:-1].lower(),collections.defaultdict(list));sections.append(current)
        elif current is not None and '=' in line:
            key,value=line.split('=',1);current[1][key.strip().lower()].append(value.strip())
    return sections

def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.children)

@functools.lru_cache(None)
def crc(name):return utf.crc(name)

@functools.lru_cache(None)
def asset(relative):
    path=DATA/relative.replace('\\','/')
    _,roots=utf.read_tree(path.read_bytes())
    materials={};meshes=[]
    for node in walk(roots):
        if node.name.lower()=='material library':
            for material in node.children:
                fields={}
                for leaf in material.children:
                    if leaf.blob is None:continue
                    if leaf.name.lower()=='type' or leaf.name.lower().endswith('_name'):
                        fields[leaf.name]=leaf.blob.rstrip(b'\0').decode('ascii',errors='replace')
                    elif len(leaf.blob)<=16:fields[leaf.name]=leaf.blob.hex()
                materials[crc(material.name)]=dict(name=material.name,library=relative,fields=fields)
        if node.name=='VMeshData' and node.blob:
            groups,refs,fvf,vertices=struct.unpack_from('<4H',node.blob,8)
            for i in range(groups):
                identity,start,end,count=struct.unpack_from('<I3H',node.blob,16+12*i)
                meshes.append(dict(material=identity,fvf=hex(fvf),normals=bool(fvf&16),triangles=count//3))
    return materials,meshes

def dyson(name,texture):
    if name.lower()=='beast_dyson_recess':return False
    base=texture.replace('\\','/').split('/')[-1].lower()
    return name.lower().startswith(('dyson_','detailmap_dyson_','asteroid_dyson')) or base.startswith('dyson_') or base in ('vdyson1','vdyson2','vdyson3')

def main():
    system=sys.argv[1] if len(sys.argv)>1 else 'UNIVERSE/SPECIAL/ANOMALY/anm.ini'
    objects=[s for kind,s in ini(DATA/system) if kind=='object']
    uses=collections.Counter(s['archetype'][0].lower() for s in objects)
    solars={s['nickname'][0].lower():s for kind,s in ini(DATA/'SOLAR/solararch.ini') if kind=='solar' and s['nickname']}
    report=[]
    for nickname,count in uses.items():
        solar=solars[nickname];model=solar['da_archetype'][0]
        libraries=solar['material_library'];materials={}
        for lib in libraries:materials.update(asset(lib)[0])
        own,meshes=asset(model);materials.update(own)
        used=[]
        for identity in sorted(set(m['material'] for m in meshes)):
            item=dict(materials.get(identity,dict(name=f'UNRESOLVED {identity:08x}',fields={})))
            item['dyson_profile']=dyson(item['name'],item['fields'].get('Dt_name',''))
            item['mesh_formats']=sorted(set(m['fvf'] for m in meshes if m['material']==identity))
            item['all_meshes_have_normals']=all(m['normals'] for m in meshes if m['material']==identity)
            used.append(item)
        row=dict(archetype=nickname,instances=count,model=model,libraries=libraries,
                 envmap_material=solar['envmap_material'],nomad=solar['nomad'],materials=used)
        report.append(row)
        print(nickname,count,model)
        for m in used:
            print(' ', 'DYSON' if m['dyson_profile'] else 'OTHER',m['name'],m['fields'].get('Type'),
                  {k:v for k,v in m['fields'].items() if k.endswith('_name')},m['mesh_formats'])
    out=ROOT/'src/obj/dyson_bump/anm_audit.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(system=system,objects=len(objects),archetypes=report),indent=2))
    print('REPORT',out)

if __name__=='__main__':main()
