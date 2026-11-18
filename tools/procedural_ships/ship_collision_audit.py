"""Read-only SUR structure/bounds survey and cross-reference with the model inventory."""
import collections
import hashlib
import json
from pathlib import Path
import struct as S
import sys

import numpy as np
import full_ship_audit as audit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tradelane'))
from docking_surface import parts as sur_parts


def surface(blob):
    assert len(blob)>=48,'Truncated surface header'
    root=S.unpack_from('<i',blob,32)[0]
    seen=set();hulls=[]
    def visit(at):
        assert at not in seen and at>=48 and at+28<=len(blob),('Invalid tree node',at,len(blob))
        seen.add(at);right,ledge=S.unpack_from('<ii',blob,at)
        if right:
            visit(at+28);visit(at+right)
        else:
            h=at+ledge;assert h>=48 and h+16<=len(blob)
            poff,client,flags,count,unused=S.unpack_from('<iIIHH',blob,h)
            assert h+16+count*16<=len(blob)
            ids=[]
            for f in range(count):
                for k in range(3):ids.append(S.unpack_from('<H',blob,h+20+f*16+k*4)[0])
            vertices=[]
            for i in set(ids):
                off=h+poff+i*16;assert off>=0 and off+16<=len(blob)
                vertices.append(S.unpack_from('<3f',blob,off))
            pts=np.array(vertices)
            hulls.append(dict(triangles=count,vertices=len(vertices),client=client,flags=flags,
                       bounds=[pts.min(0).tolist(),pts.max(0).tolist()] if len(vertices) else None))
    visit(root)
    return dict(tree_nodes=len(seen),hulls=hulls)


def main():
    manifest=json.loads((audit.OUT/'inventory.json').read_text(encoding='utf8'))
    models={Path(r['path']).with_suffix('.sur').as_posix():r for r in manifest['models']}
    paths=set((audit.DATA/'SHIPS').rglob('*.sur'))
    paths.update(audit.DATA/p for p in models if (audit.DATA/p).exists())
    records=[]
    for p in sorted(paths):
        data=p.read_bytes();rel=p.relative_to(audit.DATA).as_posix().lower()
        r=dict(path=rel,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),parts=[])
        try:
            for part_id,chunks in sur_parts(data):
                row=dict(id=part_id,tags=[tag.decode('ascii') for tag,_ in chunks])
                for tag,blob in chunks:
                    if tag==b'surf':row['surface']=surface(blob)
                    if tag==b'exts':row['extents']=list(S.unpack('<6f',blob))
                    if tag==b'hpid':row['hardpoints']=list(S.unpack('<'+'I'*(len(blob)//4),blob))
                r['parts'].append(row)
            model=models.get(rel)
            if model:
                names={'Root',*(j['name'] for j in model.get('constructs',[]))}
                byid={audit.m.crc(n):n for n in names};byid[0]='standalone root'
                for part in r['parts']:part['model_part']=byid.get(part['id'])
                r['model']=model['path']
        except Exception as e:r['error']=type(e).__name__+': '+str(e)
        records.append(r)
    summary=dict(files=len(records),errors=[dict(path=r['path'],error=r['error']) for r in records if 'error' in r],
       parts=sum(len(r['parts']) for r in records),hulls=sum(len(p.get('surface',{}).get('hulls',[])) for r in records for p in r['parts']))
    (audit.OUT/'collision.json').write_text(json.dumps(dict(summary=summary,files=records),indent=2),encoding='utf8')
    text=['# Коллизионные модели кораблей\n',
          f"Прочитано SUR: {len(records)}. Ошибки/неподдержанные структуры: {len(summary['errors'])}. Частей: {summary['parts']}; листовых оболочек: {summary['hulls']}.\n",
          'Прочитаны контейнеры, дерево surface, индексы граней, точки листовых оболочек и локальные границы. Это **структурный разбор**, не проверка выпуклости, соседства рёбер, качества физики или совпадения SUR с визуальной поверхностью во всех позах. Неизвестный CRC не означает автоматически ошибку: SUR может содержать служебные/хардпоинтные части.\n',
          '| SUR | Частей | Оболочек | Сопоставление |','|---|---:|---:|---|']
    for r in records:
        hulls=sum(len(p.get('surface',{}).get('hulls',[])) for p in r['parts'])
        match=', '.join(p['model_part'] or f"{p['id']:08x}" for p in r['parts'] if 'model_part' in p)
        text.append(f"| `{r['path']}` | {len(r['parts'])} | {hulls} | {r.get('error') or match or 'без одноимённого CMP/3DB'} |")
    text+=['\n[Все CRC, оболочки, границы и SHA-256](collision.json)\n']
    (audit.OUT/'COLLISION.md').write_text('\n'.join(text),encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
