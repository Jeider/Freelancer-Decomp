// Included only in the isolated cost fixture. No production shader edits.
template<class T> static void QueryResult(IDirect3DQuery9* q,T& value){
 HRESULT hr;ULONGLONG start=GetTickCount64();
 while((hr=q->GetData(&value,sizeof value,D3DGETDATA_FLUSH))==S_FALSE){Need(GetTickCount64()-start<30000,"GPU query timeout");Sleep(0);}Check(hr);
}
static void ReplaceOnce(std::string& text,const char* before,const char* after){
 auto at=text.find(before);Need(at!=std::string::npos,before);text.replace(at,strlen(before),after);
}
static int BenchmarkNomad(IDirect3DDevice9* d,const std::string& source,IDirect3DVertexShader9* vs,
 IDirect3DPixelShader9** production,float* vc,float* pc,const V* quad,int W,int H){
 const char* prefix="#define SURFACE_NOMAD 1\n#define SURFACE_NO_SHADOW 1\n";
 std::string noPom=source,six=source;
 ReplaceOnce(noPom,"#ifndef SURFACE_NOMAD_LIGHT","#if 0");
 ReplaceOnce(six,"float2 stepUv=shift/12;","float2 stepUv=shift/6;");
 ReplaceOnce(six,"k<12","k<6");
 ReplaceOnce(six,"layer+=1.0/12;","layer+=1.0/6;");
 ReplaceOnce(six,"(layer-1.0/12)","(layer-1.0/6)");
 IDirect3DPixelShader9 *noPomPs=nullptr,*sixPs=nullptr;
 auto aCode=Compile(prefix+noPom,"PSMain","ps_3_0");Check(d->CreatePixelShader((DWORD*)aCode.data(),&noPomPs));
 aCode=Compile(prefix+six,"PSMain","ps_3_0");Check(d->CreatePixelShader((DWORD*)aCode.data(),&sixPs));
 // Synthetic blocked/unblocked far depth map, full PCSS branch. This measures
 // receiving cost only, not shadow-map generation or a captured game scene.
 IDirect3DTexture9 *lit=nullptr,*blocked=nullptr;
 for(int i=0;i<2;++i){auto** out=i?&blocked:&lit;Check(d->CreateTexture(1024,1024,1,0,D3DFMT_R32F,D3DPOOL_MANAGED,out,nullptr));
  D3DLOCKED_RECT l;Check((*out)->LockRect(0,&l,nullptr,0));for(int y=0;y<1024;++y)for(int x=0;x<1024;++x)
   ((float*)((char*)l.pBits+y*l.Pitch))[x]=i?.25f+.015f*sin(x*.03f)*cos(y*.04f):1.f;Check((*out)->UnlockRect(0));}
 for(int slot:{8,9,11,12}){d->SetTexture(slot,blocked);for(auto s:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER})d->SetSamplerState(slot,s,D3DTEXF_POINT);
  d->SetSamplerState(slot,D3DSAMP_MIPFILTER,D3DTEXF_NONE);d->SetSamplerState(slot,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);d->SetSamplerState(slot,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);}
 D3DXMATRIX id;D3DXMatrixIdentity(&id);memcpy(pc+208,&id,64);memcpy(pc+224,&id,64);
 pc[241]=pc[380]=1.f/1024;pc[242]=4500;pc[243]=5000;pc[244]=0;pc[245]=0;pc[246]=1;
 pc[252]=300;pc[253]=240;pc[254]=300;pc[255]=10000;
 pc[288]=tan(3.14159265f/180);pc[289]=16;pc[290]=32;pc[291]=.85f;
 pc[292]=pc[293]=.05f;pc[294]=.5f;pc[296]=pc[297]=100;
 pc[304]=500;pc[305]=1;pc[306]=pc[307]=4;
 // One sun plus up to seven point lights, all within range.
 pc[52]=pc[53]=0;pc[54]=1;
 for(int i=1;i<8;++i){float* l=pc+48+i*20;l[0]=sin(float(i));l[1]=cos(float(i));l[2]=-1;l[3]=1;l[7]=100;
  l[8]=.18f;l[9]=.14f;l[10]=.12f;l[12]=l[13]=l[14]=.3f;l[16]=1;}
 struct Mode{const char* name;IDirect3DPixelShader9* ps;int lights,shadow;};
 Mode modes[]={{"POM12_1light",production[1],1,0},{"no_POM_1light",noPomPs,1,0},
  {"POM6_1light",sixPs,1,0},{"POM12_8lights",production[1],8,0},
  {"POM12_shadow_lit_16_32",production[0],1,1},{"POM12_shadow_blocked_16_32",production[0],1,2},
  {"POM12_shadow_blocked_4_4",production[0],1,3}};
 IDirect3DQuery9 *begin=nullptr,*end=nullptr,*freq=nullptr,*disjoint=nullptr,*occ=nullptr;
 Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&begin));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&end));
 Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&freq));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&disjoint));Check(d->CreateQuery(D3DQUERYTYPE_OCCLUSION,&occ));
 for(int scene=0;scene<3;++scene){
  V verts[6];memcpy(verts,quad,sizeof verts);for(auto& v:verts){if(scene==0){v.x*=.5f;v.y*=.5f;}if(scene==2){v.nx=.95f;v.nz=-.31225f;v.u=.45f+v.u*.02f;v.v=.45f+v.v*.02f;}}
  IDirect3DVertexBuffer9* vb=nullptr;Check(d->CreateVertexBuffer(sizeof verts,0,0,D3DPOOL_MANAGED,&vb,nullptr));
  void* data=nullptr;Check(vb->Lock(0,0,&data,0));memcpy(data,verts,sizeof verts);Check(vb->Unlock());d->SetStreamSource(0,vb,0,sizeof(V));
  auto setup=[&](int mode){auto& m=modes[mode];d->SetVertexShader(vs);d->SetPixelShader(m.ps);pc[19]=(float)m.lights;pc[240]=m.shadow?1.f:0;
   pc[289]=m.shadow==3?4.f:16.f;pc[290]=m.shadow==3?4.f:32.f;d->SetTexture(9,m.shadow==1?lit:blocked);
   Check(d->SetVertexShaderConstantF(0,vc,17));Check(d->SetPixelShaderConstantF(0,pc,103));};
  auto draw=[&](){Check(d->DrawPrimitive(D3DPT_TRIANGLELIST,0,2));};
  setup(0);d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0,1,0);d->BeginScene();occ->Issue(D3DISSUE_BEGIN);draw();occ->Issue(D3DISSUE_END);d->EndScene();DWORD fragments=0;QueryResult(occ,fragments);
  printf("SCENE %dx%d %s coverage %.2f%%\n",W,H,scene==0?"quarter":scene==1?"full":"close_grazing",100.*fragments/(W*H));
  const int repeats=8,rounds=11,modeCount=sizeof(modes)/sizeof(*modes);std::vector<double> times[modeCount];
  for(int round=0;round<rounds;++round)for(int order=0;order<modeCount;++order){int mode=(round+order)%modeCount;setup(mode);
   Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0,1,0));Check(d->BeginScene());draw();
   disjoint->Issue(D3DISSUE_BEGIN);begin->Issue(D3DISSUE_END);for(int n=0;n<repeats;++n)draw();
   end->Issue(D3DISSUE_END);disjoint->Issue(D3DISSUE_END);freq->Issue(D3DISSUE_END);Check(d->EndScene());
   UINT64 a=0,b=0,hz=0;BOOL bad=TRUE;QueryResult(end,b);QueryResult(begin,a);QueryResult(freq,hz);QueryResult(disjoint,bad);
   if(round>=3 && !bad && hz && b>=a)times[mode].push_back(double(b-a)*1000/hz/repeats);
  }
  for(int i=0;i<modeCount;++i){auto& t=times[i];Need(t.size()>=6,"timestamp samples");std::sort(t.begin(),t.end());
   printf("  %-32s median %.4f ms p10 %.4f p90 %.4f\n",modes[i].name,t[t.size()/2],t[(t.size()-1)/10],t[(t.size()-1)*9/10]);}
  d->SetStreamSource(0,nullptr,0,0);vb->Release();
 }
 puts("GPU timestamps; 8 retained interleaved samples, 8 draws/sample; hot cache; isolated material cost, NOT game FPS.");
 return 0;
}
