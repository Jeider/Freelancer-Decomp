"""Probe real RP9 depth selection and sampling through native and installed D3D9; no game launch."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/shader_startup/depth'
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

POLICY_STUB='''
#include <set>
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
#include "ship_warp_state.h"
const D3DFORMAT kIntzFormat=D3DFORMAT(MAKEFOURCC('I','N','T','Z'));
struct FakeD3D {
 bool intz=true,match24=true;std::set<D3DFORMAT> formats={D3DFMT_D16,D3DFMT_D32,D3DFMT_D24S8,D3DFMT_D24X8,D3DFMT_D24X4S4};
 HRESULT CheckDeviceFormat(UINT,D3DDEVTYPE,D3DFORMAT,DWORD,D3DRESOURCETYPE type,D3DFORMAT f){return (type==D3DRTYPE_TEXTURE?intz:formats.count(f)!=0)?S_OK:E_FAIL;}
 HRESULT CheckDepthStencilMatch(UINT,D3DDEVTYPE,D3DFORMAT,D3DFORMAT,D3DFORMAT f){return match24||f==D3DFMT_D32||f==D3DFMT_D16?S_OK:E_FAIL;}
};
struct FDirectX9 {FakeD3D* D3d_=nullptr;UINT AdapterIndex_=0;D3DDEVTYPE DeviceType_=D3DDEVTYPE_HAL;
D3DFORMAT PickDepthFormat(D3DFORMAT,D3DFORMAT,int*,int*);bool ExWantsIntzDepth(D3DFORMAT,D3DFORMAT);};
struct FTrail {std::string Name;};
struct FState {void const* Jump=nullptr;std::string Nose;std::vector<FTrail> Trails;};
'''
POLICY_TEST='''
int main(){
 FakeD3D api;FDirectX9 pipe;pipe.D3d_=&api;
 auto pick=[&](int z,int s){return pipe.PickDepthFormat(D3DFMT_X8R8G8B8,D3DFMT_A8R8G8B8,&z,&s);};
 assert(pick(32,0)==D3DFMT_D24X8);assert(pick(32,8)==D3DFMT_D24S8);assert(pick(24,4)==D3DFMT_D24X4S4);
 assert(pick(16,0)==D3DFMT_D16);api.intz=false;assert(pick(32,0)==D3DFMT_D32);
 api.intz=true;api.match24=false;assert(pick(32,0)==D3DFMT_D32);
 api.match24=true;api.formats={D3DFMT_D16,D3DFMT_D32};assert(pick(32,0)==D3DFMT_D32);
 api.formats.clear();assert(pick(32,0)==D3DFMT_UNKNOWN);
 puts("PASS production depth selection: INTZ preferred, stencil respected, 16-bit and unsupported-device fallbacks retained");
 FState lane,jump;jump.Jump=&jump;
 for(char const* name:{"HpHeadLight","HpContrail01","HpContail07","hpcontrail42","HPCONTRAIL01","HpGun01"}){Collect(name,&lane);Collect(name,&jump);}
 assert(lane.Trails.size()==3&&jump.Trails.empty());assert(lane.Nose=="HpHeadLight"&&jump.Nose=="HpHeadLight");
 puts("PASS production hardpoint collection: lane contrails retained, hyperjump contrails removed, bow anchor retained");
}
'''

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rp=(ROOT/'src/RP9/RP9.cpp').read_text()
    ex=(ROOT/'src/RP9/RP9Ex.cpp').read_text()
    table=rp[rp.index('    struct FZFormatRow'):rp.index('    // FUN_06d15b0d')]
    pick=rp[rp.index('D3DFORMAT FDirectX9::PickDepthFormat('):rp.index('// Keep format-specific capability gates')]
    wants=ex[ex.index('bool FDirectX9::ExWantsIntzDepth('):ex.index('HRESULT FDirectX9::ExCreateDeviceResources(')]
    ship=(ROOT/'src/freelancer/Client/ship_warp_visual.cpp').read_text()
    collect=ship[ship.index('void __cdecl Collect('):ship.index('bool Init(')]
    stub='''#include <initializer_list>
const D3DFORMAT kIntzFormat=D3DFORMAT(MAKEFOURCC('I','N','T','Z'));
struct FDirectX9 {IDirect3D9* D3d_=nullptr;UINT AdapterIndex_=0;D3DDEVTYPE DeviceType_=D3DDEVTYPE_HAL;
D3DFORMAT PickDepthFormat(D3DFORMAT,D3DFORMAT,int*,int*);bool ExWantsIntzDepth(D3DFORMAT,D3DFORMAT);};
'''
    (OUT/'depth_selection.inc').write_text(stub+table+pick+wants)
    compiler,env=compiler_env();dx=Path('C:/DXSDK_Jun10')
    env['INCLUDE']+=';'+str(dx/'Include')
    (OUT/'policy.cpp').write_text('#define NOMINMAX\n#include <windows.h>\n#include <d3d9.h>\n#include <cstdio>\n'+POLICY_STUB+table+pick+wants+collect+POLICY_TEST)
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/O2','/MT','/EHsc','/I'+str(ROOT/'src/freelancer/Client'),'policy.cpp','/Fepolicy.exe'],cwd=OUT,env=env,check=True)
    result=subprocess.check_output([str(OUT/'policy.exe')],cwd=OUT,env=env,text=True)
    (OUT/'policy.log').write_text(result);print(result,flush=True)
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/O2','/MT','/EHsc','/I'+str(OUT),str(ROOT/'tools/shader_startup/check_depth_device.cpp'),'/Feprobe.exe','/link',str(dx/'Lib/x86/d3dx9.lib'),'user32.lib'],cwd=OUT,env=env,check=True)
    for name,path in [('native','C:/Windows/SysWOW64/d3d9.dll'),('installed','D:/Games/FL_MOD/bin/D3D9.dll')]:
        log=OUT/(name+'.log');before=OUT/(name+'.before.log')
        if log.exists() and not before.exists():before.write_text(log.read_text())
        r=subprocess.run([str(OUT/'probe.exe'),path],cwd=OUT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        log.write_text(r.stdout);print(r.stdout,flush=True);r.check_returncode()
    paths=[ROOT/p for p in ('src/RP9/RP9.cpp','src/RP9/RP9Ex.cpp','src/freelancer/Client/ship_warp_visual.cpp',
                           'tools/shader_startup/check_depth_device.cpp','tools/shader_startup/check_depth_device.py')]
    paths.append(Path('D:/Games/FL_MOD/bin/D3D9.dll'))
    (OUT/'verified.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))

if __name__=='__main__':main()
