// Runs inside the D3D9 fixture, on the real atlas extracted from beast.cmp.
{
 float saved[103*4];memcpy(saved,pc,sizeof saved);
 auto bc=Compile(prefix+"#define SURFACE_BEAST 1\n#define SURFACE_NO_SHADOW 1\n"+source,"PSMain","ps_3_0");
 auto shadowCode=Compile(prefix+"#define SURFACE_BEAST 1\n"+source,"PSMain","ps_3_0");
 Need(bc==shadowCode,"BEAST has no hidden PCSS receiver variant");
 ID3DXBuffer* asmBuffer=nullptr;Check(D3DXDisassembleShader((DWORD*)bc.data(),FALSE,nullptr,&asmBuffer));
 std::string assembly((char*)asmBuffer->GetBufferPointer());asmBuffer->Release();
 FILE* asmFile=fopen("src/obj/beast_relief/bump_assembly.txt","wb");Need(asmFile!=nullptr,"assembly output");fwrite(assembly.data(),1,assembly.size(),asmFile);fclose(asmFile);
 auto occurrences=[&](const char* word){size_t count=0,at=0;while((at=assembly.find(word,at))!=std::string::npos){++count;at+=strlen(word);}return count;};
 Need(occurrences("texldd ")==5,"exactly four bump neighbours plus original diffuse");
 Need(occurrences("loop ")+occurrences("rep ")==1,"only the lighting loop remains, no depth march");
 IDirect3DPixelShader9* bp=nullptr;Check(d->CreatePixelShader((DWORD*)bc.data(),&bp));
 IDirect3DTexture9* atlas=nullptr;Check(D3DXCreateTextureFromFileA(d,"src/obj/beast_relief/atlas.dds",&atlas));
 d->SetTexture(0,atlas);pc[384]=1;pc[385]=1;pc[386]=0;pc[387]=0;pc[391]=0;
 V tile[6];memcpy(tile,quad,sizeof tile);
 for(auto& v:tile){v.u=.01f+v.u*.47f;v.v=.02f+v.v*.21f;}
 auto recessed=render(bp,tile,6);save("beast_bump");
 pc[385]=0;auto flatBeast=render(bp,tile,6);save("beast_flat");
 // A gentle bump affects lighting at grooves, rather than warping the whole texture.
 Need(changed(recessed,flatBeast)>W*H/10,"BEAST bump visible on original atlas");
 pc[385]=2;auto maximum=render(bp,tile,6);
 Need(changed(maximum,recessed)>W*H/100,"maximum BEAST strength retained");
 for(size_t i=0;i<maximum.size();++i)Need((maximum[i]>>24)==(flatBeast[i]>>24),"maximum strength preserves opacity");
 pc[385]=1;pc[387]=20;Need(changed(recessed,render(bp,tile,6))==0,"BEAST relief stationary");
 for(size_t i=0;i<recessed.size();++i)Need((recessed[i]>>24)==(flatBeast[i]>>24),"BEAST original opacity preserved");
 V distant[6];memcpy(distant,tile,sizeof tile);for(auto& v:distant){v.u*=20;v.v*=20;}
 auto farBeast=render(bp,distant,6);pc[385]=0;
 Need(changed(farBeast,render(bp,distant,6))==0,"subpixel BEAST relief fades completely");
 float oldLights=pc[19],oldAmbient[3]={pc[4],pc[5],pc[6]};pc[19]=0;pc[4]=pc[5]=pc[6]=1;
 auto unlit=render(bp,tile,6);pc[385]=1;
 Need(changed(unlit,render(bp,tile,6))==0,"bump cannot displace original texture coordinates");
 pc[19]=oldLights;for(int i=0;i<3;++i)pc[4+i]=oldAmbient[i];
 #include "beast_benchmark.h"
 d->SetTexture(0,textures[0]);atlas->Release();bp->Release();memcpy(pc,saved,sizeof saved);
 puts("PASS BEAST fixed five texture reads, no parallax/PCSS, visible bump and maximum strength, static UVs, opacity and subpixel fade");
}
