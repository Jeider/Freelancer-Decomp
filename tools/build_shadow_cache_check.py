from pathlib import Path

source=Path('src/RP9/RP9Ex.cpp').read_text()
rp=Path('src/RP9/RP9.cpp').read_text()
def function(text, marker):
    start=text.index(marker); begin=text.index('{',start); depth=1; end=begin+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}'); end+=1
    return text[start:end]
prefix=r'''
#define RP_DIRECT3D9
#include "RP9Ex.h"
#include "RP9DeviceCallCache.h"
#include <d3dx9.h>
#include <cmath>
#include <algorithm>
#include <cstdio>
#include <cassert>
#include <cstring>
const int kExFdumpNotice=0;
void ExLogf(int,const char*,int,const char*,...) {}
float ReadShadowSetting(const char*,float v,float,float) {return v;}
bool CompileStage(const std::string& source,const std::string& path,ID3DXInclude*,const std::string& entry,const char* profile,std::vector<unsigned char>* out)
{
 ID3DXBuffer *code=0,*errors=0;HRESULT hr;
 if(path.find("local_shadow.hlsl")!=std::string::npos)
  hr=D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/local_shadow.hlsl",0,0,entry.c_str(),profile,0,&code,&errors,0);
 else hr=D3DXCompileShader(source.c_str(),(UINT)source.size(),0,0,entry.c_str(),profile,0,&code,&errors,0);
 if(errors){puts((char*)errors->GetBufferPointer());errors->Release();}
 if(FAILED(hr))return false;
 out->assign((unsigned char*)code->GetBufferPointer(),(unsigned char*)code->GetBufferPointer()+code->GetBufferSize());code->Release();return true;
}
struct ShadowTest {
 FRp9ExState State={};FRp9ExState* Ex_=&State;IDirect3DDevice9* Device_=nullptr;
 FRp9RenderStateCache RenderStates_={};FRp9DeviceStateCaches DeviceStates_={};
 FRp9PipelineTransforms Transforms_={};FRp9StreamCache StreamCache_={};
 INT DeviceBaseVertex_=0;FRp9PipelineStateSlot PipelineStates_[kRp9PipelineStateCount]={};
 void FlushDrawState(IDirect3DDevice9*) {}
 void ExFlushSurfaceInstances() {}
 GENRESULT DACOM_API BeginLocalShadowFrame(const float*,const float*,const float*);
 GENRESULT DACOM_API BeginStaticShadowCache(unsigned long,unsigned long);
 GENRESULT DACOM_API BeginLocalShadowMap(unsigned long);
 GENRESULT DACOM_API EndLocalShadowMap();
 void ExShadowRelease();
};
'''
parts=[prefix,function(source,'FRp9ExState::FRp9ExState()'),function(rp,'void FRp9TransformCache::StoreAffine(')]
for name in ('BeginLocalShadowFrame','BeginStaticShadowCache','BeginLocalShadowMap','EndLocalShadowMap'):
    parts.append(function(source,'GENRESULT DACOM_API FDirectX9::'+name+'(').replace('FDirectX9::','ShadowTest::'))
parts.append(function(source,'void FDirectX9::ExShadowRelease(').replace('FDirectX9::','ShadowTest::'))
parts.append(r'''
void ck(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);ExitProcess(1);}}
struct V{float x,y,z,w,u,v;};
void draw(IDirect3DDevice9* d,IDirect3DPixelShader9* ps,float z,float width){
 V q[]={{-.5f,-.5f,z,1,0,0},{width-.5f,-.5f,z,1,1,0},{-.5f,1023.5f,z,1,0,1},{width-.5f,1023.5f,z,1,1,1}};
 d->SetVertexShader(0);d->SetPixelShader(ps);d->SetFVF(D3DFVF_XYZRHW|D3DFVF_TEX1);
 float c[]={z,z,z,z};d->SetPixelShaderConstantF(0,c,1);
 d->SetRenderState(D3DRS_ZENABLE,TRUE);d->SetRenderState(D3DRS_ZWRITEENABLE,TRUE);d->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
 d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);d->SetRenderState(D3DRS_ALPHATESTENABLE,FALSE);
 ck(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(V)));
}
void checkDepth(ShadowTest& t,float right){
 IDirect3DSurface9 *s=0,*r=0;ck(t.State.ShadowMaps[1]->GetSurfaceLevel(0,&s));
 ck(t.Device_->CreateOffscreenPlainSurface(1024,1024,D3DFMT_R32F,D3DPOOL_SYSTEMMEM,&r,0));
 ck(t.Device_->GetRenderTargetData(s,r));D3DLOCKED_RECT l;ck(r->LockRect(&l,0,D3DLOCK_READONLY));
 for(int y=0;y<1024;y++)for(int x=0;x<1024;x++){
  float z=((float*)((char*)l.pBits+y*l.Pitch))[x];assert(fabs(z-(x<512?.25f:right))<1.e-6f);
 }r->UnlockRect();r->Release();s->Release();
}
int main(){
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 HWND w=CreateWindowA("STATIC","shadow cache check",WS_POPUP,0,0,64,64,0,0,GetModuleHandle(0),0);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 ShadowTest t;ck(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_SOFTWARE_VERTEXPROCESSING,&pp,&t.Device_));
 auto& e=t.State;e.bShadowConfigRead=true;e.ShadowResolution=1024;e.ShadowFarRadius=1000;
 float view[]={1,0,0,0,1,0,0,0,-1,0,0,0},eye[]={10000,20000,30000},ray[]={.3f,.4f,.8660254f};
 ck(t.BeginLocalShadowFrame(view,eye,ray));ck(t.Device_->BeginScene());
 assert(t.BeginStaticShadowCache(10,20)==0);assert(e.bShadowStaticDrawing);
 std::vector<unsigned char> code;assert(CompileStage("float4 C:register(c0); struct O {float4 C:COLOR0;float D:DEPTH;}; O main(){O o;o.C=C;o.D=C.x;return o;}","test",0,"main","ps_3_0",&code));
 IDirect3DPixelShader9* paint=0;ck(t.Device_->CreatePixelShader((DWORD*)code.data(),&paint));
 draw(t.Device_,paint,.25f,512);ck(t.EndLocalShadowMap());assert(e.bShadowStaticValid);
 ck(t.BeginLocalShadowMap(1));D3DVIEWPORT9 vp;ck(t.Device_->GetViewport(&vp));assert(vp.Width==1024);
 draw(t.Device_,paint,.75f,1024);ck(t.EndLocalShadowMap());ck(t.Device_->EndScene());checkDepth(t,.75f);
 puts("PASS: cached static depth occludes live geometry behind it; live shadow appears in open region");
 D3DXMATRIX saved;memcpy(&saved,e.ShadowMatrices[1],64);
 eye[0]+=10;ck(t.BeginLocalShadowFrame(view,eye,ray));
 D3DXVECTOR3 world(10050,20020,29990),before(world.x-10000,world.y-20000,world.z-30000),after(world.x-eye[0],world.y-eye[1],world.z-eye[2]),a,b;
 D3DXVec3TransformCoord(&a,&before,&saved);D3DXVec3TransformCoord(&b,&after,(D3DXMATRIX*)e.ShadowMatrices[1]);
 assert(D3DXVec3Length(&(a-=b))<1.e-5f);
 D3DXVECTOR3 reference;D3DXVec3TransformCoord(&reference,&before,&saved);
 view[0]=.8f;view[2]=.6f;view[6]=.6f;view[8]=-.8f;
 ck(t.BeginLocalShadowFrame(view,eye,ray));D3DXVECTOR3 turned;
 D3DXVec3TransformNormal(&turned,&after,(D3DXMATRIX*)e.ShadowCameraRotation);
 D3DXVec3TransformCoord(&b,&turned,(D3DXMATRIX*)e.ShadowMatrices[1]);
 assert(D3DXVec3Length(&(reference-=b))<1.e-5f);
 assert(t.BeginStaticShadowCache(10,20)==1);assert(!e.bShadowDrawing);
 ck(t.Device_->BeginScene());ck(t.BeginLocalShadowMap(1));ck(t.EndLocalShadowMap());ck(t.Device_->EndScene());checkDepth(t,1);
 puts("PASS: camera translation/rotation preserve world-space cache; removed live shadow leaves no ghost");
 assert(t.BeginStaticShadowCache(11,20)==0);ck(t.EndLocalShadowMap());assert(e.ShadowStaticBuilds==2);
 ck(t.BeginLocalShadowFrame(view,eye,ray));assert(t.BeginStaticShadowCache(11,20)==1);
 eye[0]+=100;ck(t.BeginLocalShadowFrame(view,eye,ray));assert(!e.bShadowStaticValid);
 assert(t.BeginStaticShadowCache(11,20)==0);ck(t.EndLocalShadowMap());
 ray[0]+=.01f;ck(t.BeginLocalShadowFrame(view,eye,ray));assert(!e.bShadowStaticValid);
 assert(t.BeginStaticShadowCache(11,20)==0);ck(t.EndLocalShadowMap());
 e.ShadowStaticBuiltAt=GetTickCount()-1001;ck(t.BeginLocalShadowFrame(view,eye,ray));assert(!e.bShadowStaticValid);
 e.bShadowStaticCache=false;assert(t.BeginStaticShadowCache(11,20)<0);
 puts("PASS: geometry-key, region, sunlight and age invalidation; cache-off fallback");
 t.ExShadowRelease();assert(!e.ShadowStaticMap && !e.ShadowRestorePs && !e.bShadowStaticValid);
 paint->Release();t.Device_->Release();api->Release();DestroyWindow(w);
 puts("PASS: cache resources released");
}
''')
Path('src/obj').mkdir(parents=True, exist_ok=True)
Path('src/obj/shadow_cache_check.cpp').write_text('\n'.join(parts))
