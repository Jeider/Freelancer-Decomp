// Sparse object depth versus the installed compositor and a fully sampled
// reference. Production shaders; controlled geometry, not a game screenshot.
IDirect3DSurface9 *readColor=nullptr,*upload=nullptr;
Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&readColor,nullptr));
Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&upload,nullptr));
auto pixels=[&](){Check(d->GetRenderTargetData(back,readColor));D3DLOCKED_RECT l;Check(readColor->LockRect(&l,nullptr,D3DLOCK_READONLY));std::vector<DWORD> p(W*H);
 for(unsigned y=0;y<H;++y)memcpy(p.data()+y*W,(char*)l.pBits+y*l.Pitch,W*4);Check(readColor->UnlockRect());return p;};
auto compositePixels=[&](bool repair){repairDepth=repair;Check(d->SetRenderTarget(0,back));Check(d->UpdateSurface(upload,nullptr,back,nullptr));
 Check(d->BeginScene());pass(false);Check(d->EndScene());return pixels();};
setDepth(1800,false);Check(d->SetRenderTarget(0,back));Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,0xff202327,1,0));
Check(d->BeginScene());pass(true);pass(false);Check(d->EndScene());auto expected=pixels();
unsigned long long backgroundPixels=0,oldBad=0,newBad=0;
for(int radius:{2,4,8,16})for(int coverage:{16,32,64}){
 std::vector<unsigned char> mask(W*H);D3DLOCKED_RECT dep,col;
 Check(depth->LockRect(0,&dep,nullptr,0));Check(upload->LockRect(&col,nullptr,0));
 for(unsigned y=0;y<H;++y)for(unsigned x=0;x<W;++x){
  int dx=int(x)%64-32,dy=int(y)%64-32;
  int a=2*abs(int(x%2)-int(y%2))+y%2;
  int b=2*abs(int(x/2%2)-int(y/2%2))+y/2%2;
  int k=2*abs(int(x/4%2)-int(y/4%2))+y/4%2;
  bool rock=dx*dx+dy*dy<radius*radius && 16*a+4*b+k<coverage;
  mask[y*W+x]=rock;
  ((float*)((char*)dep.pBits+y*dep.Pitch))[x]=rock?c[0][0]+c[0][1]/1800.f:1.f;
  ((DWORD*)((char*)col.pBits+y*col.Pitch))[x]=rock?0xff202327:0xff080a10;
 }
 Check(depth->UnlockRect(0));Check(upload->UnlockRect());
 Check(d->BeginScene());pass(true);Check(d->EndScene());
 auto before=compositePixels(false);
 char file[1024];
 if(radius==4&&coverage==32){sprintf_s(file,"%s_before.png",argv[4]);Check(D3DXSaveSurfaceToFileA(file,D3DXIFF_PNG,back,nullptr,nullptr));}
 auto after=compositePixels(true);
 if(radius==4&&coverage==32){sprintf_s(file,"%s_after.png",argv[4]);Check(D3DXSaveSurfaceToFileA(file,D3DXIFF_PNG,back,nullptr,nullptr));
  Require(compositePixels(true)==after,"stationary result is bit-identical");}
 unsigned count=0,bad[2]={};double sum[2]={};
 for(size_t i=0;i<after.size();++i){
  if(!mask[i]){Require(before[i]==after[i],"sky/cloud background is bit-identical to installed compositor");++backgroundPixels;continue;}
  ++count;
  for(int mode=0;mode<2;++mode){double diff=0;DWORD value=mode?after[i]:before[i];
   for(int shift:{0,8,16})diff+=abs(int((value>>shift)&255)-int((expected[i]>>shift)&255));
   diff/=3;sum[mode]+=diff;if(diff>12)++bad[mode];}
 }
 printf("radius %d coverage %d/64: %u object pixels; wrong fog %u -> %u (%.2f%% -> %.2f%%); mean RGB error %.3f -> %.3f\n",
  radius,coverage,count,bad[0],bad[1],100.*bad[0]/count,100.*bad[1]/count,sum[0]/count,sum[1]/count);
 if(bad[0]){Require(bad[1]<bad[0]*.1,"remove over 90 percent of severe surface fog errors");
  Require(sum[1]<sum[0]*.4 || sum[1]/count<.5,"reduce mean error by over 60 percent or below half an 8-bit level");}
 else Require(sum[1]<=sum[0]+.01,"opaque reference does not regress");
 oldBad+=bad[0];newBad+=bad[1];
 if(radius==8&&coverage==16){
  IDirect3DQuery9 *start=nullptr,*end=nullptr,*freq=nullptr,*disjoint=nullptr;
  Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&start));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&end));
  Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&freq));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&disjoint));
  std::vector<double>times[2];
  for(int frame=0;frame<20;++frame)for(int mode=0;mode<2;++mode){repairDepth=mode!=0;
   Check(d->BeginScene());Check(disjoint->Issue(D3DISSUE_BEGIN));Check(start->Issue(D3DISSUE_END));pass(false);
   Check(end->Issue(D3DISSUE_END));Check(disjoint->Issue(D3DISSUE_END));Check(freq->Issue(D3DISSUE_END));Check(d->EndScene());
   UINT64 a,b,hz;BOOL invalid;Query(end,&b,8);Query(start,&a,8);Query(freq,&hz,8);Query(disjoint,&invalid,4);
   if(frame>=4&&!invalid&&hz)times[mode].push_back(double(b-a)*1000/hz);
  }
  for(int mode=0;mode<2;++mode){Require(!times[mode].empty(),"GPU timing");std::sort(times[mode].begin(),times[mode].end());
   printf("Composite GPU %s: median %.3f ms, p95 %.3f ms (1920x1080, sparse object coverage %.2f%%)\n",
    mode?"repaired":"installed",times[mode][times[mode].size()/2],times[mode][(times[mode].size()-1)*95/100],100.*count/(W*H));}
  start->Release();end->Release();freq->Release();disjoint->Release();
 }
}
Require(oldBad>10000&&newBad<oldBad/20,"fixture reproduces and substantially fixes the installed issue");
printf("PASS %llu unchanged background pixels; severe object errors %llu -> %llu; production volume/profile unchanged\n",backgroundPixels,oldBad,newBad);
return 0;
