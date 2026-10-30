if(getenv("BEAST_BENCH")) {
 auto beforeSimplify=Read("src/obj/beast_relief/before_simplify.hlsl");
 for(const char* define:{"", "#define SURFACE_NOMAD_LIGHT 1\n"}) {
  std::string variant=prefix+"#define SURFACE_NO_SHADOW 1\n"+define;
  Need(Compile(variant+source,"PSMain","ps_3_0")==Compile(variant+beforeSimplify,"PSMain","ps_3_0"),"Dyson and Lair bytecode unchanged by BEAST simplification");
 }
 auto previous=Compile(prefix+"#define SURFACE_BEAST 1\n#define SURFACE_NO_SHADOW 1\n"+beforeSimplify,"PSMain","ps_3_0");
 IDirect3DPixelShader9* old=nullptr;Check(d->CreatePixelShader((DWORD*)previous.data(),&old));
 auto simpleCode=Compile(prefix+"#define SURFACE_BEAST 1\n#define SURFACE_NO_SHADOW 1\n"+Read("src/obj/beast_relief/before_medium.hlsl"),"PSMain","ps_3_0");
 IDirect3DPixelShader9* simple=nullptr;Check(d->CreatePixelShader((DWORD*)simpleCode.data(),&simple));
 IDirect3DQuery9 *begin=nullptr,*end=nullptr,*frequency=nullptr,*disjoint=nullptr;
 Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&begin));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&end));
 Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&frequency));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&disjoint));
 auto result=[](IDirect3DQuery9* q,void* data,DWORD bytes){HRESULT hr;ULONGLONG start=GetTickCount64();
  while((hr=q->GetData(data,bytes,D3DGETDATA_FLUSH))==S_FALSE){Need(GetTickCount64()-start<30000,"timestamp timeout");Sleep(0);}Check(hr);};
 pc[385]=2;pc[387]=0;
 IDirect3DVertexBuffer9* vb=nullptr;Check(d->CreateVertexBuffer(sizeof tile,0,0,D3DPOOL_MANAGED,&vb,nullptr));
 void* buffer=nullptr;Check(vb->Lock(0,0,&buffer,0));memcpy(buffer,tile,sizeof tile);Check(vb->Unlock());
 d->SetStreamSource(0,vb,0,sizeof(V));d->SetVertexShaderConstantF(0,vc,17);d->SetPixelShaderConstantF(0,pc,103);
 std::vector<double> timings[3];
 for(int round=0;round<12;++round)for(int order=0;order<3;++order){int mode=(round+order)%3;
  d->SetPixelShader(mode==0?old:mode==1?simple:bp);Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0,1,0));Check(d->BeginScene());
  Check(d->DrawPrimitive(D3DPT_TRIANGLELIST,0,2));disjoint->Issue(D3DISSUE_BEGIN);begin->Issue(D3DISSUE_END);
  for(int i=0;i<16;++i)Check(d->DrawPrimitive(D3DPT_TRIANGLELIST,0,2));
  end->Issue(D3DISSUE_END);disjoint->Issue(D3DISSUE_END);frequency->Issue(D3DISSUE_END);Check(d->EndScene());
  UINT64 a=0,b=0,hz=0;BOOL bad=TRUE;result(end,&b,sizeof b);result(begin,&a,sizeof a);result(frequency,&hz,sizeof hz);result(disjoint,&bad,sizeof bad);
  if(round>=4 && !bad && hz && b>=a)timings[mode].push_back(double(b-a)*1000/hz/16);
 }
 for(int mode=0;mode<3;++mode){auto& t=timings[mode];Need(t.size()>=6,"GPU timing samples");std::sort(t.begin(),t.end());
  printf("BEAST %dx%d %s: median %.4f ms per fullscreen draw (no local shadows, strength 2)\n",W,H,mode==0?"previous Sobel (9 reads)":mode==1?"original simple bump (5 reads)":"current simple bump (5 reads)",t[t.size()/2]);}
 puts("Isolated GPU material cost; not whole-scene FPS.");
 d->SetStreamSource(0,nullptr,0,0);vb->Release();old->Release();simple->Release();begin->Release();end->Release();frequency->Release();disjoint->Release();
}
