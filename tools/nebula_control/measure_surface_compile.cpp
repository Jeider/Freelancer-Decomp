#include <d3dx9.h>
#include <chrono>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
int main(int argc,char**argv){
 if(argc!=2)return 2;setvbuf(stdout,nullptr,_IONBF,0);
 std::ifstream file(argv[1]);std::string source((std::istreambuf_iterator<char>(file)),{});
 if(source.empty())return 2;
 source="#define SURFACE_RELIEF_QUALITY 0\n#define SURFACE_HIGHLIGHT_QUALITY 0\n"+source;
 ID3DXBuffer* code=nullptr,*errors=nullptr;auto start=std::chrono::steady_clock::now();
 printf("Compiling %s full-shadow quality 0\n",argv[1]);
 HRESULT h=D3DXCompileShader(source.data(),(UINT)source.size(),nullptr,nullptr,"PSMain","ps_3_0",0,&code,&errors,nullptr);
 printf("HRESULT %08lx, %.3f seconds\n",h,std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count());
 if(errors){puts((char*)errors->GetBufferPointer());errors->Release();}
 if(code)code->Release();return FAILED(h)?3:0;
}
