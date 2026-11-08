"""Build our isolated Feed-derived host with explicit per-frame status (private v1)."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
VC=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat')

def replace_once(text, before, after):
    if text.count(before)!=1:raise RuntimeError(f'Pinned host source changed: {before[:80]}')
    return text.replace(before,after)

def main():
    ref=ROOT/'out/base_neural/reference/DLSS5-Feeder-0.7.0'
    sdk=ROOT/'out/base_neural/reference/ngx'
    obj=ROOT/'out/base_neural/on/obj/host'
    out=ROOT/'out/base_neural/on/bin/neural/host64'
    obj.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    source=(ref/'host/dlss5-feed-host64.cpp').read_text()
    source=replace_once(source,'#include "../src/feed_ipc.h"','#include "feed_ipc.h"\n#pragma pack(push,1)\nstruct FrameAck { uint64_t frame; int32_t ok; };\n#pragma pack(pop)')
    source=replace_once(source,'hello.version > FEED_IPC_VERSION','hello.version != FEED_IPC_VERSION')
    source=replace_once(source,'    const bool gl_client = hello.client_kind == FEED_CLIENT_GL;',
        '    ULONG peer = 0;\n    if (!GetNamedPipeClientProcessId(pipe, &peer) || peer != hello.pid || hello.pid != game_pid || hello.client_kind != FEED_CLIENT_D3D11) return 1;\n    const bool gl_client = false;')
    source=replace_once(source,'h.width / 2, h.height, 1','h.width, h.height, 1')
    source=replace_once(source,'// Deliberately copy only the LEFT half: a split screen in the game is\n                    // unambiguous visual proof that the host\'s output reaches the screen.',
        '// Full-frame identity transport for automated pixel validation.')
    source=replace_once(source,'if (h.feature == nullptr && !transport_only) { h.fence_out->Signal(fm.n); continue; }',
        'if (h.feature == nullptr && !transport_only) break;')
    source=replace_once(source,'{ Log("[host] frame %llu: in-fence never arrived", (unsigned long long)fm.n); h.fence_out->Signal(fm.n); continue; }',
        '{ Log("[host] input fence timeout"); break; }')
    source=replace_once(source,'            PumpPresent();\n        }\n        else',
        '            FrameAck result = {fm.n, done ? 1 : 0};\n            DWORD written = 0;\n            if (!WriteFile(pipe, &result, sizeof(result), &written, nullptr) || written != sizeof(result)) break;\n            PumpPresent();\n        }\n        else')
    header=(ref/'src/feed_ipc.h').read_text().replace('0x35534C44u','0x4E424C46u').replace('FEED_IPC_VERSION 2u','FEED_IPC_VERSION 0x464C0001u').replace('dlss5-feed.%lu','fl-base-neural.%lu')
    (obj/'feed_ipc.h').write_text(header)
    (obj/'host.cpp').write_text('// Derived from DLSS5-Feeder v0.7.0, Copyright 2026 Jean-Laurent ROUZIES, MIT.\n'+source)
    q=lambda p:'"'+str(p)+'"'
    command='cl /nologo /std:c++20 /O2 /EHsc /W3 /MD /I'+q(sdk/'include')+' '+q(obj/'host.cpp')+' /link /OUT:'+q(out/'fl_base_neural_host.exe')+' '+q(sdk/'lib/Windows_x86_64/x64/nvsdk_ngx_d.lib')+' version.lib kernel32.lib user32.lib gdi32.lib advapi32.lib ole32.lib'
    batch=obj/'build.cmd'
    batch.write_text('@echo off\ncall '+q(VC)+' amd64 >nul\nif errorlevel 1 exit /b 1\ncd /d '+q(obj)+'\n'+command+'\nexit /b %errorlevel%\n')
    log=obj/'build.log'
    with log.open('wb') as stream:r=subprocess.run(['cmd','/d','/c',str(batch)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    if r.returncode:print(log.read_text(errors='replace')[-6000:])
    r.check_returncode();print('PASS x64 private-protocol host')

if __name__=='__main__':main()
