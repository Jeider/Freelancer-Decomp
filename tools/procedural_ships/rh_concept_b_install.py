"""Prepare/apply the approved RH B assets via Pythonlancer's DATA API only."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import difflib
import rh_concept_b_final as f

GAME=Path('D:/Games/FL_MOD')
API=GAME/'Assets/Pythonlancer/tools/data_folder.py'
STAGE=f.OUT/'install'
PREFIX='ships/rheinland/rh_concept_b/'
API_METHOD='''
    # BEGIN RH CONCEPT B ASSET OUTPUT
    def sync_rh_concept_b(self, files):
        """Install, stage or restore the approved model through the DATA API."""
        import re
        fixed = {'SHIPS/shiparch.ini',
                 'ships/rheinland/rh_concept_b/rh_concept_b.cmp',
                 'ships/rheinland/rh_concept_b/rh_concept_b.sur',
                 'ships/rheinland/rh_concept_b/rh_concept_b_lods.mat'}
        for name in files:
            damage = re.fullmatch(r'ships/rheinland/rh_concept_b/damage/rh_b_(dmg|break)_(port_wing|starboard_wing|port_engine|starboard_engine|tail)\\.(3db|sur)', name)
            if name not in fixed and not damage:
                raise ValueError('Unexpected RH concept B target: ' + name)
            self.data_path(name)
        for name, content in files.items():
            if content is None:
                self.remove_data_file(name)
            else:
                self.sync_data_file(name, content)
    # END RH CONCEPT B ASSET OUTPUT
'''


def digest(raw):return hashlib.sha256(raw).hexdigest() if raw is not None else None
def load_api(path):
    spec=importlib.util.spec_from_file_location('rh_b_data_folder',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.DataFolder


def sections(text):
    starts=list(re.finditer(r'^\[([^\]\r\n]+)\][^\r\n]*(?:\r?\n|$)',text,re.M))
    return [(m.group(1).lower(),m.start(),starts[i+1].start() if i+1<len(starts) else len(text)) for i,m in enumerate(starts)]


def field(text,key):
    m=re.search(r'^\s*'+re.escape(key)+r'\s*=\s*([^;\r\n]+)',text,re.M|re.I)
    return m.group(1).strip() if m else None


def set_field(text,key,value,newline):
    pattern=r'^([ \t]*'+re.escape(key)+r'[ \t]*=[ \t]*)[^\r\n]*'
    if re.search(pattern,text,re.M|re.I):
        return re.sub(pattern,lambda m:m.group(1)+value,text,count=1,flags=re.M|re.I)
    return text.rstrip('\r\n')+newline+key+' = '+value+newline+newline


def patch_shiparch(raw):
    text=raw.decode('latin1');newline='\r\n' if '\r\n' in text else '\n'
    descriptions=json.loads((f.OUT/'damage_manifest.json').read_text())
    zones={d['part'].lower():d for d in descriptions}
    own_simples={Path(d[k]['file']).stem+'_cap' for d in descriptions for k in ('parent','debris')}
    spans=sections(text);active=False;changed=0;ships=0;edits=[]
    for kind,a,b in spans:
        block=text[a:b];new=block
        if kind=='ship':
            active=field(block,'nickname')=='rh_elite_pir'
            if active:
                ships+=1
                new=set_field(new,'DA_archetype',PREFIX.replace('/','\\')+'rh_concept_b.cmp',newline)
                new=set_field(new,'LODranges','0, 180, 550, 10000',newline)
                library=PREFIX.replace('/','\\')+'rh_concept_b_lods.mat'
                if not re.search(r'^material_library\s*=\s*'+re.escape(library)+r'\s*$',new,re.M|re.I):
                    new=new.rstrip('\r\n')+newline+'material_library = '+library+newline+newline
        elif kind=='collisiongroup' and active:
            zone=zones.get((field(block,'obj') or '').lower())
            if zone:
                changed+=1
                for key,value in (('dmg_obj',Path(zone['parent']['file']).stem+'_cap'),('group_dmg_hp','DpBreak'),('group_dmg_obj',Path(zone['debris']['file']).stem+'_cap')):
                    new=set_field(new,key,value,newline)
        elif kind=='simple' and field(block,'nickname') in own_simples:
            new=''
        if new!=block:edits.append((a,b,new))
    assert ships==1 and changed==5,(ships,changed)
    for a,b,new in reversed(edits):text=text[:a]+new+text[b:]
    fragment=(f.OUT/'shiparch_fragment.ini').read_text(encoding='utf8')
    caps=[fragment[a:b].strip().replace('\n',newline) for kind,a,b in sections(fragment) if kind=='simple']
    assert len(caps)==10
    text=text.rstrip('\r\n')+newline+newline+('; RH concept B: shared-MAT damage caps'+newline)+ (newline+newline).join(caps)+newline
    # Explicitly preserve every balance/cockpit/flight field in the target Ship.
    def target(source):
        return next(source[a:b] for k,a,b in sections(source) if k=='ship' and field(source[a:b],'nickname')=='rh_elite_pir')
    def immutable(block):
        return [ln for ln in block.splitlines() if ln.strip() and not re.match(r'\s*(da_archetype|lodranges|material_library)\s*=',ln,re.I)]
    assert immutable(target(raw.decode('latin1')))==immutable(target(text))
    return text.encode('latin1')


def prepare():
    checks=json.loads((f.OUT/'checks.json').read_text());blend=json.loads((f.OUT/'blend_checks.json').read_text())
    assert checks['cmp_sha256']==blend['cmp_sha256']==f.digest(f.DEST)
    assert f.digest(f.OUT/'rh_concept_b_rigged.blend')==blend['blend_sha256']
    STAGE.mkdir(exist_ok=True)
    before_api=API.read_bytes();api_text=before_api.decode('utf8')
    if '# BEGIN RH CONCEPT B ASSET OUTPUT' not in api_text:
        api_text=api_text.rstrip()+'\n'+API_METHOD
    after_api=api_text.encode('utf8');prepared_api=STAGE/'data_folder.py';prepared_api.write_bytes(after_api)
    DataFolder=load_api(prepared_api);stage=DataFolder(root=STAGE);game=DataFolder(root=GAME)
    files={PREFIX+p.name:p.read_bytes() for p in (f.DEST,f.OUT/'rh_concept_b.sur',f.LOD_MAT)}
    for p in sorted((f.OUT/'damage').glob('*')):
        if p.suffix in ('.3db','.sur'):files[PREFIX+'damage/'+p.name]=p.read_bytes()
    original=game.data_path('SHIPS/shiparch.ini').read_bytes()
    files['SHIPS/shiparch.ini']=patch_shiparch(original)
    assert len(files)==24
    stage.sync_rh_concept_b(files)
    entries=[]
    for name,raw in files.items():
        dest=game.data_path(name);before=dest.read_bytes() if dest.exists() else None
        assert stage.data_path(name).read_bytes()==raw
        entries.append(dict(relative=name,before=digest(before),after=digest(raw),bytes=len(raw)))
    (STAGE/'shiparch.diff').write_text(''.join(difflib.unified_diff(original.decode('latin1').splitlines(True),files['SHIPS/shiparch.ini'].decode('latin1').splitlines(True),fromfile='installed/shiparch.ini',tofile='prepared/shiparch.ini')),encoding='utf8')
    manifest=dict(game=str(GAME),cmp_sha256=f.digest(f.DEST),shared_mat_sha256=f.digest(f.SHARED_MAT),
                  api_before=digest(before_api),api_after=digest(after_api),files=entries,
                  scope='rh_elite_pir visual model, LOD MAT and 5 collision groups; 10 new caps. Balance/cockpit unchanged.')
    (STAGE/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('PREPARED',len(files),'DATA files;',sum(e['bytes'] for e in entries),'bytes. Game unchanged.',flush=True)


def apply():
    if (f.OUT/'installation_hold.json').exists():
        raise RuntimeError('Installation is suspended by the user for mapping review; see installation_hold.json')
    for name in ('freelancer.exe','flserver.exe'):
        r=subprocess.run(['tasklist','/FI','IMAGENAME eq '+name,'/FO','CSV','/NH'],capture_output=True,check=True)
        if name.encode() in r.stdout.lower():raise RuntimeError('Close '+name+' before installing')
    m=json.loads((STAGE/'manifest.json').read_text())
    assert m['game']==str(GAME) and m['cmp_sha256']==f.digest(f.DEST)
    assert f.digest(f.SHARED_MAT)==m['shared_mat_sha256']
    assert digest(API.read_bytes())==m['api_before']
    api_raw=(STAGE/'data_folder.py').read_bytes();assert digest(api_raw)==m['api_after']
    DataFolder=load_api(STAGE/'data_folder.py');game=DataFolder(root=GAME);stage=DataFolder(root=STAGE)
    before={};after={}
    for e in m['files']:
        name=e['relative'];target=game.data_path(name)
        before[name]=target.read_bytes() if target.exists() else None
        after[name]=stage.data_path(name).read_bytes()
        assert digest(before[name])==e['before'],('Changed since prepare',name)
        assert digest(after[name])==e['after'],name
    backup=DataFolder(root=STAGE/'transaction_backup')
    backup.sync_rh_concept_b({n:v for n,v in before.items() if v is not None})
    old_api=API.read_bytes();(STAGE/'data_folder.before.py').write_bytes(old_api)
    try:
        API.write_bytes(api_raw)
        Live=load_api(API);live=Live(root=GAME)
        live.sync_rh_concept_b(after)
        for name,raw in after.items():assert live.data_path(name).read_bytes()==raw,name
        assert f.digest(f.SHARED_MAT)==m['shared_mat_sha256']
    except Exception:
        game.sync_rh_concept_b(before)
        API.write_bytes(old_api)
        raise
    m['installed_verified']=True
    (f.OUT/'installation.json').write_text(json.dumps(m,indent=2))
    # Successful transaction: keep authoring models, remove installation duplicates.
    stage.sync_rh_concept_b({n:None for n in after})
    backup.sync_rh_concept_b({n:None for n,v in before.items() if v is not None})
    (STAGE/'data_folder.before.py').unlink()
    print('INSTALLED AND VERIFIED',len(after),'DATA files. Freelancer was not launched.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    apply() if args.apply else prepare()
