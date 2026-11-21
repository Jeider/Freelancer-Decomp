// Model the existing depth-clipped clouds with a coloured plane behind rocks.
// The retained depth explains why the pre-cover draw reappears as a flat blob.
auto cloudBehind=[&](){
 struct Screen{float x,y,z,w;DWORD colour;};
 Screen quad[]={{-.5f,-.5f,.999999f,1,0xff603010},{1919.5f,-.5f,.999999f,1,0xffd0a040},
                {-.5f,1079.5f,.999999f,1,0xff401808},{1919.5f,1079.5f,.999999f,1,0xff805020}};
 Check(d->SetVertexShader(nullptr));Check(d->SetPixelShader(nullptr));Check(d->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE));
 Check(d->SetRenderState(D3DRS_LIGHTING,0));Check(d->SetRenderState(D3DRS_FOGENABLE,0));
 Check(d->SetRenderState(D3DRS_ZENABLE,1));Check(d->SetRenderState(D3DRS_ZWRITEENABLE,0));Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,0));
 Check(d->SetTexture(0,nullptr));Check(d->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1));Check(d->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE));
 Check(d->SetTextureStageState(0,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1));Check(d->SetTextureStageState(0,D3DTSS_ALPHAARG1,D3DTA_DIFFUSE));
 Check(d->SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE));
 Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(Screen)));
};
auto physicalOrderFrame=[&](unsigned coverage,bool after){
 Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff182735,1,0));Check(d->BeginScene());
 if(!after)triplet(coverage,true);overlay(255);if(after)triplet(coverage,true);
 cloudBehind();Check(d->EndScene());return snapshot();
};
auto noRock=physicalOrderFrame(0,true);unsigned previousCoverage=0;
for(unsigned coverage:{0u,16u,64u,128u,255u}){
 auto old=physicalOrderFrame(coverage,false);
 if(coverage==255)Check(D3DXSaveSurfaceToFileA((std::string(argv[12])+"_physical_old.png").c_str(),D3DXIFF_PNG,target,nullptr,nullptr));
 auto fixed=physicalOrderFrame(coverage,true);
 if(coverage==255)Check(D3DXSaveSurfaceToFileA((std::string(argv[12])+"_physical_fixed.png").c_str(),D3DXIFF_PNG,target,nullptr,nullptr));
 std::set<DWORD> oldColours,newColours;unsigned covered=0;
 for(size_t i=0;i<fixed.size();++i){
  if(fixed[i]==noRock[i]){Require(old[i]==noRock[i],"clear samples have no residual silhouette");continue;}
  ++covered;oldColours.insert(old[i]);newColours.insert(fixed[i]);
 }
 Require(covered>=previousCoverage,"complete scene coverage remains monotonic");previousCoverage=covered;
 if(!coverage)Require(old==noRock&&fixed==noRock,"zero coverage completely disappears through the full order");
 else Require(oldColours.size()==1&&newColours.size()>100,"reproduce flat fog blob and preserve material with post-cover scheduling");
 printf("PASS physical order coverage %u: %u samples, %zu old fog colours / %zu corrected material colours\n",coverage,covered,oldColours.size(),newColours.size());
}
