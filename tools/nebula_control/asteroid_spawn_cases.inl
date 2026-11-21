// Material and depth must survive the whole spawn, including the switch to the
// ordinary opaque draw. The sky never receives the object's fog/colour.
for(auto&vertex:q){vertex.nx=0;vertex.ny=0;vertex.nz=-1;}
C(base.Texture->LockRect(0,&lock,0,0));
for(int y=0;y<4;++y)for(int x=0;x<4;++x)((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=((x+y)&1)?0xbfe0c080:0xbf403020;
base.Texture->UnlockRect(0);
auto framePixels=[&](){C(d->GetRenderTargetData(target,read));C(read->LockRect(&lock,0,D3DLOCK_READONLY));std::vector<DWORD> result(900*600);
 for(int y=0;y<600;++y)memcpy(result.data()+y*900,(char*)lock.pBits+y*lock.Pitch,900*4);read->UnlockRect();return result;};
const DWORD background=0xff112233;
auto spawnFrame=[&](unsigned flags,bool active){
 p->ExSurfaceRelease();C(p->SetLocalShadowReceiver(flags));rs(D3DRS_ZENABLE,1);rs(D3DRS_ZWRITEENABLE,1);rs(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
 C(d->Clear(0,0,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));C(d->BeginScene());
 bool actual=p->ExSurfaceBegin();R(actual==active,"spawn preserves a valid material route");
 C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(V)));if(actual)p->ExSurfaceEnd();C(d->EndScene());return framePixels();
};
for(int mode=0;mode<4;++mode){
 // The real close server rocks use the enhanced rock route, whereas distant
 // rocks and disabled enhancements use the native-lighting variant above.
 if(mode==3){e->RockClass=1;e->RockDetail=base.Texture;e->bRockEnabled=true;e->RockRadius=35;}
 e->bSurfaceEnabled=mode!=2;rs(D3DRS_FOGENABLE,mode!=1);rs(D3DRS_FOGSTART,bits(0));rs(D3DRS_FOGEND,bits(1));
 unsigned scope=mode==0?768:mode==3?512:256;
 auto reference=spawnFrame(scope,mode==0||mode==3);
 std::vector<DWORD> previous;unsigned previousCount=0;
 for(unsigned opacity:{0u,16u,64u,128u,192u,254u,255u}){
  auto current=spawnFrame(scope|1024u|(opacity<<16),true);unsigned count=0;
  for(size_t i=0;i<current.size();++i){
   if(current[i]==background)continue;++count;
   R(reference[i]!=background && delta(current[i],reference[i])<=1,"surviving pixels retain texture/light/fog at every opacity");
   if(!previous.empty()&&previous[i]!=background)R(delta(previous[i],current[i])<=1,"existing covered samples never flash");
  }
  R(count>=previousCount,"spawn coverage increases monotonically");
  if(opacity==0)R(count==0,"new rock starts invisible");
  if(opacity==255){R(count>10000,"spawn reaches visible mesh coverage");
   for(size_t i=0;i<current.size();++i)R((current[i]==background)==(reference[i]==background),"opaque boundary has identical silhouette");}
  R(current==spawnFrame(scope|1024u|(opacity<<16),true),"no temporal shimmer while stationary");
  if(mode==0 && opacity==128){
   p->ExSurfaceRelease();rs(D3DRS_FOGENABLE,0);rs(D3DRS_LIGHTING,0);rs(D3DRS_ZWRITEENABLE,0);
   C(d->SetTexture(0,nullptr));C(d->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE));
   C(d->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1));C(d->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE));
   struct Screen{float x,y,z,w;DWORD colour;};Screen plane[]={{-.5f,-.5f,.8f,1,0xff00ff00},{899.5f,-.5f,.8f,1,0xff00ff00},{-.5f,599.5f,.8f,1,0xff00ff00},{899.5f,599.5f,.8f,1,0xff00ff00}};
   C(d->BeginScene());C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,plane,sizeof(Screen)));C(d->EndScene());auto depth=framePixels();
   for(size_t i=0;i<current.size();++i)R(current[i]==background?depth[i]==0xff00ff00:depth[i]==current[i],"spawn colour and scene depth use the same coverage");
   rs(D3DRS_FOGENABLE,1);rs(D3DRS_LIGHTING,1);C(d->SetFVF(fvf));C(d->SetTexture(0,base.Texture));
   tss(0,D3DTSS_COLOROP,D3DTOP_MODULATE);tss(0,D3DTSS_COLORARG1,D3DTA_TEXTURE);
  }
  previous=std::move(current);previousCount=count;
 }
 printf("PASS spawn mode %d: texture, fog, native fallback, stable fade and opaque endpoint\n",mode);
}
C(p->SetLocalShadowReceiver(0));R(e->SurfaceSpawnCoverage<0,"spawn scope clears for the next object");
e->bSurfaceEnabled=true;e->RockClass=0;e->RockDetail=nullptr;
