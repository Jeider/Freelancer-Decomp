#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wincrypt.h>
#include <string.h>
static const char* kExeHash="ce31304cf0e3353e72926281b612697a1815cc94042dfc80be6c252c9fb5c920";
static const char* kCommonHash="7d358c16d2285d9e0d1ef0248a7acb8f26f6828c4a9f300320a11da77aff1d0c";
static bool verifyFile(const wchar_t* path,const char* expected) {
    HANDLE f=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,0,nullptr);
    if(f==INVALID_HANDLE_VALUE)return false;
    HCRYPTPROV provider=0;HCRYPTHASH hash=0;bool ok=false;
    if(CryptAcquireContextW(&provider,nullptr,nullptr,PROV_RSA_AES,CRYPT_VERIFYCONTEXT) && CryptCreateHash(provider,CALG_SHA_256,0,0,&hash)) {
        BYTE buffer[8192];DWORD n;bool readOk=true;
        for(;;){if(!ReadFile(f,buffer,sizeof buffer,&n,nullptr)){readOk=false;break;}if(!n)break;if(!CryptHashData(hash,buffer,n,0)){readOk=false;break;}}
        BYTE bytes[32];DWORD size=32;char hex[65]={};const char* digits="0123456789abcdef";
        if(readOk && CryptGetHashParam(hash,HP_HASHVAL,bytes,&size,0)) {
            for(unsigned i=0;i<32;++i){hex[i*2]=digits[bytes[i]>>4];hex[i*2+1]=digits[bytes[i]&15];}
            ok=_stricmp(hex,expected)==0;
        }
    }
    if(hash)CryptDestroyHash(hash);if(provider)CryptReleaseContext(provider,0);CloseHandle(f);return ok;
}
