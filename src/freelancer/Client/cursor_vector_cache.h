// Size-adaptive raster cache for code-authored vector cursors. No per-frame
// tessellation or blur: a hit is one cached handle and one ordinary cursor quad.
#pragma once
#include "cursor_vector_art.h"
#include "pixel_format.h"
#include "port_config.h"
#include "DALib.h"
#include "render/IRenderPipeline.h"

namespace CursorVectorCache {
struct Entry { void* texture=nullptr;int size=0;bool failed=false; };
inline Entry* Entries() {static Entry entries[16];return entries;}
inline bool Enabled() {static bool const enabled=PortConfigInt("Render","vector_cursors",1)!=0;return enabled;}
inline int Find(char const* name) {
    for(size_t i=0;i<CursorVectorArt::Icons().size();++i)
        if(_stricmp(name,CursorVectorArt::Icons()[i].name)==0)return static_cast<int>(i);
    return -1;
}
inline void Clear() {
    for(int i=0;i<16;++i) {
        auto& entry=Entries()[i];
        if(entry.texture && DALib::Pipeline)DALib::Pipeline->DestroyTexture(entry.texture);
        entry=Entry{};
    }
}
inline void* Get(int index,float displayedSide) {
    if(index<0 || index>=16 || !DALib::Pipeline || !std::isfinite(displayedSide) || displayedSide<=0)return nullptr;
    auto& entry=Entries()[index];
    int size=CursorVectorArt::TextureSize(displayedSide);
    if(entry.size==size)return entry.failed?nullptr:entry.texture;
    // Managed textures survive D3D9 reset. MouseShutdown releases them before
    // pipeline teardown. Replacing a size bucket never accumulates old copies.
    if(entry.texture)DALib::Pipeline->DestroyTexture(entry.texture);
    entry={nullptr,size,true};
    unsigned format=static_cast<unsigned>(PixelFormatFromD3D(21)); // A8R8G8B8
    if(!format)return nullptr;
    void* texture=nullptr;
    if(DALib::Pipeline->CreateTexture(size,size,&format,1,0,&texture)!=GR_OK || !texture)return nullptr;
    auto pixels=CursorVectorArt::Rasterize(CursorVectorArt::Icons()[index],size);
    // Explicit top-down rows, straight alpha. No image-format orientation flags
    // enter this path; v=0 is the top edge of the existing cursor quad.
    if(DALib::Pipeline->SetTextureLevelData(texture,0,size,size,size*4,&format,pixels.data(),nullptr,nullptr)!=GR_OK) {
        DALib::Pipeline->DestroyTexture(texture);return nullptr;
    }
    entry.texture=texture;entry.failed=false;
    return texture;
}
}
