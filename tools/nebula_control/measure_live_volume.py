"""Replay a read-only live constants snapshot on an isolated D3D9 device.

Synthetic depth, actual shader/constants/native cloud art; not an in-game GPU timer.
Does not change the game, settings or live shader cache.
"""
from pathlib import Path
import hashlib,json,os,struct,subprocess
from build_asf_hq import compiler_env
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/lod/live';PROBE=OUT/'volume_probe'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    PROBE.mkdir(parents=True,exist_ok=True)
    capture=OUT/'render_state.json';rows=json.loads(capture.read_text())
    raw=lambda n:bytes.fromhex(next(x['raw'] for x in rows if x['name']==n))
    ray,composite=raw('GRaymarchConstants'),raw('GCompositeConstants');assert len(ray)==1792 and len(composite)==432
    (PROBE/'constants.bin').write_bytes(ray+composite);c=struct.unpack('<108f',composite)
    width,height=round(.5/c[8]),round(.5/c[9]);lw,lh=round(c[4]),round(c[5]);assert 1<=lw<=width<=8192 and 1<=lh<=height<=8192
    source=(ROOT/'tools/nebula_control/check_omega15_volume.cpp').read_text()
    source=source[:source.index(' double previous=1;')]
    source=source.replace('const unsigned W=1920,H=1080,LW=W/2,LH=H/2;',f'const unsigned W={width},H={height},LW={lw},LH={lh};')
    source=source.replace('float c[112][4]={},tone[4]={};','float c[112][4]={},capturedComposite[27][4]={};')
    source=source.replace('fread(tone,sizeof(tone),1,f)','fread(capturedComposite,sizeof(capturedComposite),1,f)')
    start=source.index(' if(quality==2)');end=source.index(' auto*api=',start);source=source[:start]+source[end:]
    start=source.index(' const float coverage=');end=source.index(' IDirect3DVolumeTexture9*volume=',start);source=source[:start]+source[end:]
    start=source.index('  else {float p[26]');end=source.index('  Check(d->DrawPrimitiveUP',start)
    source=source[:start]+'''  else {Check(d->SetPixelShaderConstantF(0,&capturedComposite[0][0],27));Check(d->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE));Check(d->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_SRCALPHA));}
'''+source[end:]
    texture=ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_surface/probe/textures/omega15.png';assert texture.exists()
    bind=''' IDirect3DTexture9* puff=nullptr;Check(D3DXCreateTextureFromFileA(d,"TEXTURE",&puff));Check(d->SetTexture(2,puff));
 for(auto s:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER,D3DSAMP_MIPFILTER})Check(d->SetSamplerState(2,s,D3DTEXF_LINEAR));
 for(auto s:{D3DSAMP_ADDRESSU,D3DSAMP_ADDRESSV})Check(d->SetSamplerState(2,s,D3DTADDRESS_CLAMP));
'''.replace('TEXTURE',texture.as_posix())
    source=source.replace(' std::vector<unsigned long>noise;',bind+' std::vector<unsigned long>noise;')
    source+='''
 IDirect3DQuery9 *start=nullptr,*end=nullptr,*freq=nullptr,*disjoint=nullptr;
 Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&start));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&end));
 Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&freq));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&disjoint));
 printf("Live constants: %ux%u output, %ux%u volume, %.0f steps; synthetic depth, no in-game timer\\n",W,H,LW,LH,c[10][0]);
 for(float distance:{1500.f,6000.f,100000.f}){
  setDepth(distance,false);std::vector<double> times[3];
  for(int frame=0;frame<48;++frame)for(int step=0;step<3;++step){int mode=(frame+step)%3;
   Check(d->BeginScene());Check(disjoint->Issue(D3DISSUE_BEGIN));Check(start->Issue(D3DISSUE_END));
   if(mode!=1)pass(true);if(mode!=0)pass(false);
   Check(end->Issue(D3DISSUE_END));Check(disjoint->Issue(D3DISSUE_END));Check(freq->Issue(D3DISSUE_END));Check(d->EndScene());
   UINT64 a,b,hz;BOOL bad;Query(end,&b,8);Query(start,&a,8);Query(freq,&hz,8);Query(disjoint,&bad,4);
   if(frame>=8&&!bad&&hz)times[mode].push_back(double(b-a)*1000/hz);
  }
  for(int mode=0;mode<3;++mode){auto& t=times[mode];Require(!t.empty(),"GPU timings");std::sort(t.begin(),t.end());
   printf("Depth %.0f mode %d (0=march,1=composite,2=both): median %.4f ms p95 %.4f ms\\n",distance,mode,t[t.size()/2],t[(t.size()-1)*95/100]);}
 }
 return 0;
}
'''
    (PROBE/'volume.cpp').write_text(source)
    prod=(ROOT/'src/freelancer/Client/nebula_volume.cpp').read_text(encoding='utf-8-sig')
    noise=prod[prod.index('    unsigned int Hash(unsigned int X)'):prod.index('    // Coverage (the fraction')]
    (PROBE/'nebula_noise_fixture.h').write_text('const unsigned long kNoiseSize=64;\nfloat Clamp(float x,float a,float b){return std::max(a,std::min(b,x));}\n'+noise)
    compiler,env=compiler_env();env['INCLUDE']=';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper())+';C:/DXSDK_Jun10/Include'
    env['PATH']=str(ROOT/'bin')+';D:/Games/FL_MOD/bin;'+env['PATH'];env['TEMP']=env['TMP']=str(PROBE)
    cmd=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/utf-8','/DNOMINMAX','/D_CRT_SECURE_NO_WARNINGS',
         '/Isrc/RP9','/I'+str(PROBE),str(PROBE/'volume.cpp'),'/Fo'+str(PROBE/'volume.obj'),'/Fe'+str(PROBE/'volume.exe'),
         '/link','d3d9.lib','user32.lib','C:/DXSDK_Jun10/Lib/x86/d3dx9.lib']
    shaders=['nebula_volume.hlsl','nebula_volume.hlsli','nebula_composite.hlsl','common.hlsli']
    hashes={n:digest(ROOT/'DATA_EXTRA/SHADERS'/n) for n in shaders}
    for n,h in hashes.items():assert digest(Path('D:/Games/FL_MOD/DATA_EXTRA/SHADERS')/n)==h,n
    for name,args in [('volume_build',cmd),('volume_result',[str(PROBE/'volume.exe'),str(PROBE/'constants.bin'),str(ROOT/'DATA_EXTRA/SHADERS')+'/',str(PROBE/'cache'),str(OUT/'unused.png'),'3'])]:
        with (OUT/(name+'.log')).open('wb') as stream:r=subprocess.run(args,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        print((OUT/(name+'.log')).read_text(errors='replace')[-6000:]);r.check_returncode()
    (OUT/'volume_measurement.json').write_text(json.dumps({'capture_sha256':digest(capture),'shaders':hashes,'resolution':[width,height,lw,lh],
        'scope':'Isolated replay, synthetic depth planes; live game can compete for GPU. No in-game attribution or whole-frame timing.','game_launched':False},indent=2))
    for p in PROBE.rglob('*'):
        assert p.resolve().is_relative_to(PROBE.resolve()) and not p.is_junction() and not p.is_symlink()
        if p.is_file() and p.suffix.lower() in ('.exe','.obj','.pdb','.ilk','.bin'):
            p.unlink()
if __name__=='__main__':main()
