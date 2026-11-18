"""Verify and install customization UI localization in the client only."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/customization'
sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
base.OUT=OUT
base.BUILD=OUT/'build'
NAMES=('freelancer.exe','freelancer.pdb')
SOURCES=('src/freelancer/Client/customization_text.h','src/freelancer/Client/preferences_customization.cpp',
         'src/freelancer/Client/page_customization.cpp','src/include/player_customization.h')
PLAN=OUT/'language_install.json'


def prepare():
    # All existing RU captions and persisted keys must survive this text-only change.
    russian=re.compile(r'L"[^"\n]*\\u[0-9a-fA-F]{4}[^"\n]*"')
    for source in SOURCES[1:]:
        before=subprocess.check_output(['git','show','HEAD:'+source],cwd=ROOT,text=True,encoding='utf-8')
        after=(ROOT/source).read_text()
        assert russian.findall(before)==russian.findall(after),'Russian captions changed: '+source
        if source.endswith('player_customization.h'):
            keys=lambda text:re.findall(r'\{"([^"]+)", L"',text)
            assert keys(before)==keys(after),'Persisted customization keys changed'
            choices=re.findall(r'\{"[^"]+", L"[^"]+", L"([^"]+)"\}',after)
            assert len(choices)==32 and all(choice.isascii() for choice in choices)
    exe=base.BUILD/'bin/freelancer.exe'
    assert exe.stat().st_mtime>=max((ROOT/p).stat().st_mtime for p in SOURCES)
    dependencies,imports=base.verify_imports(('freelancer.exe',))
    for name in ('RP9.dll','D3D9.dll','dgVoodoo.conf'):
        dependencies[name]=base.digest(base.GAME/name)
    plan=dict(files={name:dict(before=base.digest(base.GAME/name),after=base.digest(base.BUILD/'bin'/name)) for name in NAMES},
              dependencies=dependencies,verified_imports=imports,
              sources={str(ROOT/p):base.digest(ROOT/p) for p in SOURCES},
              embedded_bytes=base.verify_resource(exe),validation='32 EN choice labels; all RU captions and saved keys preserved')
    PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Ready: localized client + symbols; {imports} imports checked; RU captions and saved keys preserved')


def apply():
    base.idle();plan=json.loads(PLAN.read_text())
    for path,expected in plan['sources'].items():assert base.digest(Path(path))==expected,path
    for name,expected in plan['dependencies'].items():assert base.digest(base.GAME/name)==expected,name
    previous={}
    for name in NAMES:
        target=base.safe(base.GAME/name,base.GAME)
        source=base.safe(base.BUILD/'bin'/name,base.BUILD)
        previous[name]=target.read_bytes()
        assert hashlib.sha256(previous[name]).hexdigest()==plan['files'][name]['before'],name
        assert base.digest(source)==plan['files'][name]['after'],name
    written=[]
    try:
        for name in NAMES:
            written.append(name);(base.GAME/name).write_bytes((base.BUILD/'bin'/name).read_bytes())
        for name in NAMES:assert base.digest(base.GAME/name)==plan['files'][name]['after'],name
        base.verify_resource(base.GAME/'freelancer.exe')
    except BaseException:
        for name in written:(base.GAME/name).write_bytes(previous[name])
        raise
    previous.clear();plan['build_cleanup_bytes']=base.cleanup()
    (OUT/'language_installed.json').write_text(json.dumps(plan,indent=2))
    print('Installed and hash-verified client + symbols; settings, renderer, dgVoodoo and shader cache unchanged; build copies cleaned')


if __name__=='__main__':
    apply() if '--apply' in sys.argv else prepare()
