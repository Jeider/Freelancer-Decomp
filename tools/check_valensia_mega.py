"""Compare every baked triangle/LOD/collision leaf with the preserved originals."""
import ast
from collections import Counter,defaultdict
import json
import re
import struct as S
import subprocess
import numpy as np
import valensia_mega as m


def templates(raw):
    result={}
    for cls in ast.parse(raw).body:
        if not isinstance(cls,ast.ClassDef):continue
        for member in cls.body:
            if isinstance(member,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TEMPLATE' for t in member.targets):
                result[cls.name]=ast.literal_eval(member.value)
    return result


def triangles(blob,ref):
    _,_,group_count,index_count,fvf,vertex_count=S.unpack_from('<II4H',blob)
    assert fvf==0x112
    base,nv,si,ni,sg,ng=S.unpack_from('<6H',ref,8)
    assert base+nv<=vertex_count and si+ni<=index_count and sg+ng<=group_count
    vertex_at=16+12*group_count+2*index_count
    cursor=16+12*group_count
    result=[]
    for group in range(group_count):
        material,low,high,n,_=S.unpack_from('<I4H',blob,16+12*group)
        ids=S.unpack_from('<'+'H'*n,blob,cursor)
        cursor+=2*n
        if not sg<=group<sg+ng:continue
        assert n%3==0
        absolute=[base+low+i for i in ids]
        assert all(base<=i<base+nv for i in absolute)
        verts=[blob[vertex_at+32*i:vertex_at+32*(i+1)] for i in absolute]
        result.extend((material,tuple(verts[i:i+3])) for i in range(0,n,3))
    assert len(result)*3==ni
    return result


def hull_key(h):return np.asarray(h.points,dtype='<f4').tobytes(),h.raw[16:]


def main():
    manifest=json.loads((m.OUT/'manifest.json').read_text())
    for name,digest in manifest['payload'].items():
        assert m.old.sha256((m.OUT/'stage'/name).read_bytes()).hexdigest()==digest,name
    source=templates((m.GAME/m.old.ORIGINAL_TEMPLATE).read_text(encoding='utf-8-sig'))
    target=templates((m.OUT/'stage'/m.old.TEMPLATE).read_text(encoding='utf-8-sig'))
    for name,text in source.items(): assert target[name+'Original']==text
    source['or_hq_live']=(m.GAME/'DATA'/m.old.LIVE.replace('.ini','Original.ini')).read_text(encoding='utf-8-sig')
    target['or_hq_live']=(m.OUT/'stage/DATA'/m.old.LIVE).read_text(encoding='utf-8-sig')
    current=(m.GAME/'DATA'/m.old.LIVE).read_text(encoding='utf-8-sig')
    def outside_station(text):
        return Counter(block for block in m.old.blocks(text) if not m.old.one(m.old.fields(block),'nickname').startswith('or_hq_station_1'))
    assert outside_station(current)==outside_station(target['or_hq_live'])
    lods=defaultdict(dict)
    nick=''
    for block in m.old.blocks((m.OUT/'stage/DATA/SOLAR/solararch.ini').read_text(encoding='utf-8-sig')):
        d=m.old.fields(block)
        if block.lower().startswith('[solar]'):nick=m.old.one(d,'nickname')
        if block.lower().startswith('[lod]') and nick.startswith('vlm_'):
            lods[nick][m.old.one(d,'obj')]=tuple(m.mesh.floats(m.old.one(d,'lodranges')))
    builder=m.Builder();removed=set();total_hulls=0;total_triangles=0
    nested_names={}
    for label,report in manifest['reports'].items():
        rows={p.name:p for p in m.b.placements_from_template(source[label])}
        new={p.name:p for p in m.b.placements_from_template(target[label])}
        consumed=set()
        for component in report['components']:
            name=component['name'];origin=np.array(component['origin'])
            vv,hh=[],[]
            for nick in component['members']:
                assert nick not in consumed;consumed.add(nick)
                visual,hulls,_=builder.expand(rows[nick],origin);vv.extend(visual);hh.extend(hulls)
            first=component['members'][0]
            assert new[first].archetype==name and np.allclose(new[first].pos,origin) and new[first].rotate==(0,0,0)
            removed.update(component['members'][1:])
            expected=defaultdict(Counter)
            for visual in vv:
                for level,(groups,verts) in enumerate(visual.levels):
                    transformed=[m.mesh.xform_vert(v,visual.rotation,visual.translation) for v in verts]
                    for mat,ids in groups:
                        expected[(visual.ranges,level)].update((mat,tuple(transformed[i] for i in ids[j:j+3])) for j in range(0,len(ids),3))
            root=m.b.load_model(m.OUT/f'stage/DATA/SOLAR/OPTIMIZED/valensia_mega/{name}.cmp')[1]
            library={k:m.b.one(n,'VMeshData').blob for k,n in m.b.library_meshes(root).items()}
            actual=defaultdict(Counter)
            for entry in m.b.one(root,'Cmpnd').children:
                n=m.b.one(entry,'Object name');file=m.b.one(entry,'File name')
                if not n:continue
                file_name=m.b.text(file.blob)
                file_crc=m.utf.crc(file_name)
                assert file_crc not in nested_names,(name,file_name,'EngBase global cache aliases',nested_names.get(file_crc))
                nested_names[file_crc]=(name,file_name)
                partname=m.b.text(n.blob);node=m.b.one(root,m.b.text(file.blob));ranges=lods[name][partname]
                for level in m.b.one(node,'MultiLevel').children:
                    if not level.name.startswith('Level'):continue
                    ref=m.b.one(level,'VMeshRef')
                    if not ref:continue
                    raw=library[S.unpack_from('<I',ref.blob,4)[0]]
                    actual[(ranges,int(level.name[5:]))].update(triangles(raw,ref.blob))
            assert dict(actual)==dict(expected),name+' render triangles/LODs differ'
            parts=m.old.parts((m.OUT/f'stage/DATA/SOLAR/OPTIMIZED/valensia_mega/{name}.sur').read_bytes())
            assert len(parts)==1 and parts[0][0]==m.utf.crc('Root')
            actual_hulls=m.old.leaves(dict(parts[0][1])[b'surf'])
            assert Counter(map(hull_key,actual_hulls))==Counter(map(hull_key,hh)),name+' collision differs'
            total_hulls+=len(hh);total_triangles+=sum(sum(c.values()) for c in actual.values())
            print('PASS',name,'all LOD triangles and',len(hh),'collision leaves',flush=True)
        original_blocks=Counter(block for block in m.old.blocks(source[label]) if m.old.one(m.old.fields(block),'nickname') not in consumed)
        new_blocks=Counter(block for block in m.old.blocks(target[label]) if m.old.one(m.old.fields(block),'nickname') not in consumed)
        assert original_blocks==new_blocks,label+' unaffected objects changed'
    pattern=m.OUT/'removed_nicknames.txt';pattern.write_text('\n'.join(sorted(removed)),encoding='utf-8')
    scan=subprocess.run(['rg','-n','-i','-F','-f',str(pattern),str(m.GAME/'DATA'),str(m.GAME/'Assets/Pythonlancer'),'-g','*.ini','-g','*.py'],capture_output=True)
    assert scan.returncode in (0,1)
    bad=[line for line in scan.stdout.decode(errors='replace').splitlines() if not re.search(r':\d+:\s*nickname\s*=',line,re.I)]
    assert not bad,'\n'.join(bad[:20])
    result=dict(manifest_sha256=m.old.sha256((m.OUT/'manifest.json').read_bytes()).hexdigest(),hulls=total_hulls,lod_triangles=total_triangles,originals=True,external_references=True)
    (m.OUT/'checks.json').write_text(json.dumps(result,indent=2))
    print(result)


if __name__=='__main__':main()
