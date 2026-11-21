IDirect3DSurface9 *readColor=nullptr,*upload=nullptr;
Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&readColor,nullptr));
Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&upload,nullptr));
auto pixels=[&](){Check(d->GetRenderTargetData(back,readColor));D3DLOCKED_RECT l;Check(readColor->LockRect(&l,nullptr,D3DLOCK_READONLY));std::vector<DWORD> p(W*H);
 for(unsigned y=0;y<H;++y)memcpy(p.data()+y*W,(char*)l.pBits+y*l.Pitch,W*4);Check(readColor->UnlockRect());return p;};
std::vector<unsigned char>mask(W*H);
auto draw=[&](int coverage){D3DLOCKED_RECT dep,col;Check(depth->LockRect(0,&dep,nullptr,0));Check(upload->LockRect(&col,nullptr,0));
 for(unsigned y=0;y<H;++y)for(unsigned x=0;x<W;++x){int dx=int(x)%160-80,dy=int(y)%160-80;
  int a=2*abs(int(x%2)-int(y%2))+y%2,b=2*abs(int(x/2%2)-int(y/2%2))+y/2%2,k=2*abs(int(x/4%2)-int(y/4%2))+y/4%2;
  bool rock=dx*dx+dy*dy<35*35&&16*a+4*b+k<coverage;mask[y*W+x]=rock;
  ((float*)((char*)dep.pBits+y*dep.Pitch))[x]=rock?c[0][0]+c[0][1]/3500.f:1.f;
  ((DWORD*)((char*)col.pBits+y*col.Pitch))[x]=rock?(((x/4+y/4)%2)?0xff453017:0xff765430):0xff965a14;
 }
 Check(depth->UnlockRect(0));Check(upload->UnlockRect());Check(d->SetRenderTarget(0,back));Check(d->UpdateSurface(upload,nullptr,back,nullptr));
 Check(d->BeginScene());pass(true);pass(false);Check(d->EndScene());return pixels();};
auto sky=draw(0);
char file[1024];sprintf_s(file,"%s_sky.png",argv[4]);Check(D3DXSaveSurfaceToFileA(file,D3DXIFF_PNG,back,nullptr,nullptr));
for(int coverage:{48,32,16,4,0}){
 auto result=draw(coverage);unsigned skyCount=0,bad=0;double error=0;
 for(size_t i=0;i<result.size();++i)if(!mask[i]){++skyCount;int delta=0;
  for(int shift:{0,8,16})delta=(std::max)(delta,abs(int((result[i]>>shift)&255)-int((sky[i]>>shift)&255)));
  if(delta>10)++bad;error+=delta;
 }
 printf("coverage %d/64: %u cloud pixels changed >10/255; mean error %.4f over %u sky pixels\n",coverage,bad,error/skyCount,skyCount);
 sprintf_s(file,"%s_grid_%d.png",argv[4],coverage);Check(D3DXSaveSurfaceToFileA(file,D3DXIFF_PNG,back,nullptr,nullptr));
}
return 0;
