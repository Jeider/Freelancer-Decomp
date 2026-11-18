// Included by the production-shader probe after device, pass and readback setup.
// The coloured spheres/depth map are controlled test geometry, not a game capture.
IDirect3DSurface9 *readColor=nullptr,*upload=nullptr;
Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&readColor,nullptr));
Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&upload,nullptr));
auto readPixels=[&](){
    Check(d->GetRenderTargetData(back,readColor));D3DLOCKED_RECT l;
    Check(readColor->LockRect(&l,nullptr,D3DLOCK_READONLY));std::vector<DWORD> pixels(W*H);
    for(unsigned y=0;y<H;++y)memcpy(pixels.data()+y*W,(char*)l.pBits+y*l.Pitch,W*4);
    Check(readColor->UnlockRect());return pixels;
};
auto rawVolume=[&](){
    Check(d->GetRenderTargetData(low,read));D3DLOCKED_RECT l;
    Check(read->LockRect(&l,nullptr,D3DLOCK_READONLY));std::vector<unsigned char> pixels(LW*LH*8);
    for(unsigned y=0;y<LH;++y)memcpy(pixels.data()+y*LW*8,(char*)l.pBits+y*l.Pitch,LW*8);
    Check(read->UnlockRect());return pixels;
};
auto pack=[](float const* rgb){DWORD color=0xff000000;
    for(int k=0;k<3;++k)color|=DWORD(Clamp(rgb[k],0,1)*255+.5f)<<(16-8*k);
    return color;
};
std::vector<unsigned char> mask(W*H);
auto scene=[&](bool legacy){
    D3DLOCKED_RECT dep,col;Check(depth->LockRect(0,&dep,nullptr,0));Check(upload->LockRect(&col,nullptr,0));
    for(unsigned y=0;y<H;++y)for(unsigned x=0;x<W;++x){
        float z=100000.f,rgb[3]={.035f,.045f,.06f};unsigned char object=0;
        for(unsigned j=0;j<3;++j){
            float dx=(float(x)-W*(.2f+.3f*j))/135.f,dy=(float(y)-H*.5f)/135.f;
            float r2=dx*dx+dy*dy;if(r2>=1)continue;
            float n=sqrtf(1-r2);float distances[]={600,1800,3600};z=distances[j]*(1-.12f*n);
            float light=.2f+.8f*Clamp(-.4f*dx-.5f*dy+.7f*n,0,1);
            bool check=(int((dx+1)*8)+int((dy+1)*8))%2!=0;
            float paint[3]={check?.38f:.12f,check?.35f:.17f,check?.28f:.2f};
            for(int k=0;k<3;++k)rgb[k]=paint[k]*light;
            if(legacy){
                // Existing linear surface fog, including the previous artistic form trial.
                float keep=Clamp((FixtureFogEnd-z)/(FixtureFogEnd-FixtureFogStart),0,1);
                float facing=Clamp((-dy+.35f)/1.35f,0,1),rim=powf(1-n,3)*facing;
                float shape=4*keep*(1-keep),tint=1+shape*(.55f*(2*facing-1)+.12f*rim);
                for(int k=0;k<3;++k)rgb[k]=rgb[k]*keep+FixtureFogRgb[k]*tint*(1-keep);
            }
            object=(unsigned char)(j+1);break;
        }
        mask[y*W+x]=object;
        ((float*)((char*)dep.pBits+y*dep.Pitch))[x]=c[0][0]+c[0][1]/z;
        ((DWORD*)((char*)col.pBits+y*col.Pitch))[x]=pack(rgb);
    }
    Check(depth->UnlockRect(0));Check(upload->UnlockRect());Check(d->UpdateSurface(upload,nullptr,back,nullptr));
    Check(d->BeginScene());pass(true);pass(false);Check(d->EndScene());return readPixels();
};
for(float distance:{50.f,600.f,1800.f,3600.f,10000.f}){
    setDepth(distance,false);Check(d->BeginScene());pass(true);Check(d->EndScene());auto t=transmission();
    printf("Existing walker profile, depth %.0f: T %.6f, variance %.6f\n",distance,t.first,t.second);
    if(distance==50)Require(t.first>.98,"near object remains clear");
}
// Surface detail at the native fog end must survive according to the existing volume,
// instead of being erased before the volume is composited.
setDepth(FixtureFogEnd+200,false);Check(d->BeginScene());pass(true);Check(d->EndScene());auto surfaceT=transmission();
std::vector<DWORD> black;
for(int white=0;white<2;++white){
    Check(d->SetRenderTarget(0,back));D3DVIEWPORT9 vp={0,0,W,H,0,1};Check(d->SetViewport(&vp));
    Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,white?0xffffffff:0xff000000,1,0));
    Check(d->BeginScene());pass(false);Check(d->EndScene());auto color=readPixels();
    if(!white)black=std::move(color);
    else{double contrast=0;
        for(size_t i=0;i<color.size();++i)for(int s:{0,8,16})contrast+=int((color[i]>>s)&255)-int((black[i]>>s)&255);
        contrast/=W*H*3.*255.;Require(std::abs(contrast-surfaceT.first)<.03,"object contrast matches existing fog transmission");
        Require(contrast>.005,"object detail survives beyond flat-fog boundary");
        printf("PASS surface contrast %.6f, ray transmission %.6f; native pre-fog contrast here is zero\n",contrast,surfaceT.first);
    }
}
for(int exclusion=0;exclusion<2;++exclusion){
    float saved[112][4];memcpy(saved,c,sizeof(c));
    if(exclusion){
        // Controlled spherical exclusion; its interior haze multiplier comes from
        // the installed fog_far and exclusion_density_scale. No profile edits.
        c[35][0]=1;c[37][3]=5;c[45][0]=c[53][1]=c[61][2]=1.f/5000;
        c[45][3]=FixtureExclusionScale-1;c[53][3]=5006;
    }
    auto before=scene(true);auto fogBefore=rawVolume();
    char path[1024];sprintf_s(path,"%s_before_%d.png",argv[4],exclusion);
    Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,back,nullptr,nullptr));
    auto after=scene(false);auto fogAfter=rawVolume();
    Require(fogBefore==fogAfter,"unchanged volume RGBA for identical geometry");
    unsigned background=0,changed=0;double difference[3]={};unsigned count[3]={};
    for(unsigned i=0;i<W*H;++i){
        if(!mask[i]){Require(before[i]==after[i],"background pixels unchanged");++background;}
        else{changed+=before[i]!=after[i];unsigned j=mask[i]-1;++count[j];
            for(int s:{0,8,16})difference[j]+=abs(int((before[i]>>s)&255)-int((after[i]>>s)&255));}
    }
    Require(changed>1000,"surface fog visibly changes object pixels");
    sprintf_s(path,"%s_after_%d.png",argv[4],exclusion);
    Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,back,nullptr,nullptr));
    Require(scene(false)==after,"stationary frame is deterministic");
    printf("PASS exclusion %d: %u background pixels identical; %u changed object pixels; object RGB differences %.3f / %.3f / %.3f\n",
        exclusion,background,changed,difference[0]/(3*count[0]),difference[1]/(3*count[1]),difference[2]/(3*count[2]));
    memcpy(c,saved,sizeof(c));
}
setDepth(1800,false);Check(d->BeginScene());pass(true);Check(d->EndScene());auto dense=transmission();
c[35][0]=1;c[37][3]=5;c[45][0]=c[53][1]=c[61][2]=1.f/5000;c[45][3]=FixtureExclusionScale-1;c[53][3]=5006;
Check(d->BeginScene());pass(true);Check(d->EndScene());auto clear=transmission();
Require(clear.first>dense.first+.05,"exclusion reduces fog on geometry");
printf("PASS exclusion object transmission %.6f -> %.6f\n",dense.first,clear.first);
puts("PASS production volume/composite, native cloud texture and unchanged installed walker profile; no game launch");
return 0;
