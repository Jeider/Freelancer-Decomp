// Production shader on a curved hull panel, before/after under identical light.
#define main ShipNormalRegressionMain
#include "check.cpp"
#undef main
int main()
{
 HWND w=CreateWindowA("STATIC","matte panel",WS_POPUP,0,0,512,512,0,0,GetModuleHandle(0),0);
 auto*a=Direct3DCreate9(D3D_SDK_VERSION);IDirect3DDevice9*d=nullptr;
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=pp.BackBufferHeight=512;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 Check(a->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 std::string src=Read("DATA_EXTRA/SHADERS/surface_material.hlsl"),before=Read("src/obj/ship_normals/matte/before.hlsl");
 auto v=Compile(src,"VSMain","vs_3_0");IDirect3DVertexShader9*vs=nullptr;Check(d->CreateVertexShader((DWORD*)v.data(),&vs));
 auto make=[&](const std::string&s){auto c=Compile("#define SURFACE_SHIP_NORMALS 1\n#define SURFACE_NO_SHADOW 1\n"+s,"PSMain","ps_3_0");IDirect3DPixelShader9*p=nullptr;Check(d->CreatePixelShader((DWORD*)c.data(),&p));return p;};
 auto*old=make(before);auto*matte=make(src);
 float vc[68]={},pc[102*4]={};D3DXMATRIX id,proj;D3DXMatrixIdentity(&id);
 for(int i=0;i<4;++i)memcpy(vc+16*i,&id,64);
 D3DXMatrixPerspectiveFovLH(&proj,.85f,1,.1f,10);memcpy(vc+16,&proj,64);
 pc[0]=pc[1]=pc[2]=pc[3]=1;pc[4]=pc[5]=pc[6]=.18f;pc[12]=pc[13]=pc[14]=.04f;pc[15]=.35f;
 pc[16]=1;pc[18]=1;pc[19]=1;pc[28]=pc[29]=4;pc[31]=5;memcpy(pc+32,&id,64);
 pc[51]=3;pc[52]=-.45f;pc[53]=-.25f;pc[54]=1;pc[56]=pc[57]=pc[58]=.85f;pc[60]=pc[61]=pc[62]=1;
 pc[388]=1;pc[389]=2000;pc[390]=6000;pc[391]=2;pc[392]=1;
 auto texture=[&](const char*path){IDirect3DTexture9*t=nullptr;Check(D3DXCreateTextureFromFileA(d,path,&t));return t;};
 std::string paths=Read("src/obj/ship_normals/matte/preview_inputs.txt");paths.erase(std::remove(paths.begin(),paths.end(),'\r'),paths.end());size_t split=paths.find('\n');
 std::string np=paths.substr(0,split),mp=paths.substr(split+1);mp.resize(mp.find('\n'));
 auto*diffuse=texture("src/obj/ship_normals/preview_2_diffuse.png");auto*normal=texture(np.c_str());auto*surface=texture(mp.c_str());
 IDirect3DTexture9*env=nullptr;Check(d->CreateTexture(64,64,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&env,0));D3DLOCKED_RECT l;
 Check(env->LockRect(0,&l,0,0));for(int y=0;y<64;++y)for(int x=0;x<64;++x){int c=int(90+65*std::sin(x*.16f)*std::sin(y*.13f));((DWORD*)((char*)l.pBits+y*l.Pitch))[x]=0xff000000|(c<<16)|(c<<8)|c;}env->UnlockRect(0);
 d->SetTexture(0,diffuse);d->SetTexture(10,env);d->SetTexture(13,normal);d->SetTexture(14,surface);
 for(int s:{0,10,13,14}){d->SetSamplerState(s,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);d->SetSamplerState(s,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);d->SetSamplerState(s,D3DSAMP_MIPFILTER,D3DTEXF_LINEAR);}
 std::vector<Vertex> verts;
 auto point=[](int i,int j){float x=-1+2*i/64.f,y=-1+2*j/64.f,n=std::sqrt(1+.81f*x*x);return Vertex{x,y,2.8f+.45f*x*x,.9f*x/n,0,-1/n,(x+1)*.5f,(1-y)*.5f};};
 for(int y=0;y<64;++y)for(int x=0;x<64;++x){Vertex a=point(x,y),b=point(x,y+1),c=point(x+1,y),e=point(x+1,y+1);for(auto p:{a,b,c,c,b,e})verts.push_back(p);}
 d->SetVertexShader(vs);d->SetFVF(D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1);d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);d->SetRenderState(D3DRS_ZENABLE,0);
 d->SetVertexShaderConstantF(0,vc,17);d->SetPixelShaderConstantF(0,pc,102);
 IDirect3DSurface9*rt=nullptr;Check(d->GetRenderTarget(0,&rt));
 for(int i=0;i<2;++i){Check(d->Clear(0,0,D3DCLEAR_TARGET,0xff10151d,1,0));Check(d->BeginScene());d->SetPixelShader(i?matte:old);Check(d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,UINT(verts.size()/3),verts.data(),sizeof(Vertex)));Check(d->EndScene());Check(D3DXSaveSurfaceToFileA(i?"src/obj/ship_normals/matte/after.png":"src/obj/ship_normals/matte/before.png",D3DXIFF_PNG,rt,0,0));}
 rt->Release();d->SetVertexShader(nullptr);d->SetPixelShader(nullptr);for(int s:{0,10,13,14})d->SetTexture(s,nullptr);
 for(auto*t:{diffuse,normal,surface,env})t->Release();old->Release();matte->Release();vs->Release();d->Release();a->Release();DestroyWindow(w);
 puts("Saved identical-light hull material previews");
}
