#pragma once

// Persistent SM3 bytecode, independent of a D3D device. Expanded source is the
// dependency manifest: includes, macros and compiler identity all affect its key.
#include <windows.h>
#include <wincrypt.h>
#include <d3dx9.h>
#include <string>
#include <vector>
#include <cstring>
#pragma comment(lib,"advapi32.lib")

namespace Rp9ShaderCache
{
    class Hash
    {
        HCRYPTPROV Provider=0;
        HCRYPTHASH Handle=0;
        bool Valid=false;
    public:
        Hash() {Valid=CryptAcquireContextW(&Provider,nullptr,nullptr,PROV_RSA_AES,CRYPT_VERIFYCONTEXT)!=0 &&
                       CryptCreateHash(Provider,CALG_SHA_256,0,0,&Handle)!=0;}
        ~Hash() {if(Handle) CryptDestroyHash(Handle);if(Provider) CryptReleaseContext(Provider,0);}
        bool Add(const void* Bytes,size_t Count)
        {
            if(!Valid || Count>MAXDWORD) return false;
            Valid=CryptHashData(Handle,(const BYTE*)Bytes,(DWORD)Count,0)!=0;return Valid;
        }
        bool String(const std::string& Text)
        {DWORD Size=(DWORD)Text.size();return Add(&Size,sizeof(Size)) && Add(Text.data(),Text.size());}
        bool Finish(BYTE Out[32])
        {DWORD Size=32;return Valid && CryptGetHashParam(Handle,HP_HASHVAL,Out,&Size,0)!=0 && Size==32;}
        Hash(const Hash&)=delete;
        Hash& operator=(const Hash&)=delete;
    };

    inline bool HashModule(Hash& Digest,HMODULE Module)
    {
        if(!Module) return false;
        wchar_t Path[MAX_PATH]={};DWORD Count=GetModuleFileNameW(Module,Path,MAX_PATH);
        if(!Count || Count>=MAX_PATH) return false;
        HANDLE File=CreateFileW(Path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,0,nullptr);
        if(File==INVALID_HANDLE_VALUE) return false;
        BYTE Buffer[32768];DWORD Got=0;bool Ok=true;
        for(;;)
        {
            if(!ReadFile(File,Buffer,sizeof(Buffer),&Got,nullptr)) {Ok=false;break;}
            if(!Got) break;
            if(!Digest.Add(Buffer,Got)) {Ok=false;break;}
        }
        CloseHandle(File);return Ok;
    }

    inline const std::string& CompilerIdentity()
    {
        // Called after preprocessing, so the compiler's lazy dependency is loaded.
        static const std::string Identity=[]() -> std::string {
            HMODULE Module=nullptr;
            if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                reinterpret_cast<LPCWSTR>(&D3DXPreprocessShader),&Module)) return {};
            Hash Digest;
            if(!HashModule(Digest,Module)) return {};
            HMODULE Compiler=GetModuleHandleW(L"d3dcompiler_43.dll");
            if(Compiler && !HashModule(Digest,Compiler)) return {};
            BYTE Bytes[32];if(!Digest.Finish(Bytes)) return {};
            return std::string((char*)Bytes,sizeof(Bytes));
        }();
        return Identity;
    }

    inline std::string Key(const std::string& Source,const std::string& Entry,const char* Profile,DWORD Flags)
    {
        auto const& Compiler=CompilerIdentity();if(Compiler.empty()) return {};
        Hash Digest;
        if(!Digest.String("Freelancer-RP9-SM3-cache-v1") || !Digest.String(Compiler) ||
           !Digest.String(Source) || !Digest.String(Entry) || !Digest.String(Profile) ||
           !Digest.Add(&Flags,sizeof(Flags))) return {};
        BYTE Bytes[32];if(!Digest.Finish(Bytes)) return {};
        const char Hex[]="0123456789abcdef";std::string Result;
        for(BYTE B:Bytes) {Result+=Hex[B>>4];Result+=Hex[B&15];}return Result;
    }

    inline std::wstring Directory()
    {
        // Override is useful for isolated tests and portable installs.
        wchar_t Path[MAX_PATH]={};
        DWORD Count=GetEnvironmentVariableW(L"FREELANCER_SHADER_CACHE_DIR",Path,MAX_PATH);
        if(Count && Count<MAX_PATH) return Path;
        Count=GetEnvironmentVariableW(L"LOCALAPPDATA",Path,MAX_PATH);
        if(!Count || Count>=MAX_PATH) return {};
        return std::wstring(Path)+L"\\Freelancer-Decomp\\RP9\\ShaderCache";
    }

    inline std::wstring FilePath(const std::wstring& Folder,const std::string& Key)
    {
        if(Folder.empty() || Key.size()!=64) return {};
        for(char C:Key) if(!((C>='0'&&C<='9')||(C>='a'&&C<='f'))) return {};
        return Folder+L"\\"+std::wstring(Key.begin(),Key.end())+L".bin";
    }

    struct Header {DWORD Magic,Version,Size;BYTE Digest[32];char Key[64];};
    const DWORD Magic=0x43533952; // R9SC
    const DWORD MaxSize=1024*1024;

    inline bool Load(const std::string& CacheKey,std::vector<unsigned char>* Out)
    {
        std::wstring Path=FilePath(Directory(),CacheKey);if(Path.empty()) return false;
        HANDLE File=CreateFileW(Path.c_str(),GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_DELETE,
                                nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
        if(File==INVALID_HANDLE_VALUE) return false;
        Header H={};DWORD Got=0;LARGE_INTEGER Size={};
        bool Ok=GetFileSizeEx(File,&Size)!=0 && ReadFile(File,&H,sizeof(H),&Got,nullptr)!=0 &&
            Got==sizeof(H) && H.Magic==Magic && H.Version==1 && H.Size>=8 && H.Size<=MaxSize &&
            H.Size%4==0 && Size.QuadPart==(LONGLONG)(sizeof(H)+H.Size) && memcmp(H.Key,CacheKey.data(),64)==0;
        std::vector<unsigned char> Bytes;
        if(Ok) {Bytes.resize(H.Size);Ok=ReadFile(File,Bytes.data(),H.Size,&Got,nullptr)!=0 && Got==H.Size;}
        CloseHandle(File);
        if(Ok)
        {
            Hash Digest;BYTE Actual[32];DWORD End=0;
            memcpy(&End,Bytes.data()+Bytes.size()-4,4);
            Ok=End==0x0000ffff && Digest.Add(Bytes.data(),Bytes.size()) && Digest.Finish(Actual) &&
               memcmp(Actual,H.Digest,32)==0;
        }
        if(Ok) Out->swap(Bytes);return Ok;
    }

    inline bool Store(const std::string& CacheKey,const std::vector<unsigned char>& Bytes)
    {
        std::wstring Folder=Directory(),Path=FilePath(Folder,CacheKey);
        if(Path.empty() || Bytes.size()<8 || Bytes.size()>MaxSize) return false;
        for(size_t I=3;I<Folder.size();++I) if(Folder[I]==L'\\' || Folder[I]==L'/')
            CreateDirectoryW(Folder.substr(0,I).c_str(),nullptr);
        CreateDirectoryW(Folder.c_str(),nullptr);
        Header H={Magic,1,(DWORD)Bytes.size(),{}};Hash Digest;
        memcpy(H.Key,CacheKey.data(),64);
        if(!Digest.Add(Bytes.data(),Bytes.size()) || !Digest.Finish(H.Digest)) return false;
        wchar_t Temp[MAX_PATH]={};
        if(!GetTempFileNameW(Folder.c_str(),L"rp9",0,Temp)) return false;
        HANDLE File=CreateFileW(Temp,GENERIC_WRITE,0,nullptr,TRUNCATE_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
        bool Ok=File!=INVALID_HANDLE_VALUE;
        if(Ok)
        {
            DWORD Written=0;
            Ok=WriteFile(File,&H,sizeof(H),&Written,nullptr)!=0 && Written==sizeof(H) &&
               WriteFile(File,Bytes.data(),H.Size,&Written,nullptr)!=0 && Written==H.Size;
            CloseHandle(File);
        }
        if(Ok) Ok=MoveFileExW(Temp,Path.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;
        if(!Ok) DeleteFileW(Temp); // only this call's own temporary file
        return Ok;
    }

    inline HRESULT Compile(const std::string& Source,ID3DXInclude* Include,const std::string& Entry,
                           const char* Profile,DWORD Flags,std::vector<unsigned char>* Out,
                           std::string* Messages,bool* Hit,bool* Stored)
    {
        *Hit=false;*Stored=false;Messages->clear();
        ID3DXBuffer *Expanded=nullptr,*Errors=nullptr;
        HRESULT Hr=D3DXPreprocessShader(Source.data(),(UINT)Source.size(),nullptr,Include,&Expanded,&Errors);
        if(Errors) {Messages->append((char*)Errors->GetBufferPointer());Errors->Release();Errors=nullptr;}
        if(FAILED(Hr) || !Expanded) {if(Expanded) Expanded->Release();return FAILED(Hr)?Hr:E_FAIL;}
        // D3DX's text buffer includes the terminating NUL.
        std::string Text((char*)Expanded->GetBufferPointer());Expanded->Release();
        std::string CacheKey=Key(Text,Entry,Profile,Flags);
        if(!CacheKey.empty() && Load(CacheKey,Out)) {*Hit=true;return S_OK;}
        ID3DXBuffer* Code=nullptr;
        Hr=D3DXCompileShader(Text.data(),(UINT)Text.size(),nullptr,nullptr,Entry.c_str(),Profile,
                            Flags,&Code,&Errors,nullptr);
        if(Errors) {Messages->append((char*)Errors->GetBufferPointer());Errors->Release();}
        if(SUCCEEDED(Hr) && Code)
        {
            auto* Bytes=(unsigned char*)Code->GetBufferPointer();
            Out->assign(Bytes,Bytes+Code->GetBufferSize());
            if(!CacheKey.empty()) *Stored=Store(CacheKey,*Out);
        }
        else if(SUCCEEDED(Hr)) Hr=E_FAIL;
        if(Code) Code->Release();return Hr;
    }
}
