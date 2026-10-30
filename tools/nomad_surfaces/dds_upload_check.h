// Real RP9 upload, using the same DDS cursor and pitches as TextureLibrary.
#include "../../src/include/render/DdsMipCursor.h"
static void CheckWebDdsUpload(FDirectX9* p,IDirect3DDevice9* d)
{
 struct TextureHandle {IDirect3DTexture9* Texture;unsigned long Extra=0;};
 p->PipelineStates_[2].Value=1;
 for(const char* name:{"web-outer-v1","web-inner-v1"}) {
  char path[256];sprintf(path,"src/obj/nomad_membrane/%s.dds",name);
  FILE* f=fopen(path,"rb");Need(f!=nullptr,"DDS fixture exists");fseek(f,0,SEEK_END);size_t size=ftell(f);rewind(f);std::vector<unsigned char> data(size);Need(fread(data.data(),1,size,f)==size,"read DDS");fclose(f);
  auto* header=reinterpret_cast<const DWORD*>(data.data());
  Need(header[21]==D3DFMT_DXT5 && !(header[2]&8),"DXT5 linear-size header");
  IDirect3DTexture9* reference=nullptr;Check(D3DXCreateTextureFromFileInMemoryEx(d,data.data(),UINT(size),D3DX_DEFAULT,D3DX_DEFAULT,D3DX_DEFAULT,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,D3DX_FILTER_NONE,D3DX_FILTER_NONE,0,nullptr,nullptr,&reference));
  for(D3DFORMAT target:{D3DFMT_DXT5,D3DFMT_A8R8G8B8}) {
   TextureHandle upload={};Check(d->CreateTexture(header[4],header[3],header[7],0,target,D3DPOOL_MANAGED,&upload.Texture,nullptr));
   Need(header[5]==0,"fixture reproduces omitted DDS linear size");
   FTextureDdsCursor cursor={data.data()+128,FTextureDdsCursor::CompressedBytes(header[4],header[3],16),16,header[4],header[3],true};
   for(unsigned level=0;level<header[7];++level) {
    size_t offset=cursor.Pixels-data.data();unsigned bytes=cursor.Bytes,width=cursor.Width,height=cursor.Height;
    unsigned format=14;Need(offset+bytes<=data.size(),"DDS mip bounds");
    Check(p->SetTextureLevelData(&upload,level,width,height,((width+3)/4)*16,&format,data.data()+offset,nullptr,nullptr));
    IDirect3DSurface9 *surface=nullptr,*decoded=nullptr;Check(upload.Texture->GetSurfaceLevel(level,&surface));Check(d->CreateOffscreenPlainSurface(width,height,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&decoded,nullptr));
    Check(D3DXLoadSurfaceFromSurface(decoded,nullptr,nullptr,surface,nullptr,nullptr,D3DX_FILTER_NONE,0));
    D3DLOCKED_RECT a={},b={};Check(decoded->LockRect(&a,nullptr,D3DLOCK_READONLY));Check(reference->LockRect(level,&b,nullptr,D3DLOCK_READONLY));
    unsigned maxRgb=0,maxAlpha=0,alphaPixels=0;
    for(unsigned y=0;y<height;++y)for(unsigned x=0;x<width*4;++x){int av=static_cast<unsigned char*>(a.pBits)[y*a.Pitch+x],bv=static_cast<unsigned char*>(b.pBits)[y*b.Pitch+x];unsigned delta=unsigned(abs(av-bv));if(x%4==3){maxAlpha=(std::max)(maxAlpha,delta);if(delta>1)++alphaPixels;}else maxRgb=(std::max)(maxRgb,delta);}
    printf("%s target %08x mip %u %ux%u offset %u bytes %u RGB error %u alpha error %u (%u pixels)\n",name,unsigned(target),level,width,height,unsigned(offset),bytes,maxRgb,maxAlpha,alphaPixels);
    decoded->UnlockRect();reference->UnlockRect(level);decoded->Release();surface->Release();
    Need(maxRgb<=1 && maxAlpha<=1,"engine upload equals D3DX reference RGBA at every mip");
    cursor.Advance();
   }
   upload.Texture->Release();
  }
  reference->Release();printf("PASS real RP9 upload: %s, 11 mips, DXT5 and RGBA8 targets\n",name);
 }
}
