// Run the production motion shader on smooth, spatially varying subpixel motion.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d11.h>
#include <d3dcompiler.h>
#include <wrl/client.h>
#include <vector>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include "shaders.h"
using Microsoft::WRL::ComPtr;
void Check(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);exit(1);}}
int main(){
 constexpr unsigned W=127,H=95; // Also verify partial 4x4 groups at the edges.
 ComPtr<ID3D11Device> d;ComPtr<ID3D11DeviceContext> c;D3D_FEATURE_LEVEL level;
 Check(D3D11CreateDevice(nullptr,D3D_DRIVER_TYPE_HARDWARE,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&d,&level,&c));
 ComPtr<ID3DBlob> blob,error;
 HRESULT hr=D3DCompile(BaseNeuralShaders,sizeof(BaseNeuralShaders)-1,"flow",nullptr,nullptr,"Flow","cs_5_0",D3DCOMPILE_OPTIMIZATION_LEVEL3,0,&blob,&error);
 if(FAILED(hr)&&error)puts(static_cast<char const*>(error->GetBufferPointer()));Check(hr);
 ComPtr<ID3D11ComputeShader> shader;Check(d->CreateComputeShader(blob->GetBufferPointer(),blob->GetBufferSize(),nullptr,&shader));
 D3D11_TEXTURE2D_DESC desc={W,H,1,1,DXGI_FORMAT_R32G32B32A32_FLOAT,{1,0},D3D11_USAGE_DEFAULT,D3D11_BIND_SHADER_RESOURCE,0,0};
 ComPtr<ID3D11Texture2D> tex[2];ComPtr<ID3D11ShaderResourceView> view[2];
 for(int i=0;i<2;i++){Check(d->CreateTexture2D(&desc,nullptr,&tex[i]));Check(d->CreateShaderResourceView(tex[i].Get(),nullptr,&view[i]));}
 desc.Format=DXGI_FORMAT_R32G32_FLOAT;desc.BindFlags=D3D11_BIND_UNORDERED_ACCESS;
 ComPtr<ID3D11Texture2D> output,readback;Check(d->CreateTexture2D(&desc,nullptr,&output));
 ComPtr<ID3D11UnorderedAccessView> uav;Check(d->CreateUnorderedAccessView(output.Get(),nullptr,&uav));
 desc.BindFlags=0;desc.Usage=D3D11_USAGE_STAGING;desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;Check(d->CreateTexture2D(&desc,nullptr,&readback));
 D3D11_BUFFER_DESC bd={32,D3D11_USAGE_DEFAULT,D3D11_BIND_CONSTANT_BUFFER,0,0,0};
 ComPtr<ID3D11Buffer> buffer;Check(d->CreateBuffer(&bd,nullptr,&buffer));
 std::vector<float> previous(W*H*4),current(W*H*4);
 auto pattern=[](float x,float y){return .5f+.13f*sinf(x*.37f+y*.21f)+.12f*cosf(x*.113f-y*.173f)+.1f*sinf(x*.071f+y*.087f);};
 for(unsigned y=0;y<H;y++)for(unsigned x=0;x<W;x++){
  float a=pattern(float(x),float(y)),b=pattern(float(x)+.5f+y*.03125f,float(y));
  for(unsigned k=0;k<4;k++){previous[(y*W+x)*4+k]=a;current[(y*W+x)*4+k]=b;}
 }
 c->UpdateSubresource(tex[1].Get(),0,nullptr,previous.data(),W*16,0);
 for(unsigned test=0;test<3;test++){
  c->UpdateSubresource(tex[0].Get(),0,nullptr,test==2?previous.data():current.data(),W*16,0);
  struct{unsigned w,h,reset,mode;float strength,pad[3];} params={W,H,test==1?1u:0u,2,1,{}};
  c->UpdateSubresource(buffer.Get(),0,nullptr,&params,0,0);
  ID3D11Buffer* cb=buffer.Get();ID3D11ShaderResourceView* srv[]={view[0].Get(),view[1].Get()};ID3D11UnorderedAccessView* target=uav.Get();
  c->CSSetShader(shader.Get(),nullptr,0);c->CSSetConstantBuffers(0,1,&cb);c->CSSetShaderResources(0,2,srv);c->CSSetUnorderedAccessViews(2,1,&target,nullptr);
  c->Dispatch((W+31)/32,(H+31)/32,1);target=nullptr;c->CSSetUnorderedAccessViews(2,1,&target,nullptr);
  c->CopyResource(readback.Get(),output.Get());D3D11_MAPPED_SUBRESOURCE map;Check(c->Map(readback.Get(),0,D3D11_MAP_READ,0,&map));
  double sum=0;unsigned count=0,fractional=0,varying=0;
  for(unsigned y=0;y<H;y++)for(unsigned x=0;x<W;x++){
   auto* v=reinterpret_cast<float*>(static_cast<unsigned char*>(map.pData)+y*map.RowPitch)+2*x;
   if(!std::isfinite(v[0])||!std::isfinite(v[1]))return 2;
   if(test&& (v[0]!=0||v[1]!=0)){puts("FAIL reset/static not zero");return 3;}
   if(x>20&&x<W-20&&y>20&&y<H-20){
    sum+=fabs(v[0]-(.5+y*.03125))+fabs(v[1]);count++;
    if(fabs(v[0]-round(v[0]))>.01)fractional++;
    if(x%4&&fabs(v[0]-v[-2])>.001)varying++;
   }
  }
  c->Unmap(readback.Get(),0);
  if(!test){printf("Flow MAE=%.3f px; subpixel=%u/%u; within-block variations=%u\n",sum/count,fractional,count,varying);
   if(sum/count>.8||fractional<count/2||varying<count/5)return 4;}
 }
 puts("PASS per-pixel subpixel motion, reset/static zero, partial dispatch edges");
}
