import json,os,subprocess,re,sys
from pathlib import Path
import station_batch_model as p
import numpy as np
m=p.m
original=os.environ.get('STATION_CHECK_ORIGINAL')=='1'
candidate=os.environ.get('PHYSICS_TEST_BIN')
out=p.OUT/('physics_candidate' if candidate else ('physics_original' if original else 'physics_check'));out.mkdir(parents=True,exist_ok=True)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[m.REPO/'src/include',vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]+[Path('C:/DXSDK/Include')]))
env['LIB']=';'.join(map(str,[m.REPO/'bin',vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
env['PATH']=str(m.GAME/'bin')+';'+env['PATH']
if candidate:env['PATH']=candidate+';'+env['PATH']
env['_NT_SYMBOL_PATH']=str(m.REPO/'src/obj/graphics_auto_install/bin')+';'+str(m.GAME/'bin')
cmd=[str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/MD','/EHsc','/D_ITERATOR_DEBUG_LEVEL=1',str(m.REPO/'tools/check_station_batch_physics.cpp'),'/Fecheck.exe','/link','Common.lib','DALib.lib','dacom.lib']
subprocess.run(cmd,cwd=out,env=env,check=True)
(out/'check_dacom.ini').write_text('[DACOM]\nIgnoreDACOMEnv = true\nDllPath = '+str(m.GAME/'bin')+'\\\n[Libraries]\nReadFile.dll\nx86math.dll\nEngBase.dll\nsystem.dll\n[System]\n[Engine]\nHardpoint\nAnimation\n')
legacy=False
manifest=json.loads((p.OUT/'manifest.json').read_text());fixture=[]
p.CONFIG.update(manifest['config'])
folder=m.old.data_folder(m.GAME,p.OUT/'stage')
for c in manifest['components']:
    model=p.OUT/f"stage/DATA/SOLAR/OPTIMIZED/{p.TASK}/{c['name']}.cmp"
    fixture.append(f"{model.name} "+' '.join(map(str,c['origin']))+" 1 1")
    for body in c['bodies']:
        surface=p.OUT/f"stage/DATA/SOLAR/OPTIMIZED/{p.TASK}/{body['name']}.sur"
        hulls=m.old.leaves(dict(dict(m.old.parts(surface.read_bytes()))[m.utf.crc('Root')])[b'surf'])
        def largest(h):
            triangles=h.points[h.faces];areas=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)
            index=int(np.argmax(areas));return float(areas[index]),triangles[index]
        _,triangle=max((largest(h) for h in hulls),key=lambda x:x[0])
        a,b,d=triangle;normal=np.cross(b-a,d-a);normal/=np.linalg.norm(normal)
        center=(a+b+d)/3+np.array(body['origin'])
        rays=np.concatenate([center+normal*2,center-normal*2])
        fixture.append(body['name']+'.cmp '+' '.join(map(str,body['origin']))+' 1 0 '+' '.join(map(str,np.eye(3).flat))+' '+' '.join(map(str,rays)))
# Include the unchanged working dock and both retained towers at their actual
# template poses. Stage their existing assets through the same DATA API.
raw_source=(m.GAME/p.TEMPLATE).read_text(encoding='utf-8-sig')
if p.CONFIG.get('static'):source=p.source_text(raw_source)
else:
    sources=p.templates(raw_source)
    source=sources.get(p.CLASS+'Original',sources[p.CLASS])
source=source.replace(p.SOURCE_PREFIX,p.PREFIX)
p.GROUPS.update({name:c['group'] for c in manifest['components'] for name in c['members']})
if original:fixture=[];p.GROUPS.clear()
retained=[];pods=[];missing_mounts=[]
builder=m.Builder();folder=m.old.data_folder(m.GAME,p.OUT/'stage')
stage_solars,_,stage_loadouts=m.b.catalog(p.OUT/'stage/DATA')
builder.solars.update(stage_solars);builder.loadouts.update(stage_loadouts)
for row in m.b.placements_from_template(source):
    if p.group(row):continue
    if row.name in p.CONFIG.get('omit',[]):continue
    import dataclasses
    row=dataclasses.replace(row,**p.CONFIG.get('overrides',{}).get(row.name,{}))
    arch=builder.solars[row.archetype.lower()]
    relative=m.old.one(arch,'da_archetype').replace('\\','/')
    path=p.OUT/'stage/DATA'/relative
    if not path.exists():path=m.b.model_path(m.GAME/'DATA',relative)
    for asset in (path,path.with_suffix('.sur')):
        if asset.exists():folder.sync_data_file('SOLAR/OPTIMIZED/'+p.TASK+'/'+asset.name,asset.read_bytes())
    rot=m.old.euler_matrix(*row.rotate)
    root_id=m.utf.crc('Root') if path.suffix.lower()=='.cmp' else 0
    count=1+(sum(ident!=root_id and b'!fxd' in dict(chunks) for ident,chunks in m.old.parts(path.with_suffix('.sur').read_bytes())) if path.with_suffix('.sur').exists() else 0)
    retained.append(path.name+' '+' '.join(map(str,row.pos))+f' {count} 0 '+' '.join(map(str,rot.flat)))
    loadout=row.loadout or m.old.one(arch,'loadout')
    def mount_names(node):
        result=set(m.b.hardpoints(node))
        for child in node.children:result.update(mount_names(child))
        return result
    original_mounts=mount_names(m.utf.read_tree(path.read_bytes())[1][0])
    for line in builder.loadouts.get(loadout,{}).get('equip',[]):
        fields=[s.strip() for s in line.split(',')];eq=builder.equipment.get(fields[0].lower(),{})
        if eq.get('section')!='cargopod':continue
        if fields[1].lower() not in original_mounts:
            missing_mounts.append(dict(object=row.name,model=str(path),loadout=loadout,entry=line))
            continue
        model=m.b.model_path(m.GAME/'DATA',m.old.one(eq,'da_archetype'))
        for asset in (model,model.with_suffix('.sur')):
            if asset.exists():folder.sync_data_file('SOLAR/OPTIMIZED/'+p.TASK+'/'+asset.name,asset.read_bytes())
        pods.append(f"{len(retained)} {model.name} {m.old.one(eq,'hp_child','HpRoot')} {fields[1]}")
fixture=retained+fixture
(out/'fixture.txt').write_text('\n'.join(fixture))
(out/'fixture.txt.pods').write_text('\n'.join(pods))
approaches=[]
if p.CONFIG.get('dock_model') and not original:
    from station_docks import direct,entries
    root=m.utf.read_tree((m.GAME/p.CONFIG['dock_model'].get('source_model','DATA/SOLAR/DOCKABLE/space_police01.cmp')).read_bytes())[1][0]
    source_hp=m.b.hardpoints(direct(root,dict(entries(root))['Root']))
    primary=next(r for r in m.b.placements_from_template(source) if r.name==p.CONFIG['dock_model'].get('root_name',p.PREFIX+'_dock'))
    primary=dataclasses.replace(primary,**p.CONFIG.get('overrides',{}).get(primary.name,{}))
    main=(m.old.euler_matrix(*primary.rotate),np.array(primary.pos))
    for port in p.CONFIG['dock_model']['ports']:
        pose=m.b.compose(main,(np.array(port['rotation']),np.array(port['position'])))
        letter=port.get('source_letter','b' if p.CONFIG['dock_model'].get('active_side',1)==2 else 'a')
        a=m.b.compose(pose,source_hp['hpdockpoint'+letter+'02'])[1]
        b=m.b.compose(pose,source_hp['hpdockpoint'+letter+'01'])[1]
        approaches.append(' '.join(map(str,np.concatenate([a,b]))))
(out/'fixture.txt.approaches').write_text('\n'.join(approaches))

(out/'original_missing_mounts.json').write_text(json.dumps(missing_mounts,indent=2))
print('Retained original cargo mounts:',len(pods),'; absent in original model:',len(missing_mounts),flush=True)
logpath=out/'result.log'
with logpath.open('wb') as log:
    result=subprocess.run([str(out/'check.exe'),str(p.OUT/('stage/DATA/SOLAR/OPTIMIZED/'+p.TASK)),str(out/'fixture.txt')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=40)
print(logpath.read_text(errors='replace')[-5000:]);result.check_returncode()
if not original and not candidate:(p.OUT/'physics_check.ok').write_text(m.old.sha256((p.OUT/'manifest.json').read_bytes()).hexdigest())
