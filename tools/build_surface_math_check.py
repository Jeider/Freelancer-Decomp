from pathlib import Path
import subprocess,runpy
h=runpy.run_path('tools/build_shadow_cache_check.py');s=h['source'];f=h['function']
start=s.index('bool FDirectX9::ExSurfaceBegin()')
normal=s[s.index('    D3DXMATRIX M, Inverse, Normal;',start):s.index('    const float* EnvMatrix',start)]
packing=s[s.index('    float LightView[16]',start):s.index('    ExSaveStage(1,',start)].replace('Transforms_.View.Values','View')
old=subprocess.check_output(['git','show','HEAD:src/RP9/RP9Ex.cpp']).decode()
begin=old.index('bool FDirectX9::ExSurfaceBegin()');begin=old.index('    for (unsigned I = 0; I < Count; ++I)',begin)
legacy=old[begin:old.index('    ExSaveStage(1,',begin)].replace('Transforms_.View.Values','View')
header=h['prefix'][:h['prefix'].index('struct ShadowTest')]
set_code='D3DXMATRIX M;auto Set=[&](unsigned R,float X,float Y,float Z,float W){float* P=Ps+R*4;P[0]=X;P[1]=Y;P[2]=Z;P[3]=W;};\n'
out=[header,f(s,'FRp9ExState::FRp9ExState()'),
     'bool normal(FRp9ExState* Ex,const float* Input,float* Output){float Vs[68]={};memcpy(Vs,Input,64);'+normal+'memcpy(Output,Vs+32,64);return true;}',
     'void pack(FRp9ExState* Ex,const D3DLIGHT9* Lights,unsigned Count,const float* View,const D3DMATERIAL9& Mat,float* Ps){'+set_code+packing+'}',
     'void reference(const D3DLIGHT9* Lights,unsigned Count,const float* View,const D3DMATERIAL9& Mat,float* Ps){'+set_code+legacy+'}']
out.append(r'''
int main(){
 FRp9ExState e;D3DXMATRIX m,r,scale,inverse,expected;float result[16];
 for(int i=0;i<100;i++){
  D3DXMatrixRotationYawPitchRoll(&r,i*.13f,i*.07f,i*.03f);
  if(i%2)D3DXMatrixScaling(&scale,.2f+i*.017f,.7f+i*.013f,1.3f);else D3DXMatrixIdentity(&scale);
  D3DXMatrixMultiply(&m,&scale,&r);m._41=100000+i;m._42=-20000;m._43=35000;
  assert(normal(&e,(float*)&m,result));D3DXMatrixInverse(&inverse,0,&m);D3DXMatrixTranspose(&expected,&inverse);
  for(int a=0;a<3;a++)for(int b=0;b<3;b++)assert(fabs(result[a*4+b]-expected.m[a][b])<1.e-5f);
  float repeated[16];assert(normal(&e,(float*)&m,repeated));assert(!memcmp(result,repeated,64));
 }
 puts("PASS: rigid and cached normals match inverse-transpose reference; nonuniform scale/rotation/large translations preserved");
 D3DLIGHT9 lights[8]={};D3DMATERIAL9 mat={};mat.Ambient={.3f,.4f,.5f,1};
 for(int i=0;i<8;i++){
  auto& l=lights[i];l.Type=(D3DLIGHTTYPE)(1+i%3);l.Position={float(i*12),float(i),-50};l.Direction={.1f,.2f,.3f};
  l.Diffuse={.2f,.3f,.4f,1};l.Ambient={.01f*i,.02f*i,.03f*i,1};l.Specular=i%2?D3DCOLORVALUE{.1f,.4f,.3f,1}:D3DCOLORVALUE{};
  l.Range=200;l.Attenuation0=1;l.Attenuation1=.1f;l.Attenuation2=.01f;l.Falloff=2;l.Theta=.6f;l.Phi=.9f;
 }
 for(int i=0;i<20;i++){
  D3DXMatrixRotationY(&r,(i/2)*.13f);r._41=(i/2)*100;unsigned count=(i/2)%9;
  if(i==10)lights[0].Diffuse.r=.7f;
  float actual[95*4]={},ref[95*4]={};pack(&e,lights,count,(float*)&r,mat,actual);reference(lights,count,(float*)&r,mat,ref);
  for(unsigned j=0;j<count;j++)if(lights[j].Type==D3DLIGHT_DIRECTIONAL)ref[(12+j*5)*4]=ref[(12+j*5)*4+1]=ref[(12+j*5)*4+2]=0;
  for(int j=0;j<95*4;j++)assert(fabs(actual[j]-ref[j])<1.e-6f);
 }
 lights[0].Type=D3DLIGHT_DIRECTIONAL;float ps[95*4]={};pack(&e,lights,1,(float*)&r,mat,ps);
 assert(e.SurfaceLastLightView[12]==0&&e.SurfaceLastLightView[13]==0&&e.SurfaceLastLightView[14]==0);
 puts("PASS: cached light packing preserves original active fields; canonical directional positions, light/view/count invalidation");
}
''')
Path('src/obj/surface_math_check.cpp').write_text('\n'.join(out))
