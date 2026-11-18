"""Read every ship CMP/3DB, all LODs/constructs/channels/material references; write Markdown evidence."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import struct as S

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import style_audit as a
import li_elite as m
from rh_redesign_paths import ANALYSIS

OUT=ANALYSIS/'full_models'
DATA=a.DATA


def slug(path):
    return re.sub('[^a-z0-9_]+','_',Path(path).stem.lower())+'_'+hashlib.sha256(path.lower().encode()).hexdigest()[:8]


def configuration():
    active=list(a.sections(a.GAME/'bin/freelancer.ini'))
    shipfiles=[s for _,v in active for s in v.get('ships',[])]
    equipfiles=[s for _,v in active for s in v.get('equipment',[])]
    loadfiles=[s for _,v in active for s in v.get('loadouts',[])]
    archetypes={};aliases=collections.defaultdict(list);errors=[]
    for source in shipfiles:
        path=DATA/source
        if not path.exists():errors.append(str(path));continue
        last=None
        for kind,v in a.sections(path):
            if kind in ('ship','simple') and 'nickname' in v:
                name=v['nickname'][0]
                row=dict(nickname=name,section=kind,source=source,values=v,collision_groups=[])
                archetypes[name.lower()]=row
                last=row if kind=='ship' else None
            elif kind=='collisiongroup' and last is not None:last['collision_groups'].append(v)
    for row in archetypes.values():
        model=row['values'].get('da_archetype',[''])[0].replace('\\','/').lower()
        if model:aliases[model].append(row)
    internal={};loadouts=collections.defaultdict(list)
    for source in equipfiles:
        path=DATA/source
        if not path.exists():errors.append(str(path));continue
        for kind,v in a.sections(path):
            if kind=='internalfx' and 'nickname' in v and any(k.startswith('use_animation') for k in v):
                internal[v['nickname'][0].lower()]=dict(source=source,values=v)
    for source in loadfiles:
        path=DATA/source
        if not path.exists():errors.append(str(path));continue
        for kind,v in a.sections(path):
            if kind=='loadout' and 'archetype' in v:
                used=[x.split(',')[0].strip().lower() for x in v.get('equip',[]) if x.split(',')[0].strip().lower() in internal]
                if used:loadouts[v['archetype'][0].lower()].append(dict(source=source,nickname=v.get('nickname',[''])[0],animations=used))
    return dict(ship_files=shipfiles,equipment_files=equipfiles,loadout_files=loadfiles,aliases=dict(aliases),
                animation_equipment=internal,animation_loadouts=dict(loadouts),missing_ini=errors)


def material_index(config):
    mats=collections.defaultdict(list)
    config['material_read_errors']=[]
    files=set(DATA.rglob('*.mat'))
    files.update(p for p in (DATA/'SHIPS').rglob('*') if p.suffix.lower() in ('.cmp','.3db') and p.stat().st_size)
    files.update(DATA/rel for rel in config['aliases'] if (DATA/rel).is_file() and (DATA/rel).stat().st_size)
    for path in sorted(files):
        try:_,nodes=m.read_tree(path.read_bytes())
        except Exception as e:
            config['material_read_errors'].append(dict(path=path.relative_to(DATA).as_posix(),error=str(e)))
            continue
        props=collections.defaultdict(dict)
        for p,n in m.walk(nodes):
            if '/material library/' in p.lower():props[p.split('/')[-2]][p.split('/')[-1].lower()]=n.blob
        for name,p in props.items():
            if 'type' not in p:continue
            mats[m.crc(name)].append(dict(name=name,texture=m.string(p.get('dt_name',b'')),
                  kind=m.string(p.get('type',b'')),library=path.relative_to(DATA).as_posix().lower()))
    return mats


def constructs(flat):
    sizes={'fix':176,'rev':208,'pris':208,'sphere':212}
    result=[]
    for path,blob in flat.items():
        if '/cmpnd/cons/' not in path:continue
        kind=path.rsplit('/',1)[-1];size=sizes[kind]
        assert len(blob)%size==0,(path,len(blob))
        for at in range(0,len(blob),size):
            parent=m.string(blob[at:at+64]);name=m.string(blob[at+64:at+128])
            f=np.frombuffer(blob,'<f4',(size-128)//4,at+128).astype(float)
            row=dict(name=name,parent=parent,kind=kind,origin=f[:3].tolist(),
                     rotation=f[3:12].reshape(3,3).tolist() if kind=='fix' else f[6:15].reshape(3,3).tolist())
            if kind!='fix':row['offset']=f[3:6].tolist()
            if kind in ('rev','pris'):row.update(axis=f[15:18].tolist(),limits=f[18:].tolist())
            if kind=='sphere':row['limits']=f[15:].tolist()
            result.append(row)
    return result


def channels(flat,joints):
    result=[];jointmap={j['name'].lower():j for j in joints}
    for path,blob in flat.items():
        if not path.endswith('/channel/header') or '/animation/' not in path:continue
        count,interval,flags=S.unpack('<IfI',blob)
        raw=flat[path.rsplit('/',1)[0]+'/frames']
        root=path.rsplit('/channel/',1)[0]
        name=m.string(flat.get(root+'/child name',b''));parent=m.string(flat.get(root+'/parent name',b''))
        dims={1:1,4:4}.get(flags)
        assert dims is not None,flags
        width=dims+(interval<0)
        expected=count*width*4
        assert len(raw)>=expected,(path,count,interval,flags,len(raw))
        frames=np.frombuffer(raw[:expected],'<f4').reshape(count,width).astype(float)
        times=frames[:,0] if interval<0 else np.arange(count)*interval
        values=frames[:,1:] if interval<0 else frames
        script=path.split('/script/',1)[1].split('/')[0]
        row=dict(script=script,child=name,parent=parent,count=count,interval=interval,flags=flags,
                 duration=float(times[-1]),times=times.tolist(),values=values.tolist(),
                 minimum=values.min(0).tolist(),maximum=values.max(0).tolist(),
                 first=values[0].tolist(),last=values[-1].tolist(),monotonic_times=bool(np.all(np.diff(times)>=0)),
                 finite=bool(np.isfinite(frames).all()),bound_joint=name.lower() in jointmap,
                 frames_bytes=len(raw),expected_bytes=expected,native_size_valid=len(raw)==expected,
                 extra_floats=np.frombuffer(raw[expected:],'<f4').astype(float).tolist())
        if name.lower() in jointmap:
            j=jointmap[name.lower()];row['joint_kind']=j['kind'];row['axis']=j.get('axis')
            if j['kind']=='rev' and flags==1:
                row['degrees']=[float(np.degrees(values.min())),float(np.degrees(values.max()))]
                row['degrees_endpoints']=[float(np.degrees(values[0,0])),float(np.degrees(values[-1,0]))]
            if j['parent'].lower()!=parent.lower():row['parent_mismatch']=True
        if flags==4:row['quaternion_norm_range']=[float(np.linalg.norm(values,axis=1).min()),float(np.linalg.norm(values,axis=1).max())]
        result.append(row)
    return result


def decode(blob):
    flags,primitive,ng,ni,fvf,nv=S.unpack_from('<II4H',blob)
    if flags!=1 or primitive not in (2,4) or (fvf&0xe)!=2:
        raise ValueError('Unsupported vertex format '+hex(fvf))
    normals=3*bool(fvf&0x10);colours=int(bool(fvf&0x40))+int(bool(fvf&0x80))
    texture_sizes=[(2,3,4,1)[(fvf>>(16+2*i))&3] for i in range((fvf>>8)&15)]
    width=3+normals+colours+sum(texture_sizes);at=16+12*ng;start=at+2*ni
    raw=np.frombuffer(blob,'<f4',nv*width,start).reshape(nv,width)
    assert not any(blob[start+nv*width*4:]),'Non-padding data after vertices'
    verts=np.zeros((nv,8));verts[:,:3]=raw[:,:3]
    if normals:verts[:,3:6]=raw[:,3:6]
    if texture_sizes:
        n=min(2,texture_sizes[0]);v=3+normals+colours;verts[:,6:6+n]=raw[:,v:v+n]
    return verts,[S.unpack_from('<I4H',blob,16+12*i) for i in range(ng)],np.frombuffer(blob,'<u2',ni,at).astype(int)


def quat_rotation(v):
    # EngBase AxisAngleToQuat writes W,X,Y,Z. This is not Blender's xyzw convention.
    w,x,y,z=np.array(v,float)/max(np.linalg.norm(v),1e-20)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


def matrices(joints,values=None):
    values=values or {};byname={j['name'].lower():j for j in joints};out={'root':(np.eye(3),np.zeros(3))}
    stack=set()
    def get(name):
        name=name.lower()
        if name in out:return out[name]
        if name not in byname:return np.eye(3),np.zeros(3)
        assert name not in stack,'Cyclic construct '+name
        stack.add(name);j=byname[name]
        r=np.array(j['rotation']);v=values.get(name)
        if j['kind']=='rev' and v is not None:
            axis=m.unit(np.array(j['axis']));angle=v[0]
            r=quat_rotation([np.cos(angle/2),*(axis*np.sin(angle/2))])@r
        elif j['kind']=='sphere' and v is not None:r=quat_rotation(v)@r
        t=np.array(j['origin'])-r@np.array(j.get('offset',[0,0,0]))
        if j['kind']=='pris' and v is not None:t=t+np.array(j['axis'])*v[0]
        pr,pt=get(j['parent']);out[name]=(pr@r,pr@t+pt);stack.remove(name)
        return out[name]
    for name in byname:get(name)
    return out


def read_model(path,config,materials):
    rel=path.relative_to(DATA).as_posix().lower()
    blob=path.read_bytes()
    record=dict(path=rel,key=slug(rel),bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),
                aliases=config['aliases'].get(rel,[]),family=rel.split('/')[1] if len(rel.split('/'))>2 else 'external',extension=path.suffix.lower(),
                sur=path.with_suffix('.sur').exists())
    if not blob:
        record['error']='Empty file (0 bytes)';return record,None
    if blob[:4]!=b'UTF ':
        record['error']='Not a UTF model; first 40 bytes: '+blob[:40].hex(' ')
        return record,None
    _,nodes=m.read_tree(blob)
    flat={p.lower():n.blob for p,n in m.walk(nodes)}
    joints=constructs(flat);tracks=channels(flat,joints)
    record.update(constructs=joints,channels=tracks)
    record['vmesh_headers']=[dict(name=p.split('/')[-2],flags=S.unpack_from('<I',n.blob)[0],
         primitive=S.unpack_from('<I',n.blob,4)[0],groups=S.unpack_from('<H',n.blob,8)[0],
         indices=S.unpack_from('<H',n.blob,10)[0],fvf=S.unpack_from('<H',n.blob,12)[0],
         vertices=S.unpack_from('<H',n.blob,14)[0]) for p,n in m.walk(nodes) if p.lower().endswith('/vmeshdata')]
    libs={m.crc(p.split('/')[-2]):decode(n.blob) for p,n in m.walk(nodes) if p.lower().endswith('/vmeshdata')}
    names={}
    for p,b in flat.items():
        if '/cmpnd/' in p and p.endswith('/file name'):names[m.string(b).lower()]=m.string(flat[p.rsplit('/',1)[0]+'/object name'])
    transforms=matrices(joints)
    references=[];rest=[];used=set();part_points={};warnings=[];reference_headers=[]
    for p,b in flat.items():
        if not p.endswith('/vmeshref'):continue
        part=p.split('/')[2] if path.suffix.lower()=='.cmp' and len(p.split('/'))>4 else path.name.lower()
        match=re.search(r'/level(\d+)/',p)
        lod=int(match.group(1)) if match else 0
        size,mid,start,nv,ix,ni,first,ng=S.unpack_from('<II6H',b)
        rh=dict(path=p,part=part,lod=lod,mesh_crc=mid,vertex_start=start,vertices=nv,
                index_start=ix,indices=ni,first_group=first,groups=ng,status='resolved')
        reference_headers.append(rh)
        if mid==0 and nv==0 and ni==0 and ng==0:
            rh['status']='empty placeholder';continue
        try:groups=a.extract(b,libs)
        except Exception as e:
            rh['status']='unresolved';rh['error']=type(e).__name__+': '+str(e)
            warnings.append(p+': '+rh['error']);continue
        if not groups:
            warnings.append(p+': empty VMeshRef');continue
        used.update(g['material'] for g in groups)
        positions=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in groups])
        references.append(dict(part=part,lod=lod,direct=match is None,
            triangles=sum(len(g['corners']) for g in groups),groups=len(groups),materials=sorted({g['material'] for g in groups}),
            bounds=[positions.min(0).tolist(),positions.max(0).tolist()]))
        if lod==0:
            name=names.get(part,'Root');r,t=transforms.get(name.lower(),(np.eye(3),np.zeros(3)))
            part_points.setdefault(name.lower(),[]).append(positions)
            for g in groups:
                c=g['corners'].copy();c[...,:3]=c[...,:3]@r.T+t;c[...,3:6]=c[...,3:6]@r.T
                rest.append(dict(material=g['material'],corners=c,part=part))
    lods={}
    parts=sorted({r['part'] for r in references})
    for level in sorted({r['lod'] for r in references}):
        selected=[]
        for part in parts:
            available=[r for r in references if r['part']==part]
            chosen=max((r['lod'] for r in available if r['lod']<=level),default=min(r['lod'] for r in available))
            selected.extend(r for r in available if r['lod']==chosen)
        lods[str(level)]=dict(triangles=sum(r['triangles'] for r in selected),groups=sum(r['groups'] for r in selected))
    hardpoints=[]
    for p,b in flat.items():
        if '/hardpoints/' not in p or not p.endswith('/position'):continue
        hp_root=p.rsplit('/',1)[0]
        hardpoints.append(dict(part=p.split('/')[2],name=p.split('/')[-2],kind=p.split('/')[-3],
            position=np.frombuffer(b,'<f4').tolist(),
            orientation=np.frombuffer(flat.get(hp_root+'/orientation',b''),'<f4').tolist(),
            limits={k:np.frombuffer(flat[hp_root+'/'+k],'<f4').tolist() for k in ('min','max') if hp_root+'/'+k in flat}))
    mat_rows=[]
    for key in sorted(used):
        choices=materials.get(key,[])
        mat_rows.append(dict(crc=key,definitions=choices))
        if not choices:warnings.append('Material definition not found in DATA MAT / embedded ship libraries: '+hex(key))
    for ch in tracks:
        if not ch['native_size_valid']:
            warnings.append(f"{ch['script']}/{ch['child']}: frames {ch['frames_bytes']} bytes != declared {ch['expected_bytes']}; EngBase ChannelArchetypeLoad rejects this size. Declared keys and trailing floats preserved separately.")
    wireframes=[]
    for p,b in flat.items():
        if not p.endswith('/vwiredata'):continue
        size,mid,bias,remap,count,nv=S.unpack_from('<II4H',b)
        indices=np.frombuffer(b,'<u2',count,16)
        valid=mid in libs and (not count or int(indices.max())<len(libs[mid][0]))
        wireframes.append(dict(path=p,mesh_crc=mid,bias=bias,remap_count=remap,index_count=count,
                               declared_vertices=nv,available_vertices=len(libs[mid][0]) if mid in libs else None,
                               index_range=[int(indices.min()),int(indices.max())] if count else [],
                               base_index_range_valid=valid,bytes=len(b)))
        if not valid:warnings.append(p+': wire indices/VMesh library need review')
    motion=[]
    for script in sorted({c['script'] for c in tracks}):
        cs=[c for c in tracks if c['script']==script];duration=max(c['duration'] for c in cs)
        frames=[]
        for phase in np.linspace(0,1,9):
            t=phase*duration;v={}
            for ch in cs:
                ar=np.array(ch['values'])
                if ch['native_size_valid'] and ch['bound_joint'] and not ch.get('parent_mismatch'):
                    v[ch['child'].lower()]=np.array([np.interp(t,ch['times'],ar[:,i]) for i in range(ar.shape[1])])
            mats=matrices(joints,v)
            corners=[]
            for name,arrays in part_points.items():
                r,offset=mats.get(name,(np.eye(3),np.zeros(3)))
                p=np.concatenate(arrays)
                lo,hi=p.min(0),p.max(0)
                box=np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
                corners.extend(box@r.T+offset)
            if corners:
                p=np.array(corners);frames.append([p.min(0).tolist(),p.max(0).tolist()])
        motion.append(dict(script=script,samples=len(frames),bound_type='union of transformed component AABBs; conservative',
                           first=frames[0] if frames else None,last=frames[-1] if frames else None))
    if rest:
        pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in rest]);record['bounds']=[pts.min(0).tolist(),pts.max(0).tolist()]
    record.update(parts=references,reference_headers=reference_headers,lods=lods,hardpoints=hardpoints,materials=mat_rows,motion=motion,warnings=warnings,wireframes=wireframes,
                  embedded_materials=[p for p in flat if '/material library/' in p and p.endswith('/type')],
                  vmesh_count=len(libs),unbound_channels=[c['script']+'/'+c['child'] for c in tracks if not c['bound_joint']],
                  metal_parts=[dict(part=r['part'],lod=r['lod']) for r in references if any(any('metal' in d['texture'].lower() or d['name'].lower().startswith('metal') for d in materials.get(k,[])) for k in r['materials'])])
    return record,rest


def esc(value):return str(value).replace('|','\\|').replace('\n',' ')
def fmt(v):return ', '.join(f'{x:.5g}' for x in v)


def write_page(r):
    text=[f"# {Path(r['path']).name}\n",f"Источник: `{r['path']}`. SHA-256: `{r['sha256']}`. Размер: {r['bytes']} байт.\n",
          'Это файл текущей установки, а не утверждение о его тождественности чистому retail.\n']
    if 'error' in r:text += ['Ошибка чтения: '+r['error']+'\n']
    else:
        text += [f"Архетипы: {', '.join('`'+v['nickname']+'`' for v in r['aliases']) or 'нет активной ссылки ships INI'}. SUR рядом: {'да' if r['sur'] else 'нет'}.\n",
                 '## Геометрия и LOD\n','Эффективные суммы учитывают последнюю доступную детализацию каждой части и прямые VMeshPart.\n',
                 '| LOD | Треугольники | Материальные группы |','|---|---:|---:|']
        for level,v in r['lods'].items():text.append(f"| {level} | {v['triangles']} | {v['groups']} |")
        text += ['\n| Часть | LOD | Треугольники | Группы | Хранение |','|---|---:|---:|---:|---|']
        for p in r['parts']:text.append(f"| {p['part']} | {p['lod']} | {p['triangles']} | {p['groups']} | {'VMeshPart' if p['direct'] else 'MultiLevel'} |")
        for ref in r['reference_headers']:
            if ref['status']!='resolved':text.append(f"\nСсылка `{ref['path']}`: **{ref['status']}**, CRC `{ref['mesh_crc']:08x}`, индексов {ref['indices']}. "+('Сумма геометрии неполная.' if ref['status']=='unresolved' else 'Пустая служебная часть, не потерянный меш.'))
        text += ['\n### Библиотеки VMesh и wireframe\n','| VMesh | Вершины | Индексы | Группы | Primitive / FVF |','|---|---:|---:|---:|---|']
        for h in r['vmesh_headers']:text.append(f"| {h['name']} | {h['vertices']} | {h['indices']} | {h['groups']} | {h['primitive']} / {h['fvf']:x} |")
        for w in r['wireframes']:text.append(f"\nWire `{w['path']}`: {w['index_count']} индексов, bias {w['bias']}, диапазон {w['index_range']}, библиотека `{w['mesh_crc']:08x}`. Проверка базового диапазона: {w['base_index_range_valid']}.")
        text += ['\n## Конструкции и шарниры\n','Оси локальные, значения REV в радианах; PRIS — перемещение. Это данные файла, не догадка по имени.\n',
                 '| Дочерняя часть | Родитель | Тип | Origin | Ось | Ограничения |','|---|---|---|---|---|---|']
        for j in r['constructs']:text.append(f"| {j['name']} | {j['parent']} | {j['kind']} | {fmt(j['origin'])} | {fmt(j.get('axis',[]))} | {fmt(j.get('limits',[]))} |")
        text += ['\n## Анимации\n','Первый/последний ключ не называется автоматически «сложено/раскрыто»: семантика проверяется по контроллеру и реальной геометрии. Полные времена и значения каждого ключа — в соседнем JSON.\n',
                 '| Скрипт | Часть ← родитель | Тип / ключи | Длительность | Начало → конец | Диапазон | Связь |','|---|---|---|---:|---|---|---|']
        for c in r['channels']:
            values=c.get('degrees_endpoints');ends=f'{values[0]:.3f}° → {values[1]:.3f}°' if values else fmt(c['first'])+' → '+fmt(c['last'])
            span=fmt(c.get('degrees',c['minimum']))+('°' if 'degrees' in c else ' / '+fmt(c['maximum']))
            text.append(f"| {c['script']} | {c['child']} ← {c['parent']} | {c['joint_kind'] if c['bound_joint'] else 'unbound'} / {c['count']} | {c['duration']:.6g} | {ends} | {span} | {'не найдена' if not c['bound_joint'] else 'родитель отличается' if c.get('parent_mismatch') else 'есть'} |")
        text += ['\n## Хардпоинты\n','| Имя | Владелец | Тип | Позиция |','|---|---|---|---|']
        for h in r['hardpoints']:text.append(f"| {h['name']} | {h['part']} | {h['kind']} | {fmt(h['position'])} |")
        text += ['\n<details><summary>Все ключи анимаций: время и значение</summary>\n']
        for c in r['channels']:
            text.append(f"- `{c['script']}` / `{c['child']}`: "+'; '.join(f"{t:.7g}: [{fmt(v)}]" for t,v in zip(c['times'],c['values'])))
            if c['extra_floats']:text.append(f"  Лишние данные за объявленными ключами (не воспроизводятся как дополнительные ключи): {c['extra_floats']}.")
        text += ['\n</details>\n']
        text += ['\n## Материалы\n','Определения перечислены из MAT в DATA и встроенных библиотек кораблей; это список кандидатов, а не установленный порядок загрузки. Наличие metal на Root само по себе не определяет, внутренняя это поверхность или наружная.\n',
                 '| CRC | Материал | Текстура | Библиотека |','|---|---|---|---|']
        for mat in r['materials']:
            for d in mat['definitions'] or [dict(name='не найдено',texture='',library='')]:text.append(f"| {mat['crc']:08x} | {d['name']} | {d['texture']} | {d['library']} |")
        text += ['\n## Архетип и разрушение\n']
        for alias in r['aliases']:
            text.append(f"\n### {alias['nickname']} — {alias['source']}\n")
            for k in ('type','da_archetype','material_library','lodranges','cockpit','bay_door_anim','shield_link','hp_bay_surface','hp_bay_external'):
                if k in alias['values']:text.append(f"- `{k}`: "+'; '.join(alias['values'][k]))
            if alias['collision_groups']:
                text+=['\n| Отделяемая часть | dmg_hp | dmg_obj | separable |','|---|---|---|---|']
                for cg in alias['collision_groups']:text.append('| '+' | '.join(', '.join(cg.get(k,[])) for k in ('obj','dmg_hp','dmg_obj','separable'))+' |')
        text += ['\n## Проверки и ограничения\n',f"Прочитаны заголовки VMeshRef: {len(r['reference_headers'])}; разрешено геометрических ссылок: {len(r['parts'])}; библиотек VMesh: {r['vmesh_count']}; sampled scripts: {len(r['motion'])}.\n",
                 'Сэмплы движения используют компоненты с их иерархией; AABB являются консервативными. Это не тест столкновений и не запуск игры.\n']
        for warning in r['warnings']:text.append('- '+warning)
        if r['unbound_channels']:text.append('\nНесвязанные каналы (в том числе возможные неиспользуемые исторические скрипты): '+', '.join(r['unbound_channels']))
        if r.get('preview'):text.append(f"\n![Нулевая поза, два ракурса](../previews/{r['key']}.jpg)\n")
    text += [f"\n[Машиночитаемые данные со всеми ключами]({r['key']}.json)\n"]
    (OUT/'models'/f"{r['key']}.md").write_text('\n'.join(text),encoding='utf8')
    (OUT/'models'/f"{r['key']}.json").write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');args=parser.parse_args()
    for sub in ('models','previews','contacts'):(OUT/sub).mkdir(parents=True,exist_ok=True)
    config=configuration();materials=material_index(config)
    files={p.resolve() for p in (DATA/'SHIPS').rglob('*') if p.suffix.lower() in ('.cmp','.3db')}
    missing=[]
    for rel in config['aliases']:
        p=DATA/rel
        if p.suffix.lower() not in ('.cmp','.3db'):continue
        if p.exists():files.add(p.resolve())
        else:missing.append(rel)
    prior_file=OUT/'inventory.json'
    prior={r['key']:r['sha256'] for r in json.loads(prior_file.read_text(encoding='utf8'))['models']} if prior_file.exists() else {}
    records=[];hash_previews={};font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',16)
    for i,path in enumerate(sorted(files,key=lambda p:str(p).lower())):
        try:r,scene=read_model(path,config,materials)
        except Exception as e:
            blob=path.read_bytes();rel=path.relative_to(DATA).as_posix().lower()
            r=dict(path=rel,key=slug(rel),extension=path.suffix.lower(),family=rel.split('/')[1] if len(rel.split('/'))>2 else 'external',bytes=len(blob),
                   sha256=hashlib.sha256(blob).hexdigest(),error=type(e).__name__+': '+str(e));scene=None
        if args.render and scene and (r['extension']=='.cmp' or any(v['section']=='ship' for v in r.get('aliases',[]))):
            target=OUT/'previews'/f"{r['key']}.jpg"
            if target.exists() and prior.get(r['key'])==r['sha256']:
                hash_previews[r['sha256']]=target
            elif r['sha256'] in hash_previews:
                target.write_bytes(hash_previews[r['sha256']].read_bytes())
            else:
                # Neutral render is deliberate: it reveals the primary geometry without
                # guessing material-library precedence for inactive model variants.
                mats={g['material']:dict(name=str(g['material']),image=None,colour=np.ones(3)) for g in scene}
                p=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in scene]);c=(p.min(0)+p.max(0))/2
                radius=np.linalg.norm(p-c,axis=1).max()
                im=Image.new('RGB',(720,395),(24,29,37));d=ImageDraw.Draw(im)
                d.text((10,8),path.stem[:58]+' / '+str(r['lods'].get('0',{}).get('triangles',0)),font=font,fill='white')
                for col,cam in enumerate(((1,.7,-1.3),(-1,.6,1.2))):
                    im.paste(a.render(scene,mats,c,max(radius,1e-5),cam,360,'clay'),(360*col,35))
                im.save(target,quality=88);hash_previews[r['sha256']]=target
            im=Image.open(target).convert('RGB');d=ImageDraw.Draw(im)
            d.rectangle((0,0,719,34),fill=(24,29,37))
            d.text((10,8),path.stem[:58]+' / '+str(r['lods'].get('0',{}).get('triangles',0)),font=font,fill='white')
            im.save(target,quality=90)
            r['preview']=str(target.relative_to(OUT))
        write_page(r);records.append(r)
        if i%20==0:print('AUDIT',i+1,'/',len(files),r['path'],r.get('error','OK'),flush=True)
    good=[r for r in records if 'error' not in r]
    summary=dict(files=len(records),by_extension=dict(collections.Counter(r['extension'] for r in records)),
         errors=[dict(path=r['path'],error=r['error']) for r in records if 'error' in r],
         missing_active_models=missing,unique_contents=len({r['sha256'] for r in records}),
         channels=sum(len(r['channels']) for r in good),constructs=dict(collections.Counter(j['kind'] for r in good for j in r['constructs'])),
         animated_files=sum(bool(r['channels']) for r in good),rendered_cmp=sum('preview' in r and r['extension']=='.cmp' for r in records),
         rendered_3db_ships=sum('preview' in r and r['extension']=='.3db' for r in records))
    (OUT/'inventory.json').write_text(json.dumps(dict(summary=summary,configuration=config,models=records),ensure_ascii=False,indent=2),encoding='utf8')
    text=['# Полный каталог корабельных исходников\n',
          'Источник — текущая DATA вашей сборки. Все CMP и 3DB в DATA/SHIPS, плюс прямые ссылки активных ship/simple-архетипов вне этой папки. Исходные файлы только читались.\n',
          f"Всего файлов: **{summary['files']}**; CMP/3DB: `{summary['by_extension']}`. Анимационных каналов: **{summary['channels']}**. Файлов с анимацией: **{summary['animated_files']}**.\n",
          'Полный разбор каждого файла включает все LOD, части, шарниры, каналы, хардпоинты и материалы. Для повреждённых/пустых файлов приведена ошибка, а не выдуманный результат.\n',
          '## CMP — составные модели\n','| Файл | LOD0 / группы | Части / каналы | Активные архетипы |','|---|---|---|---|']
    for r in records:
        if r['extension']!='.cmp':continue
        l=r.get('lods',{}).get('0',{})
        text.append(f"| [{r['path']}](models/{r['key']}.md) | {l.get('triangles','?')} / {l.get('groups','?')} | {len(r.get('constructs',[]))} / {len(r.get('channels',[]))} | {esc(', '.join(a['nickname'] for a in r.get('aliases',[])))} |")
    text+=['\n## 3DB — детали, damage caps и самостоятельные модели\n','| Файл | LOD0 | Назначение / связь |','|---|---:|---|']
    for r in records:
        if r['extension']!='.3db':continue
        text.append(f"| [{r['path']}](models/{r['key']}.md) | {r.get('lods',{}).get('0',{}).get('triangles','?')} | {esc(r.get('error') or ', '.join(a['nickname'] for a in r.get('aliases',[])) or 'нет активной ссылки; не удалять автоматически')} |")
    text+=['\n## Ошибки и отсутствующие ссылки\n']
    for r in summary['errors']:text.append('- `'+r['path']+'`: '+r['error'])
    for path in missing:text.append('- Отсутствует активная ссылка: `'+path+'`.')
    (OUT/'README.md').write_text('\n'.join(text),encoding='utf8')
    rendered=[r for r in records if r.get('preview')]
    for start in range(0,len(rendered),8):
        subset=rendered[start:start+8];sheet=Image.new('RGB',(1440,395*((len(subset)+1)//2)),(24,29,37))
        for j,r in enumerate(subset):sheet.paste(Image.open(OUT/r['preview']),((j%2)*720,(j//2)*395))
        sheet.save(OUT/'contacts'/f'{start//8+1:02}.jpg',quality=90)
    print(json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
