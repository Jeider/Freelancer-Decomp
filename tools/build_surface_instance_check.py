from pathlib import Path
import runpy

helper=runpy.run_path('tools/build_shadow_cache_check.py')
function=helper['function'];source=helper['source'];rp=helper['rp']
prefix=helper['prefix'].replace('ShadowTest','InstanceTest').replace('void ExFlushSurfaceInstances() {}',
'''void ExFlushSurfaceInstances();
 void ExReleaseSurfaceInstances();void ExNoteDraw(unsigned long);
 bool ExQueueSurfaceInstance(unsigned long,unsigned int,unsigned int,unsigned int,unsigned int);
 GENRESULT DACOM_API SetLocalShadowReceiver(unsigned long);
 FRp9Ib ScratchIb_={};''')
parts=[prefix,function(source,'FRp9ExState::FRp9ExState()'),function(rp,'unsigned long FRp9RenderStateCache::GetPending(')]
for marker in ('bool FDirectX9::ExQueueSurfaceInstance(', 'void FDirectX9::ExFlushSurfaceInstances(',
               'void FDirectX9::ExReleaseSurfaceInstances(', 'void FDirectX9::ExNoteDraw(',
               'GENRESULT DACOM_API FDirectX9::SetLocalShadowReceiver('):
    parts.append(function(source,marker).replace('FDirectX9::','InstanceTest::'))
parts.append(r'''
void ck(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);ExitProcess(1);}}
std::vector<DWORD> readPixels(IDirect3DDevice9* d){
 IDirect3DSurface9 *s=0,*r=0;ck(d->GetRenderTarget(0,&s));
 ck(d->CreateOffscreenPlainSurface(128,128,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&r,0));
 ck(d->GetRenderTargetData(s,r));D3DLOCKED_RECT l;ck(r->LockRect(&l,0,D3DLOCK_READONLY));std::vector<DWORD> v(128*128);
 for(int y=0;y<128;y++)memcpy(v.data()+y*128,(char*)l.pBits+y*l.Pitch,128*4);
 r->UnlockRect();r->Release();s->Release();return v;
}
int main(){
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 HWND w=CreateWindowA("STATIC","instancing check",WS_POPUP,0,0,128,128,0,0,GetModuleHandle(0),0);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=pp.BackBufferHeight=128;pp.BackBufferFormat=D3DFMT_A8R8G8B8;pp.EnableAutoDepthStencil=1;pp.AutoDepthStencilFormat=D3DFMT_D24X8;
 InstanceTest t;ck(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&t.Device_));
 auto* d=t.Device_;auto& e=t.State;auto& calls=Rp9DeviceCalls();
 // This fixture explicitly exercises the experimental opt-in path.
 e.bInstanceConfigRead=true;e.bSurfaceInstancing=true;
 std::vector<unsigned char> code;std::string vsSource;
 FILE* file=fopen("DATA_EXTRA/SHADERS/surface_material.hlsl","rb");assert(file);char buf[4096];size_t n;while((n=fread(buf,1,sizeof(buf),file)))vsSource.append(buf,n);fclose(file);
 assert(CompileStage(vsSource,"surface",0,"VSMain","vs_3_0",&code));IDirect3DVertexShader9* vs=0;ck(d->CreateVertexShader((DWORD*)code.data(),&vs));
 assert(CompileStage("sampler2D T:register(s0);float4 C:register(c0);float4 main(float3 p:TEXCOORD0,float3 n:TEXCOORD1,float2 uv:TEXCOORD2):COLOR0{return float4(uv.x,.3+.4*abs(normalize(n).x),uv.y,1)*C*tex2D(T,uv);}","test",0,"main","ps_3_0",&code));
 IDirect3DPixelShader9* ps=0;ck(d->CreatePixelShader((DWORD*)code.data(),&ps));
 struct V{float x,y,z,nx,ny,nz,u,v;};
 V vertices[8]={};vertices[4]={-.19f,-.19f,0,.7071067f,0,.7071067f,0,1};vertices[5]={.19f,-.19f,0,.7071067f,0,.7071067f,1,1};vertices[6]={-.19f,.19f,0,.7071067f,0,.7071067f,0,0};vertices[7]={.19f,.19f,0,.7071067f,0,.7071067f,1,0};
 WORD indices[]={0,0,0,0,0,0,0,1,2,2,1,3};FRp9Vb vb={};FRp9Ib ib={};vb.Fvf=0x112;vb.Count=8;vb.Flags=D3DUSAGE_WRITEONLY;ib.Flags=D3DUSAGE_WRITEONLY;
 ck(d->CreateVertexBuffer(sizeof(vertices),vb.Flags,vb.Fvf,D3DPOOL_DEFAULT,&vb.Gpu,0));void* ptr=0;ck(vb.Gpu->Lock(0,0,&ptr,0));memcpy(ptr,vertices,sizeof(vertices));vb.Gpu->Unlock();
 ck(d->CreateIndexBuffer(sizeof(indices),ib.Flags,D3DFMT_INDEX16,D3DPOOL_DEFAULT,&ib.Gpu,0));ck(ib.Gpu->Lock(0,0,&ptr,0));memcpy(ptr,indices,sizeof(indices));ib.Gpu->Unlock();
 t.StreamCache_.VertexBuffer=&vb;t.StreamCache_.IndexBuffer=&ib;t.DeviceBaseVertex_=4;
 t.RenderStates_.Entries[D3DRS_ZENABLE].Pending=1;t.RenderStates_.Entries[D3DRS_ZWRITEENABLE].Pending=1;
 e.bInstanceScope=true;e.bSurfaceActive=true;
 IDirect3DTexture9* tex[2]={};for(int i=0;i<2;i++){ck(d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&tex[i],0));D3DLOCKED_RECT l;ck(tex[i]->LockRect(0,&l,0,0));*(DWORD*)l.pBits=i?0xff80a0ff:0xffffffff;tex[i]->UnlockRect(0);}
 std::vector<DWORD> reference;std::uint64_t instancedDraws=0;
 for(int mode=0;mode<3;mode++){
  e.bInstanceFailed=false;calls.ResetCounters();ck(d->Clear(0,0,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff000000,1,0));ck(d->BeginScene());
  for(int i=0;i<24;i++){
   ck(t.SetLocalShadowReceiver(5));
   if(i==12){if(mode==2)e.bInstanceFailed=true;t.ExFlushSurfaceInstances();if(mode==2)e.bInstanceFailed=false;}
   ck(d->SetStreamSource(0,vb.Gpu,0,sizeof(V)));ck(d->SetIndices(ib.Gpu));ck(d->SetFVF(vb.Fvf));
   ck(Rp9SetVertexShader(d,vs));ck(Rp9SetPixelShader(d,ps));ck(Rp9SetTexture(d,0,tex[i%2]));
   ck(Rp9SetSamplerState(d,0,D3DSAMP_MINFILTER,D3DTEXF_POINT));ck(Rp9SetSamplerState(d,0,D3DSAMP_MAGFILTER,D3DTEXF_POINT));
   for(auto state:{D3DRS_ZENABLE,D3DRS_ZWRITEENABLE})ck(Rp9SetRenderState(d,state,1));
   ck(Rp9SetRenderState(d,D3DRS_ZFUNC,D3DCMP_LESSEQUAL));ck(Rp9SetRenderState(d,D3DRS_CULLMODE,D3DCULL_NONE));ck(Rp9SetRenderState(d,D3DRS_ALPHABLENDENABLE,FALSE));
   float v[68]={},p[95*4]={};D3DXMATRIX m;D3DXMatrixIdentity(&m);memcpy(v,&m,64);memcpy(v+16,&m,64);memcpy(v+32,&m,64);memcpy(v+48,&m,64);
   float scale=(i%3==0)?.7f:1.0f;v[0]=scale;v[12]=-.83f+(i%6)*.33f;v[13]=-.75f+(i/6)*.5f;v[14]=.5f+.01f*(i%4);v[32]=1/scale;
   p[0]=1;p[1]=(i%2)?.7f:1;p[2]=1;p[3]=1;
   ck(Rp9SetVertexConstants(d,0,v,17));ck(Rp9SetPixelConstants(d,0,p,95));
   bool queued=mode && t.ExQueueSurfaceInstance(D3DPT_TRIANGLELIST,0,4,6,2);
   if(!queued){ck(d->DrawIndexedPrimitive(D3DPT_TRIANGLELIST,4,0,4,6,2));t.ExNoteDraw(2);}
  }
  if(mode==2)e.bInstanceFailed=true;t.ExFlushSurfaceInstances();ck(d->EndScene());auto pixels=readPixels(d);
  if(!mode){reference=pixels;assert(calls.MainDraws==24);}else assert(pixels==reference);
  if(mode==1){instancedDraws=calls.InstancedDraws;printf("instanced draws=%llu, submitted draws=%llu, instances=%llu\n",calls.InstancedDraws,calls.MainDraws,calls.Instances);assert(instancedDraws>0&&calls.MainDraws<24);}
  UINT freq=0;ck(d->GetStreamSourceFreq(0,&freq));assert(freq==1);ck(d->GetStreamSourceFreq(1,&freq));assert(freq==1);
 }
 puts("PASS: real hardware instancing is pixel-identical to ordinary draws; UVs, normals, transforms, materials, nonzero index/base ranges and fallback preserved");
 assert(instancedDraws>0);t.ExReleaseSurfaceInstances();assert(!e.SurfaceInstanceVs&&!e.SurfaceInstanceVb&&e.SurfaceInstanceDecls.empty());
 ck(t.SetLocalShadowReceiver(9));assert(e.SurfaceDistanceTier==1&&e.bShadowReceiver&&!e.bInstanceScope);
 ck(t.SetLocalShadowReceiver(17));assert(e.SurfaceDistanceTier==2&&e.bShadowReceiver);
 ck(t.SetLocalShadowReceiver(3));assert(e.SurfaceDistanceTier==0&&e.bShadowReceiverIsShip);
 ck(t.SetLocalShadowReceiver(4));assert(e.bInstanceScope&&!e.bShadowReceiver&&e.SurfaceDistanceTier==0);
 ck(t.SetLocalShadowReceiver(0));assert(!e.bInstanceScope&&!e.bShadowReceiver);
 puts("PASS: stream frequencies restored and all instance resources released");
 tex[0]->Release();tex[1]->Release();vb.Gpu->Release();ib.Gpu->Release();vs->Release();ps->Release();d->Release();api->Release();DestroyWindow(w);
}
''')
Path('src/obj/surface_instance_check.cpp').write_text('\n'.join(parts))
