// Actual native meshes, textures and production mesh shader, with the retail
// depthless fog cover retained. Compare scheduling only; no fog tuning.
auto overlay=[&](unsigned alpha){
 struct Screen{float x,y,z,w;DWORD colour;};
 DWORD colour=(alpha<<24)|(background&0xffffff);
 Screen quad[]={{-.5f,-.5f,0,1,colour},{1919.5f,-.5f,0,1,colour},{-.5f,1079.5f,0,1,colour},{1919.5f,1079.5f,0,1,colour}};
 Check(d->SetVertexShader(nullptr));Check(d->SetPixelShader(nullptr));Check(d->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE));
 Check(d->SetRenderState(D3DRS_LIGHTING,0));Check(d->SetRenderState(D3DRS_FOGENABLE,0));
 Check(d->SetRenderState(D3DRS_ZENABLE,0));Check(d->SetRenderState(D3DRS_ZWRITEENABLE,0));
 Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,1));Check(d->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA));Check(d->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA));
 Check(d->SetTexture(0,nullptr));Check(d->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1));Check(d->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE));
 Check(d->SetTextureStageState(0,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1));Check(d->SetTextureStageState(0,D3DTSS_ALPHAARG1,D3DTA_DIFFUSE));
 Check(d->SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE));
 Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(Screen)));
};
auto triplet=[&](unsigned coverage,bool textured){
 Check(d->SetVertexShader(vs));Check(d->SetPixelShader(ps));
 Check(d->SetRenderState(D3DRS_ZENABLE,1));Check(d->SetRenderState(D3DRS_ZWRITEENABLE,1));Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,0));
 p[3]=textured?1.f:0.f;p[38]=v[38]=0;Set(v,8,0,5,1,1);
 Check(d->SetPixelShaderConstantF(0,p,12));Check(d->SetVertexShaderConstantF(0,v,10));
 for(int i=0;i<3;++i){Instance instance={};instance.centre[0]=v[0]+(i-1)*600;instance.centre[1]=v[1];instance.centre[2]=v[2]-1900;
  instance.centre[3]=240;instance.rotation[3]=1;instance.colour=0xff800000|(coverage<<8);
  Upload(models[i].instances,&instance,sizeof(instance));Check(d->SetTexture(0,models[i].texture));
  Check(renderer.Draw(d,models[i].mesh,models[i].instances,models[i].vertices,0,1));
 }
};
auto renderOrder=[&](unsigned alpha,unsigned coverage,int mode,bool textured){
 Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff182735,1,0));Check(d->BeginScene());
 if(mode==0)triplet(coverage,textured);
 overlay(alpha);
 if(mode==1)triplet(coverage,textured);
 Check(d->EndScene());return snapshot();
};
for(unsigned alpha:{0u,128u,255u})for(unsigned coverage:{64u,255u}){
 auto empty=renderOrder(alpha,coverage,2,true);
 auto before=renderOrder(alpha,coverage,0,true);
 if(alpha==255&&coverage==255){std::string file=std::string(argv[12])+"_covered.png";Check(D3DXSaveSurfaceToFileA(file.c_str(),D3DXIFF_PNG,target,nullptr,nullptr));}
 auto after=renderOrder(alpha,coverage,1,true);
 if(alpha==255&&coverage==255){std::string file=std::string(argv[12])+"_restored.png";Check(D3DXSaveSurfaceToFileA(file.c_str(),D3DXIFF_PNG,target,nullptr,nullptr));}
 auto noTexture=renderOrder(alpha,coverage,1,false);
 unsigned object=0,backgroundCount=0,textureDetails=0;
 std::set<DWORD> colours;
 for(size_t i=0;i<after.size();++i){
  if(after[i]==empty[i]&&noTexture[i]==empty[i]){Require(before[i]==empty[i],"fog background untouched by scheduling");++backgroundCount;}
  else{
   ++object;colours.insert(after[i]&0xffffff);textureDetails+=after[i]!=noTexture[i];
   if(alpha==255)Require(before[i]==empty[i],"old scheduling erases the mesh material completely");
   if(alpha==0)Require(before[i]==after[i],"without overlay both schedules agree");
  }
 }
 Require(object>3000&&colours.size()>100&&textureDetails>object*.7,"native material texture and lighting survive fog cover");
 Require(renderOrder(alpha,coverage,1,true)==after,"repeated material frame is stable");
 printf("PASS overlay alpha %u, coverage %u: %u object pixels, %zu surface colours, %u textured pixels, %u identical background pixels\n",
  alpha,coverage,object,colours.size(),textureDetails,backgroundCount);
}
