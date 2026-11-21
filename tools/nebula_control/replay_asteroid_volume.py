"""Replay captured nebula constants against sparse object depth; no game launch."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage/physical_order/trace'
PROBE=OUT/'probe'
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

def main():
    PROBE.mkdir(parents=True,exist_ok=True)
    capture=OUT/'runtime.json'
    if not capture.exists():
        capture.write_bytes((ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_surface/runtime.json').read_bytes())
    rows=json.loads(capture.read_text())
    raw=lambda name:bytes.fromhex(next(x['raw'] for x in rows if x['name']==name))
    ray,composite=raw('GRaymarchConstants'),raw('GCompositeConstants')
    assert len(ray)==112*16 and len(composite)==27*16
    (PROBE/'constants.bin').write_bytes(ray+composite)
    c=struct.unpack('<108f',composite)
    width,height=round(.5/c[8]),round(.5/c[9]);lw,lh=round(c[4]),round(c[5])
    source=(ROOT/'tools/nebula_control/check_omega15_volume.cpp').read_text()
    source=source[:source.index(' double previous=1;')]+'\n#include "'+str(ROOT/'tools/nebula_control/asteroid_volume_replay_cases.inl').replace('\\','/')+'"\n}\n'
    source=source.replace('const unsigned W=1920,H=1080,LW=W/2,LH=H/2;',f'const unsigned W={width},H={height},LW={lw},LH={lh};')
    source=source.replace('float c[112][4]={},tone[4]={};','float c[112][4]={},capturedComposite[27][4]={};')
    source=source.replace('fread(tone,sizeof(tone),1,f)','fread(capturedComposite,sizeof(capturedComposite),1,f)')
    start=source.index(' if(quality==2)');end=source.index(' auto*api=',start)
    source=source[:start]+source[end:]
    start=source.index(' const float coverage=');end=source.index(' IDirect3DVolumeTexture9*volume=',start)
    source=source[:start]+source[end:]
    start=source.index('  else {float p[26]');end=source.index('  Check(d->DrawPrimitiveUP',start)
    source=source[:start]+'''  else {Check(d->SetPixelShaderConstantF(0,&capturedComposite[0][0],27));Check(d->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE));Check(d->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_SRCALPHA));}
'''+source[end:]
    texture=ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_surface/probe/textures/omega15.png'
    assert texture.exists()
    bind='''
 IDirect3DTexture9*puff=nullptr;Check(D3DXCreateTextureFromFileA(d,"PUFF_PATH",&puff));Check(d->SetTexture(2,puff));
 for(auto s:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER,D3DSAMP_MIPFILTER})Check(d->SetSamplerState(2,s,D3DTEXF_LINEAR));
 for(auto s:{D3DSAMP_ADDRESSU,D3DSAMP_ADDRESSV})Check(d->SetSamplerState(2,s,D3DTADDRESS_CLAMP));
'''.replace('PUFF_PATH',texture.as_posix())
    source=source.replace(' std::vector<unsigned long>noise;',bind+' std::vector<unsigned long>noise;')
    (PROBE/'replay.cpp').write_text(source)
    compiler,env=compiler_env()
    env['INCLUDE']=';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper())+';C:/DXSDK_Jun10/Include'
    env['PATH']=str(ROOT/'bin')+';D:/Games/FL_MOD/bin;'+env['PATH']
    env['TEMP']=env['TMP']=str(PROBE)
    command=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/utf-8','/DNOMINMAX',
             '/D_CRT_SECURE_NO_WARNINGS','/Isrc/RP9','/Iout/graphics_settings/nebula_asteroid_mesh/fog_surface/probe',
             str(PROBE/'replay.cpp'),'/Fo'+str(PROBE/'replay.obj'),'/Fe'+str(PROBE/'replay.exe'),
             '/link','d3d9.lib','user32.lib','C:/DXSDK_Jun10/Lib/x86/d3dx9.lib']
    for name,cmd in [('replay_build',command),('replay_result',[str(PROBE/'replay.exe'),str(PROBE/'constants.bin'),
            str(ROOT/'DATA_EXTRA/SHADERS')+'/',str(PROBE/'cache'),str(OUT/'replay'),'3'])]:
        with (OUT/(name+'.log')).open('wb') as f:
            result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        print((OUT/(name+'.log')).read_text(errors='replace')[-5000:],flush=True)
        result.check_returncode()

if __name__=='__main__':main()
