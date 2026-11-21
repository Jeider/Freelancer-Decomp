// Actual native meshes/materials: isolate optical attenuation from size/fade.
Set(v,0,0,0,0,0);Set(v,4,1080.f/1920,1,10000.f/9999,-10000.f/9999);
Set(v,6,10000,540,2,1-1.f/4194304);Set(v,7,0,1,10000,.001f);
Set(v,9,200,2700,2,.55f);Set(p,9,200,2700,2,.55f);p[32]=0;
auto scatterFrame=[&](float distance,int mode,bool textured){
 Instance a={};a.centre[2]=-distance;a.centre[3]=distance*.15f;a.rotation[3]=1;a.colour=0xff80ff00;
 Upload(models[0].instances,&a,sizeof(a));p[3]=textured?1.f:0.f;p[38]=v[38]=float(mode);
 Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));
 Check(d->BeginScene());draw(true);Check(d->EndScene());return snapshot();
};
double previousDetail=1e20;
for(float distance:{900.f,1700.f,2700.f,4200.f,5800.f}){
 auto clear=scatterFrame(distance,0,true),clearPlain=scatterFrame(distance,0,false);
 auto fog=scatterFrame(distance,2,true),plain=scatterFrame(distance,2,false);
 unsigned covered=0,sky=0,surviving=0;double detail=0,reference=0,survivingReference=0;
 std::set<DWORD> colours;
 for(size_t i=0;i<fog.size();++i){
  if(clear[i]==background&&clearPlain[i]==background){Require(fog[i]==background&&plain[i]==background,"surface fog never changes sky");++sky;continue;}
  ++covered;colours.insert(fog[i]);
  if(fog[i]!=background)++surviving;
  for(int c=0;c<3;++c){detail+=abs(int((fog[i]>>(c*8))&255)-int((plain[i]>>(c*8))&255));
   int difference=abs(int((clear[i]>>(c*8))&255)-int((clearPlain[i]>>(c*8))&255));
   reference+=difference;if(fog[i]!=background)survivingReference+=difference;}
 }
 Require(covered>8000&&sky>2000000,"stable projected object footprint");
 double ratio=detail/reference;
 Require(ratio<previousDetail && ratio>0.01,"texture contrast fades continuously with distance");previousDetail=ratio;
 Require(colours.size()>100,"broad shape survives without a flat fog silhouette");
 Require(fog==scatterFrame(distance,2,true),"surface fog is temporally stable");
#ifdef ASTEROID_FOG_COVERAGE_CHECK
 Require(detail/survivingReference>.50,"covered fog samples retain texture contrast");
 if(distance>=2700)Require(surviving<covered*.85,"distant fog reveals background through the mesh");
 printf("PASS mesh grid %.0f m: %.1f%% coverage, %.3f contrast per covered sample\n",distance,100.*surviving/covered,detail/survivingReference);
#endif
 printf("PASS surface scatter %.0f m: texture contrast %.4f, %zu colours, %u unchanged sky pixels\n",distance,ratio,colours.size(),sky);
}
// A clear exclusion increases optical reach rather than applying full fog inside it.
Set(p,9,200,12000,2,.55f);auto clearZone=scatterFrame(4200,2,true);
Set(p,9,200,2700,2,.55f);auto medium=scatterFrame(4200,2,true);
Require(clearZone!=medium,"authored exclusion fog range is respected");
// Side-by-side distance study: top has no object fog, bottom has surface scatter.
Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));Check(d->BeginScene());
for(int row=0;row<2;++row)for(int col=0;col<5;++col){
 const float distances[]={900,1700,2700,4200,5800};float distance=distances[col];
 Instance a={};a.centre[0]=(col-2)*.62f*distance;a.centre[1]=(row?-.40f:.40f)*distance;
 a.centre[2]=-distance;a.centre[3]=distance*.15f;a.rotation[3]=1;a.colour=0xff80ff00;
 Upload(models[0].instances,&a,sizeof(a));p[3]=1;p[38]=v[38]=row?2.f:0.f;draw(true);
}
Check(d->EndScene());std::string study=std::string(argv[12])+"_scatter.png";
Check(D3DXSaveSurfaceToFileA(study.c_str(),D3DXIFF_PNG,target,nullptr,nullptr));
