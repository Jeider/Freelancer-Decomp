#pragma once
#include <windows.h>
#include <wincodec.h>
#include <wrl/client.h>
#include <cstdint>
#include <cstring>
#include <vector>
#pragma comment(lib,"ole32.lib")
#pragma comment(lib,"windowscodecs.lib")

namespace Rp9Startup {
// Compressed JPEGs stay in the executable's resource section. Only one decoded
// frame is resident. No temporary movie, video codec, D3D device or audio needed.
class Animation {
    const BYTE* Data=nullptr;
    DWORD Size=0, Width=0, Height=0, Rate=0, Scale=0, Count=0;
    LONG Current=-1;
    bool Uninitialize=false;
    Microsoft::WRL::ComPtr<IWICImagingFactory> Factory;
    std::vector<BYTE> Pixels;
    DWORD Word(size_t Offset) const {DWORD V;memcpy(&V,Data+Offset,4);return V;}
public:
    Animation()=default;
    Animation(const Animation&)=delete;
    Animation& operator=(const Animation&)=delete;
    ~Animation() {Close();}
    void Close() {
        Factory.Reset();
        if(Uninitialize) CoUninitialize();
        Uninitialize=false;Data=nullptr;Size=Width=Height=Rate=Scale=Count=0;Current=-1;
        std::vector<BYTE>().swap(Pixels);
    }
    bool Open(const void* Bytes,DWORD Length,const CLSID& FactoryClass=CLSID_WICImagingFactory) {
        Close();
        Data=static_cast<const BYTE*>(Bytes);Size=Length;
        if(!Data || Size<32 || memcmp(Data,"FLJA",4)!=0 || Word(4)!=1) {Close();return false;}
        Width=Word(8);Height=Word(12);Rate=Word(16);Scale=Word(20);Count=Word(24);
        if(!Width || Width>1024 || !Height || Height>1024 || !Rate || Rate>120 ||
           Scale!=1 || !Count || Count>3600 || Size<28+4*(Count+1) ||
           Word(28)!=28+4*(Count+1) || Word(28+4*Count)!=Size) {Close();return false;}
        for(DWORD i=0;i<Count;++i) {
            DWORD A=Word(28+4*i), B=Word(32+4*i);
            if(A>=B || B>Size || B-A<4 || Data[A]!=0xff || Data[A+1]!=0xd8) {Close();return false;}
        }
        const HRESULT Init=CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);
        Uninitialize=SUCCEEDED(Init);
        if((FAILED(Init) && Init!=RPC_E_CHANGED_MODE) ||
           FAILED(CoCreateInstance(FactoryClass,nullptr,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&Factory)))) {
            Close();return false;
        }
        try {Pixels.resize(size_t(Width)*Height*4);} catch(...) {Close();return false;}
        if(!Decode(0)) {Close();return false;}
        return true;
    }
    bool OpenResource(HMODULE Module=GetModuleHandleW(nullptr)) {
        Close();
        HRSRC Resource=FindResourceW(Module,L"FREELANCER_SHADER_ANIMATION",MAKEINTRESOURCEW(10));
        if(!Resource) return false;
        HGLOBAL Loaded=LoadResource(Module,Resource);
        return Loaded && Open(LockResource(Loaded),SizeofResource(Module,Resource));
    }
    bool Decode(DWORD Index) {
        if(!Factory || Index>=Count) return false;
        const DWORD Offset=Word(28+4*Index), Length=Word(32+4*Index)-Offset;
        Microsoft::WRL::ComPtr<IWICStream> Stream;
        Microsoft::WRL::ComPtr<IWICBitmapDecoder> Decoder;
        Microsoft::WRL::ComPtr<IWICBitmapFrameDecode> Frame;
        Microsoft::WRL::ComPtr<IWICFormatConverter> Converter;
        // The executable owns Data throughout the lifetime of this memory stream.
        if(FAILED(Factory->CreateStream(&Stream)) ||
           FAILED(Stream->InitializeFromMemory(const_cast<BYTE*>(Data+Offset),Length)) ||
           FAILED(CoCreateInstance(CLSID_WICJpegDecoder,nullptr,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&Decoder))) ||
           FAILED(Decoder->Initialize(Stream.Get(),WICDecodeMetadataCacheOnLoad)) ||
           FAILED(Decoder->GetFrame(0,&Frame))) return false;
        UINT W=0,H=0;
        if(FAILED(Frame->GetSize(&W,&H)) || W!=Width || H!=Height ||
           FAILED(Factory->CreateFormatConverter(&Converter)) ||
           FAILED(Converter->Initialize(Frame.Get(),GUID_WICPixelFormat32bppBGR,
               WICBitmapDitherTypeNone,nullptr,0,WICBitmapPaletteTypeCustom)) ||
           FAILED(Converter->CopyPixels(nullptr,Width*4,(UINT)Pixels.size(),Pixels.data()))) return false;
        Current=(LONG)Index;
        return true;
    }
    DWORD FrameAt(ULONGLONG Milliseconds) const {
        return Count ? DWORD((Milliseconds*Rate/(1000ULL*Scale))%Count) : 0;
    }
    bool Advance(ULONGLONG Milliseconds) {
        if(!Available()) return false;
        const DWORD Index=FrameAt(Milliseconds);
        if((LONG)Index==Current) return false;
        if(!Decode(Index)) Close();
        return true;
    }
    bool Paint(HDC Dc,const RECT& Rect) const {
        if(!Available()) return false;
        BITMAPINFO Info={};Info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
        Info.bmiHeader.biWidth=(LONG)Width;Info.bmiHeader.biHeight=-(LONG)Height;
        Info.bmiHeader.biPlanes=1;Info.bmiHeader.biBitCount=32;Info.bmiHeader.biCompression=BI_RGB;
        const int Rows=StretchDIBits(Dc,Rect.left,Rect.top,Rect.right-Rect.left,Rect.bottom-Rect.top,
            0,0,Width,Height,Pixels.data(),&Info,DIB_RGB_COLORS,SRCCOPY);
        // Zero scanlines can simply mean the window is occluded.
        return Rows!=GDI_ERROR;
    }
    bool Available() const {return Current>=0 && !Pixels.empty();}
    DWORD FrameCount() const {return Count;}
    LONG FrameIndex() const {return Current;}
    const std::vector<BYTE>& FramePixels() const {return Pixels;}
};
}
