// Exercise the real native/enhanced rock routes, combining fog and birth in one
// grid. White/black differences isolate retained material from in-scattering.
IDirect3DTexture9* fogDetail=nullptr;C(d->CreateTexture(4,4,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&fogDetail,0));
C(fogDetail->LockRect(0,&lock,0,0));
for(int y=0;y<4;++y)for(int x=0;x<4;++x)((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=0xff808080;
fogDetail->UnlockRect(0);
e->RockClass=1;e->bRockEnabled=true;e->RockRadius=35;e->RockDetail=fogDetail;
for(int mode=0;mode<2;++mode){
 const unsigned scope=mode?512:768;
 rs(D3DRS_FOGENABLE,1);rs(D3DRS_FOGSTART,bits(10));rs(D3DRS_FOGEND,bits(11));
 setAlbedo(0xbfffffff);auto clearWhite=spawnFrame(scope,true);
 setAlbedo(0xbf000000);auto clearBlack=spawnFrame(scope,true);
 unsigned footprint=0;for(auto pixel:clearWhite)footprint+=pixel!=background;
 R(footprint>200000,"fog grid footprint");
 unsigned previousCoverage=footprint;
 for(float path:{.2f,.6f,1.f,2.f,4.f}){
  rs(D3DRS_FOGSTART,bits(0));rs(D3DRS_FOGEND,bits(.5f/path));
  setAlbedo(0xbfffffff);auto white=spawnFrame(scope,true);
  setAlbedo(0xbf000000);auto black=spawnFrame(scope,true);
  unsigned covered=0;double contrastSum=0,referenceSum=0,expectedCoverage=0;
  for(size_t i=0;i<white.size();++i){
   if(clearWhite[i]==background){R(white[i]==background&&black[i]==background,"fog grid leaves sky untouched");continue;}
   float x=2.f*float(i%900)/900-1,y=1-2.f*float(i/900)/600;
   float optical=sqrtf(x*x+y*y+.25f)*2*path;
   float transmission=exp2f(-2*optical*optical/(optical+.35f));
   expectedCoverage+=transmission/(std::max)(transmission,.55f);
   if(white[i]==background){R(black[i]==background,"albedo-independent coverage");continue;}
   ++covered;
   contrastSum+=int((white[i]>>16)&255)-int((black[i]>>16)&255);
   referenceSum+=int((clearWhite[i]>>16)&255)-int((clearBlack[i]>>16)&255);
  }
  R(covered<=previousCoverage && (path<.6f || covered<previousCoverage),"fog grid becomes sparser with optical distance");previousCoverage=covered;
  R(fabs(double(covered)-expectedCoverage)/footprint<.015,"coverage follows optical extinction, not a distance cutoff");
  R(contrastSum/referenceSum>.50,"covered samples keep material contrast");
  R(black==spawnFrame(scope,true),"fog grid is identical on repeat frames");
  auto half=spawnFrame(scope|1024u|(128u<<16),true);unsigned halfCount=0;
  for(size_t i=0;i<half.size();++i)if(half[i]!=background){++halfCount;
   R(black[i]!=background&&delta(black[i],half[i])<=1,"birth keeps fog-covered material unchanged");}
  R(fabs(double(halfCount)-covered*128./255)/footprint<.016,"birth and fog coverage multiply, never a second competing mask");
  printf("PASS physical rock grid mode %d path %.1f: %.2f%% coverage, %.3f sample contrast, birth ratio %.3f\n",
   mode,path,100.*covered/footprint,contrastSum/referenceSum,double(halfCount)/covered);
 }
}
// Fog holes must also be depth holes: draw a plane behind the material.
rs(D3DRS_FOGEND,bits(.5f));auto fogDepth=spawnFrame(768,true);
p->ExSurfaceRelease();rs(D3DRS_FOGENABLE,0);rs(D3DRS_LIGHTING,0);rs(D3DRS_ZWRITEENABLE,0);
C(d->SetTexture(0,nullptr));C(d->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE));
C(d->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1));C(d->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE));
struct FogScreen{float x,y,z,w;DWORD colour;};
FogScreen fogPlane[]={{-.5f,-.5f,.8f,1,0xff00ff00},{899.5f,-.5f,.8f,1,0xff00ff00},{-.5f,599.5f,.8f,1,0xff00ff00},{899.5f,599.5f,.8f,1,0xff00ff00}};
C(d->BeginScene());C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,fogPlane,sizeof(FogScreen)));C(d->EndScene());auto fogBehind=framePixels();
for(size_t i=0;i<fogDepth.size();++i)R(fogDepth[i]==background?fogBehind[i]==0xff00ff00:fogBehind[i]==fogDepth[i],"fog coverage matches colour/depth");
C(p->SetLocalShadowReceiver(0));e->RockClass=0;e->RockDetail=nullptr;fogDetail->Release();
puts("PASS fog grid depth, sky, texture, scope, native/enhanced routes and combined birth coverage");
