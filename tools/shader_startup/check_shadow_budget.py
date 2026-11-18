"""Test a larger dgVoodoo VRAM budget in an isolated folder; do not change game settings."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/shader_startup/shadows'
GAME=Path('D:/Games/FL_MOD/bin')
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    original=(GAME/'dgVoodoo.conf').read_bytes()
    # Keep encoding/newlines and every other option byte-for-byte.
    proposed,count=re.subn(rb'(?m)^(VRAM\s*=\s*)256(?=\s*(?:;[^\r\n]*)?\r?$)',rb'\g<1>4096',original)
    assert count==1,'Unexpected active VRAM setting'
    (OUT/'dgVoodoo.proposed.conf').write_bytes(proposed)
    shutil.copy2(GAME/'D3D9.dll',OUT/'D3D9.dll')
    compiler,env=compiler_env();env['INCLUDE']+=';C:/DXSDK_Jun10/Include'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/O2','/MT','/EHsc',str(ROOT/'tools/shader_startup/check_shadow_budget.cpp'),'/Feprobe.exe','/link','dxgi.lib','user32.lib'],cwd=OUT,env=env,check=True)
    for label,config in [('before',original),('after',proposed)]:
        (OUT/'dgVoodoo.conf').write_bytes(config)
        result=subprocess.run([str(OUT/'probe.exe')],cwd=OUT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        (OUT/(label+'.log')).write_text(result.stdout);print(label+'\n'+result.stdout,flush=True);result.check_returncode()
        assert 'dgVoodoo' in result.stdout
        if label=='after':assert 'RESULT near=8192 far=4096 static=1 full=1' in result.stdout
        else:assert 'full=0' in result.stdout
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT/'verified.json').write_text(json.dumps(dict(before=hashlib.sha256(original).hexdigest(),after=hashlib.sha256(proposed).hexdigest(),
        provider=digest(GAME/'D3D9.dll'),sources={str(p):digest(p) for p in (Path(__file__),ROOT/'tools/shader_startup/check_shadow_budget.cpp')},
        change='dgVoodoo DirectX VRAM: 256 MiB -> 4096 MiB; all other config bytes unchanged'),indent=2))

if __name__=='__main__':main()
