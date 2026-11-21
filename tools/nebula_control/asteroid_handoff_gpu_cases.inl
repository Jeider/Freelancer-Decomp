// The same real mesh and shader before/after physics activation. No near fade.
Set(v,7,0,1,4500,1.f/1500);Set(v,0,0,0,0,0);Set(p,9,200,2700,0,.55f);v[38]=0;
auto handoffFrame=[&](float distance,float fog){
    Instance r={};r.centre[2]=-distance;r.centre[3]=models[0].radius;r.rotation[3]=1;r.colour=0xff80ff00;
    Upload(models[0].instances,&r,sizeof(r));p[38]=v[38]=fog;
    Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));
    Check(d->BeginScene());draw(true);Check(d->EndScene());return snapshot();
};
for(float distance:{300.f,899.f,1700.f,2999.f,3000.f,3001.f,3600.f,4499.f,5500.f}){
    auto before=handoffFrame(distance,0);auto after=handoffFrame(distance,0);
    Require(before==after,"activating/suspending physics preserves the complete mesh image");
    unsigned count=0;std::set<DWORD> colours;
    for(auto pixel:before)if(pixel!=background){++count;colours.insert(pixel);}
    if(distance<4500)Require(count>10&&colours.size()>8,"native textured mesh remains visible through all near thresholds");
    else Require(count>0,"far fade still has a few surviving samples before 6 km");
    printf("PASS procedural clear air %.0f m: %u pixels, %zu colours, identical physics handoff\n",distance,count,colours.size());
}
Require(handoffFrame(1800,2)!=handoffFrame(1800,0),"fog acts on the proxy only when the camera is in nebula");
handoffFrame(6001,0);Require(pixels()==0,"only the 6 km far boundary dissolves the mesh");

auto spinRock=ProceduralAsteroids::Generate(ProceduralAsteroids::Id(0,0,0,0),802,3);
Instance spinInstance={};spinInstance.centre[2]=-300;spinInstance.centre[3]=models[0].radius;
memcpy(spinInstance.rotation,spinRock.rotation,16);spinInstance.colour=0xff80ffff;
Upload(models[0].instances,&spinInstance,sizeof(spinInstance));
auto spinFrame=[&](float clock){float half=clock*ProceduralAsteroids::SpinRate*.5f;Set(v,10,sinf(half),cosf(half),0,0);
 Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));Check(d->BeginScene());draw(true);Check(d->EndScene());return snapshot();};
auto startSpin=spinFrame(0),gpuSpin=spinFrame(27);Require(startSpin!=gpuSpin,"GPU spin changes the image without updating instance bytes");
ProceduralAsteroids::Spin(spinInstance.rotation,27);spinInstance.colour&=~255u;
Upload(models[0].instances,&spinInstance,sizeof(spinInstance));auto cpuSpin=spinFrame(27);
unsigned mismatched=0;for(size_t n=0;n<cpuSpin.size();++n)if(cpuSpin[n]!=gpuSpin[n])++mismatched;
Require(mismatched<50,"GPU and physics quaternion spin agree at handoff");
Require(cpuSpin==spinFrame(51),"active body does not receive a second GPU spin");
printf("PASS spin: shader-only motion; CPU/GPU handoff differs at %u pixels; active body not double-rotated\n",mismatched);

for(auto& model:models)model.data.clear();
float proceduralEye[3]={30000,0,20000};unsigned proceduralCount=0,nearCount=0;
ProceduralAsteroids::Around(proceduralEye,6000,802,3,[&](auto const& rock){
    Instance r={};double distance2=0;for(int k=0;k<3;++k){r.centre[k]=rock.position[k]-proceduralEye[k];distance2+=r.centre[k]*r.centre[k];}
    r.centre[3]=models[rock.model].radius;memcpy(r.rotation,rock.rotation,16);r.colour=rock.colour|0xff00|(distance2>3000.*3000.?255u:0u);
    models[rock.model].data.push_back(r);++proceduralCount;if(distance2<=3000.*3000.)++nearCount;
});
for(auto& model:models){model.instances->Release();
    Check(d->CreateVertexBuffer(unsigned(model.data.size()*sizeof(Instance)),D3DUSAGE_WRITEONLY,0,D3DPOOL_MANAGED,&model.instances,nullptr));
    Upload(model.instances,model.data.data(),unsigned(model.data.size()*sizeof(Instance)));
}
times.clear();p[38]=v[38]=0;
for(int frame=0;frame<40;++frame){
    Set(v,10,sinf(frame*.001f),cosf(frame*.001f),0,0);
    for(auto& model:models){size_t first=model.data.size(),last=0;
        for(size_t n=0;n<model.data.size();++n)if(!(model.data[n].colour&255u)){
            ProceduralAsteroids::Spin(model.data[n].rotation,1.f/60);first=(std::min)(first,n);last=n+1;}
        if(last){void* to=nullptr;unsigned offset=unsigned(first*sizeof(Instance)),bytes=unsigned((last-first)*sizeof(Instance));
            Check(model.instances->Lock(offset,bytes,&to,0));memcpy(to,model.data.data()+first,bytes);Check(model.instances->Unlock());}
    }
    Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));Check(d->BeginScene());
    Check(disjoint->Issue(D3DISSUE_BEGIN));Check(start->Issue(D3DISSUE_END));draw(false);
    Check(end->Issue(D3DISSUE_END));Check(disjoint->Issue(D3DISSUE_END));Check(freq->Issue(D3DISSUE_END));Check(d->EndScene());
    UINT64 a=0,b=0,hz=0;BOOL bad=1;ReadQuery(end,&b,8);ReadQuery(start,&a,8);ReadQuery(freq,&hz,8);ReadQuery(disjoint,&bad,4);
    if(frame>=8&&!bad&&hz)times.push_back(double(b-a)*1000/hz);
}
Require(!times.empty()&&pixels()>5000,"full-density procedural field is visible");std::sort(times.begin(),times.end());
printf("PASS procedural GPU: %u proxies, %u within 3 km; clear air 1920x1080 median %.3f ms p95 %.3f ms\n",
       proceduralCount,nearCount,times[times.size()/2],times[(times.size()-1)*95/100]);
Check(D3DXSaveSurfaceToFileA(argv[12],D3DXIFF_PNG,target,nullptr,nullptr));
#ifdef ASTEROID_DECOR_ONLY_CHECK
Set(v,10,0,1,0,0);handoffFrame(5500,0);unsigned fadedFar=pixels();
Set(v,10,0,1,1,0);
for(float distance:{300.f,999.f,1001.f,1999.f,2001.f,3000.f,5500.f,5999.f}){
 auto clear=handoffFrame(distance,0);auto native=handoffFrame(distance,1);auto shaped=handoffFrame(distance,2);
 Require(clear==native&&clear==shaped,"decor diagnostic: no fog cutoff or fog coverage on meshes");
 Require(pixels()>0,"decor diagnostic: intact geometry throughout 6 km reach");
 if(distance==5500)Require(pixels()>fadedFar,"decor diagnostic removes distance dissolve");
}
handoffFrame(6001,0);Require(pixels()==0,"decor diagnostic stays inside resident-cache reach");
for(auto& model:models){for(auto& r:model.data)r.colour|=255u;
 Upload(model.instances,model.data.data(),unsigned(model.data.size()*sizeof(Instance)));}
times.clear();p[38]=v[38]=2;
for(int frame=0;frame<40;++frame){
 Set(v,10,sinf(frame*.001f),cosf(frame*.001f),1,0);
 Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));Check(d->BeginScene());
 Check(disjoint->Issue(D3DISSUE_BEGIN));Check(start->Issue(D3DISSUE_END));draw(false);
 Check(end->Issue(D3DISSUE_END));Check(disjoint->Issue(D3DISSUE_END));Check(freq->Issue(D3DISSUE_END));Check(d->EndScene());
 UINT64 a=0,b=0,hz=0;BOOL bad=1;ReadQuery(end,&b,8);ReadQuery(start,&a,8);ReadQuery(freq,&hz,8);ReadQuery(disjoint,&bad,4);
 if(frame>=8&&!bad&&hz)times.push_back(double(b-a)*1000/hz);
}
Require(!times.empty()&&pixels()>5000,"decor diagnostic full field");std::sort(times.begin(),times.end());
printf("PASS decorations-only GPU: %u static instances, shader rotation, no fog/distance/subpixel dissolve; median %.3f ms p95 %.3f ms\n",
 proceduralCount,times[times.size()/2],times[(times.size()-1)*95/100]);
Check(D3DXSaveSurfaceToFileA(argv[12],D3DXIFF_PNG,target,nullptr,nullptr));
#endif
