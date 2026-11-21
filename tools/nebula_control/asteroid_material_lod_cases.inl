// Real RP9 draw routing with the two-layer opaque material used by the large
// Omega-15 mining asteroids. Include after check_object_fog.cpp's D3D fixture.
const bool expectBug=getenv("FOG_MATERIAL_EXPECT_BUG")!=nullptr;
Handle detail;C(d->CreateTexture(4,4,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&detail.Texture,0));
C(detail.Texture->LockRect(0,&lock,0,0));
for(int y=0;y<4;++y)for(int x=0;x<4;++x)((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=0xff808080;
detail.Texture->UnlockRect(0);
p->DeviceStates_.TextureBindings[1]={&detail,1,{}};C(d->SetTexture(1,detail.Texture));
tss(1,D3DTSS_COLOROP,D3DTOP_MODULATE2X);tss(1,D3DTSS_COLORARG1,D3DTA_TEXTURE);tss(1,D3DTSS_COLORARG2,D3DTA_CURRENT);
tss(1,D3DTSS_ALPHAOP,D3DTOP_MODULATE);tss(1,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);tss(1,D3DTSS_ALPHAARG2,D3DTA_CURRENT);
tss(1,D3DTSS_TEXCOORDINDEX,0);tss(1,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_COUNT2);
e->RockClass=RPRockAsteroid;e->SurfaceShader=RPSurfaceRock;e->bRockEnabled=true;e->RockRadius=245;e->RockDetail=detail.Texture;
rs(D3DRS_FOGSTART,bits(0));rs(D3DRS_FOGEND,bits(.25f));
rs(D3DRS_ZENABLE,1);rs(D3DRS_ZWRITEENABLE,1);rs(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
auto pixels=[&](){C(d->GetRenderTargetData(target,read));C(read->LockRect(&lock,0,D3DLOCK_READONLY));std::vector<DWORD> result(900*600);
 for(int y=0;y<600;++y)memcpy(result.data()+y*900,(char*)lock.pBits+y*lock.Pitch,900*4);read->UnlockRect();return result;};
const DWORD background=0xff965a14;
auto draw=[&](unsigned scope,bool expected){
 p->ExSurfaceRelease();C(p->SetLocalShadowReceiver(scope));C(d->SetFVF(fvf));
 C(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));C(d->BeginScene());
 const bool active=p->ExSurfaceBegin();printf("scope=%u route=%u\n",scope,active);R(active==expected,"layered asteroid keeps fog coverage at native distance tier");
 C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(V)));if(active)p->ExSurfaceEnd();C(d->EndScene());return pixels();
};
auto closePixels=draw(512,true);
auto distantPixels=draw(768,!expectBug);
if(expectBug){
 unsigned material=0;for(auto pixel:distantPixels)material+=(pixel&0xffffff)!=(background&0xffffff);
 R(material==0,"native fallback loses all material to flat fog");
 puts("REPRODUCED: two-texture material rejects native-distance shader and writes solid fog-coloured depth");
}else{
 unsigned covered=0,nearCovered=0;
 for(size_t i=0;i<distantPixels.size();++i){covered+=distantPixels[i]!=background;nearCovered+=closePixels[i]!=background;
  R((closePixels[i]==background)==(distantPixels[i]==background),"coverage does not jump when the lighting tier changes");}
 R(covered>1000 && covered<100000 && covered==nearCovered,"distant material retains sparse coverage");
 float modes[4]={};C(d->GetPixelShaderConstantF(97,modes,1));R(modes[0]==D3DTOP_MODULATE2X&&modes[3]==1,"native detail constants uploaded");
 auto repeat=draw(768,true);R(repeat==distantPixels,"stable repeat frame");
 // A single-layer material following a two-layer one must clear the detail flag.
 tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);draw(768,true);C(d->GetPixelShaderConstantF(97,modes,1));R(modes[3]==0,"no stale detail on next material");
 // Preserve actual native lighting, detail colour operations, UV transform and alpha.
 C(detail.Texture->LockRect(0,&lock,0,0));
 for(int y=0;y<4;++y)for(int x=0;x<4;++x)((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=((x+y)&1)?0x804060a0:0xc0906040;
 detail.Texture->UnlockRect(0);
 D3DXMATRIX detailMatrix=id;detailMatrix._11=2;detailMatrix._22=3;detailMatrix._31=.25f;
 memcpy(p->DeviceStates_.TextureTransforms[1].Values,&detailMatrix,64);C(d->SetTransform(D3DTS_TEXTURE1,&detailMatrix));
 rs(D3DRS_FOGSTART,bits(10));rs(D3DRS_FOGEND,bits(11));
 for(unsigned op:{D3DTOP_MODULATE,D3DTOP_MODULATE2X,D3DTOP_MODULATE4X,D3DTOP_ADD,D3DTOP_ADDSIGNED}){
  tss(1,D3DTSS_COLOROP,op);auto native=draw(256,false);auto modern=draw(768,true);
  unsigned tested=0;double error=0;
  for(int y=80;y<520;y+=13)for(int x=110;x<790;x+=17){size_t i=y*900+x;
   // Point samples exactly on a texel boundary may round to either neighbour
   // between the fixed-function and programmable interpolators.
   float tu=((x-90.f)/720*2+.25f)*4,tv=(y-60.f)/480*3*4;
   if(fabsf(tu-roundf(tu))<.0001f || fabsf(tv-roundf(tv))<.0001f)continue;
   error+=delta(native[i],modern[i]);++tested;
   if(abs(int(native[i]>>24)-int(modern[i]>>24))>1)printf("alpha mismatch x=%d y=%d native=%08lx modern=%08lx\n",x,y,native[i],modern[i]);
   R(abs(int(native[i]>>24)-int(modern[i]>>24))<=1,"authored second-layer alpha preserved");}
  printf("PASS native detail op %u: mean RGB error %.3f/255\n",op,error/tested);
  R(error/tested<2.1,"native detail colour and transformed UV retained");
 }
 C(detail.Texture->LockRect(0,&lock,0,0));
 for(int y=0;y<4;++y)for(int x=0;x<4;++x)((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=0xff808080;
 detail.Texture->UnlockRect(0);
 rs(D3DRS_FOGSTART,bits(0));rs(D3DRS_FOGEND,bits(.25f));
 tss(1,D3DTSS_COLOROP,D3DTOP_MODULATE2X);distantPixels=draw(768,true);
 printf("PASS near/far coverage identical: %u samples\n",covered);
}
// Depth check: the bright background must show through every vanished sample.
// This recreates the contrast responsible for the pale patch in the live capture.
p->ExSurfaceRelease();rs(D3DRS_FOGENABLE,0);rs(D3DRS_LIGHTING,0);rs(D3DRS_ZWRITEENABLE,0);
C(d->SetTexture(0,nullptr));C(d->SetTexture(1,nullptr));C(d->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE));
tss(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1);tss(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE);tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
struct Screen{float x,y,z,w;DWORD colour;};
Screen plane[]={{-.5f,-.5f,.8f,1,0xffffff40},{899.5f,-.5f,.8f,1,0xffffff40},{-.5f,599.5f,.8f,1,0xffffff40},{899.5f,599.5f,.8f,1,0xffffff40}};
C(d->BeginScene());C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,plane,sizeof(Screen)));C(d->EndScene());auto composited=pixels();
unsigned blocked=0;
for(size_t i=0;i<distantPixels.size();++i){blocked+=(composited[i]&0xffffff)!=0xffff40;
 if(!expectBug)R(distantPixels[i]==background?(composited[i]&0xffffff)==0xffff40:composited[i]==distantPixels[i],"colour and depth vanish together");}
if(expectBug)R(blocked>300000,"flat fog fallback still blocks the bright background");
else R(blocked<100000,"no solid silhouette after fade");
C(D3DXSaveSurfaceToFileA(argv[1],D3DXIFF_PNG,target,nullptr,nullptr));
printf("%s layered material depth: blocked %u pixels\n",expectBug?"REPRODUCED":"PASS",blocked);
return 0;
