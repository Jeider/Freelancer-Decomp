// Real GPU validation of the authored Dyson brick texture and lightweight profile.
{
 float saved[103*4];memcpy(saved,pc,sizeof saved);
 const std::string variant=prefix+"#define SURFACE_NOMAD_LIGHT 1\n";
 auto bytecode=Compile(variant+source,"PSMain","ps_3_0");
 Need(bytecode==Compile(variant+"#define SURFACE_NO_SHADOW 1\n"+source,"PSMain","ps_3_0"),"Dyson has no PCSS variant");
 ID3DXBuffer* disassembly=nullptr;Check(D3DXDisassembleShader((DWORD*)bytecode.data(),FALSE,nullptr,&disassembly));
 std::string assembly((char*)disassembly->GetBufferPointer());disassembly->Release();
 auto count=[&](const char* word){size_t n=0,at=0;while((at=assembly.find(word,at))!=std::string::npos){++n;at+=strlen(word);}return n;};
 Need(count("texldd ")==6,"Dyson four height samples, original diffuse and optional authored detail");
 Need(count("loop ")+count("rep ")==1,"only lighting loop; no parallax march");
 Need(assembly.find("s13")==std::string::npos && assembly.find("s14")==std::string::npos,"no organic or rock atlas samples");
 if(getenv("DYSON_ONLY")) {
  auto previous=Read("src/obj/beast_relief/before_dyson_bump.hlsl");
  for(const char* define:{""}) {
   std::string unchanged=prefix+"#define SURFACE_NO_SHADOW 1\n"+define;
   Need(Compile(unchanged+source,"PSMain","ps_3_0")==Compile(unchanged+previous,"PSMain","ps_3_0"),"Lair pixel bytecode unchanged");
  }
 }
 d->SetTexture(0,textures[2]);D3DSURFACE_DESC desc={};Check(textures[2]->GetLevelDesc(0,&desc));
 pc[384]=2;pc[385]=1;pc[386]=0;pc[387]=0;pc[391]=0;
 pc[408]=1.f/desc.Width;pc[409]=1.f/desc.Height;pc[410]=pc[411]=0;
 auto bump=render(ps[3],quad,6);save("dyson_bump");
 pc[385]=0;auto flat=render(ps[3],quad,6);save("dyson_flat");
 Need(changed(bump,flat)>W*H/100,"Dyson relief visible on real brick texture");
 pc[385]=2;auto strong=render(ps[3],quad,6);Need(changed(bump,strong)>W*H/100,"Dyson strength control visible");
 pc[385]=1;pc[387]=123;Need(changed(bump,render(ps[3],quad,6))==0,"Dyson brick normal stationary");
 for(size_t i=0;i<bump.size();++i)Need((bump[i]>>24)==(flat[i]>>24),"authored alpha unchanged");
 V distantTile[6];memcpy(distantTile,quad,sizeof distantTile);for(auto& v:distantTile){v.u*=128;v.v*=128;}
 auto farBump=render(ps[3],distantTile,6);pc[385]=0;Need(changed(farBump,render(ps[3],distantTile,6))==0,"subpixel relief fades without distance shader switch");
 // Native UV/detail multiplication and emission remain intact with lighting removed.
 float lights=pc[19],ambient[3]={pc[4],pc[5],pc[6]};pc[19]=0;pc[4]=pc[5]=pc[6]=1;
 for(float op:{4.f,5.f,7.f}) {
  pc[388]=op;pc[391]=1;pc[385]=0;auto unlit=render(ps[3],quad,6);
  pc[385]=2;Need(changed(unlit,render(ps[3],quad,6))==0,"detail/emission and diffuse UV preserved at maximum strength");
 }
 pc[19]=lights;for(int i=0;i<3;++i)pc[4+i]=ambient[i];pc[391]=0;
 // Relative derivative validity must not reintroduce the old close-up cutoff.
 pc[385]=1;pc[387]=0;
 for(int i:{0,5,10}){vc[i]=.001f;vc[16+i]=1000;}
 auto close=render(ps[3],quad,6);
 size_t largeErrors=0;for(size_t i=0;i<close.size();++i)for(int s:{0,8,16})largeErrors+=abs(int((close[i]>>s)&255)-int((bump[i]>>s)&255))>2;
 Need(largeErrors<W*H/100,"close-up tangent frame stays stable");
 for(int i:{0,5,10})vc[i]=vc[16+i]=1;
 d->SetTexture(0,textures[0]);memcpy(pc,saved,sizeof saved);
 puts("PASS Dyson one-layer bump: bounded samples, no organic/PCSS, real texture relief, strength, alpha, authored detail, static UV, far fade and close-up frame");
}
