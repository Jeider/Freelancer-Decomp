// Production RP9: normal-mapped/reflective solar hulls keep their old near/far
// material tiers while using the same colour/depth fog mask.
auto pixels=[&](){C(d->GetRenderTargetData(target,read));C(read->LockRect(&lock,0,D3DLOCK_READONLY));std::vector<DWORD> result(900*600);
 for(int y=0;y<600;++y)memcpy(result.data()+y*900,(char*)lock.pBits+y*lock.Pitch,900*4);read->UnlockRect();return result;};
const DWORD background=0xff112233;
auto draw=[&](unsigned scope,bool expected=true){
 p->ExSurfaceRelease();C(p->SetLocalShadowReceiver(scope));C(d->SetFVF(fvf));
 rs(D3DRS_ZENABLE,1);rs(D3DRS_ZWRITEENABLE,1);rs(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
 C(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));C(d->BeginScene());
 const bool active=p->ExSurfaceBegin();R(active==expected,"solar material route");
 C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(V)));if(active)p->ExSurfaceEnd();C(d->EndScene());return pixels();
};
auto count=[&](std::vector<DWORD> const& frame){unsigned n=0;for(auto v:frame)n+=v!=background;return n;};
auto sameMask=[&](std::vector<DWORD> const&a,std::vector<DWORD> const&b){
 for(size_t i=0;i<a.size();++i)R((a[i]==background)==(b[i]==background),"solar near/far coverage continuity");};
rs(D3DRS_FOGSTART,bits(0));rs(D3DRS_FOGEND,bits(.25f));
e->RockClass=0;e->SurfaceShader=RPSurfaceAuto;
FRp9ExState::ShipNormalMap normal;normal.Texture=base.Texture;
e->ShipNormalCurrent=&normal;e->bWeaponGlintReceiver=true;e->WeaponGlintReceiverMask=1;
for(int mode=0;mode<4;++mode){
 e->bShipNormalScope=(mode&1)!=0;e->ShadowReadyMask=(mode&2)?3:0;
 for(int reflection=0;reflection<2;++reflection){
  tss(1,D3DTSS_COLOROP,reflection?D3DTOP_MODULATE2X:D3DTOP_DISABLE);
  tss(1,D3DTSS_COLORARG1,D3DTA_TEXTURE);tss(1,D3DTSS_COLORARG2,D3DTA_CURRENT);
  tss(1,D3DTSS_TEXCOORDINDEX,D3DTSS_TCI_CAMERASPACEREFLECTIONVECTOR);
  tss(1,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_COUNT2);
  p->DeviceStates_.TextureBindings[1]={&base,1,{}};C(d->SetTexture(1,base.Texture));
  auto closePixels=draw(512|2048|1);float fog[4];C(d->GetPixelShaderConstantF(107,fog,1));
  R(fog[2]==0,"near enhanced solar keeps existing material");
  auto distantPixels=draw(512|2048|256);C(d->GetPixelShaderConstantF(107,fog,1));
  R(fog[2]==1,"far solar retains cheap native lighting");
  R(e->SurfaceLowPs || e->SurfaceLowCubePs || !e->SurfaceQualityPs.empty(),"native coverage compiled");
  float detail[4];C(d->GetPixelShaderConstantF(97,detail,1));R(detail[3]==0,"far solar has no generated normal-map constants");
  sameMask(closePixels,distantPixels);R(count(distantPixels)>1000&&count(distantPixels)<100000,"solar dissolves instead of becoming solid fog");
  R(distantPixels==draw(512|2048|256),"stationary solar mask is stable");
  printf("PASS solar mode %d reflection %d: near/far mask %u pixels, far native lighting\n",mode,reflection,count(distantPixels));
 }
}
e->bShipNormalScope=false;e->ShipNormalCurrent=nullptr;e->ShadowReadyMask=0;
tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
// Re-entering clear air and leaving the test scope must restore full coverage.
auto partial=draw(512|2048|256);
auto ordinary=draw(512);R(count(ordinary)>300000,"ordinary non-solar keeps its prior fog route");
R(!e->bNebulaFogSolar,"solar scope cleared for following object");
auto low=draw(2048);sameMask(ordinary,low);
rs(D3DRS_FOGENABLE,0);auto outside=draw(512|2048);sameMask(ordinary,outside);rs(D3DRS_FOGENABLE,1);
rs(D3DRS_FOGSTART,bits(10));rs(D3DRS_FOGEND,bits(11));auto clear=draw(512|2048|256);sameMask(ordinary,clear);
rs(D3DRS_FOGSTART,bits(0));rs(D3DRS_FOGEND,bits(.5f));auto longer=draw(512|2048|256);
R(count(longer)>count(partial),"authored longer fog range keeps more of the object");
rs(D3DRS_FOGEND,bits(.25f));auto depth=draw(512|2048|256);
p->ExSurfaceRelease();rs(D3DRS_FOGENABLE,0);rs(D3DRS_LIGHTING,0);rs(D3DRS_ZWRITEENABLE,0);
C(d->SetTexture(0,nullptr));C(d->SetTexture(1,nullptr));C(d->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE));
tss(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1);tss(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE);
struct Screen{float x,y,z,w;DWORD colour;};
Screen plane[]={{-.5f,-.5f,.8f,1,0xffffff40},{899.5f,-.5f,.8f,1,0xffffff40},{-.5f,599.5f,.8f,1,0xffffff40},{899.5f,599.5f,.8f,1,0xffffff40}};
C(d->BeginScene());C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,plane,sizeof(Screen)));C(d->EndScene());auto behind=pixels();
for(size_t i=0;i<depth.size();++i)R(depth[i]==background?behind[i]==0xffffff40:behind[i]==depth[i],"solar colour and depth holes agree");
C(D3DXSaveSurfaceToFileA(argv[1],D3DXIFF_PNG,target,nullptr,nullptr));
puts("PASS solar fog range, colour/depth, clear air, low settings and scope reset");
return 0;
