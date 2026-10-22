"""One-time source edit for static-surface shader distance tiers."""
from pathlib import Path

def edit(name, old, new):
    p=Path(name)
    s=p.read_text()
    assert old in s, (name, old[:80])
    p.write_text(s.replace(old,new,1))

edit('src/RP9/RP9Ex.h', '    IDirect3DPixelShader9* SurfacePs = nullptr;',
'''    unsigned SurfaceDistanceTier = 0; // 0 full, 1 diffuse/env only, 2 native
    IDirect3DPixelShader9* SurfaceLowPs = nullptr;
    IDirect3DPixelShader9* SurfaceLowCubePs = nullptr;
    IDirect3DPixelShader9* SurfacePs = nullptr;''')
edit('src/RP9/RP9Ex.cpp', '    if (Ex->SurfacePs != nullptr) {',
'''    if (Ex->SurfaceLowPs) { Ex->SurfaceLowPs->Release(); Ex->SurfaceLowPs=nullptr; }
    if (Ex->SurfaceLowCubePs) { Ex->SurfaceLowCubePs->Release(); Ex->SurfaceLowCubePs=nullptr; }
    if (Ex->SurfacePs != nullptr) {''')
edit('src/RP9/RP9Ex.cpp', '    if (!Ex->bSurfaceEnabled || Ex->SurfaceShader == RPSurfaceLegacy)',
'''    if (!Ex->bSurfaceEnabled || Ex->SurfaceShader == RPSurfaceLegacy ||
        (Ex->SurfaceDistanceTier==2 && !Ex->bSurfaceCockpit))''')
edit('src/RP9/RP9Ex.cpp', '    IDirect3DPixelShader9*& SurfacePs = IsCube ? Ex->SurfaceCubePs : Ex->SurfacePs;',
'''    const bool LowDetail=Ex->SurfaceDistanceTier==1 && !Cockpit && !Glass;
    IDirect3DPixelShader9*& SurfacePs = LowDetail ?
        (IsCube ? Ex->SurfaceLowCubePs : Ex->SurfaceLowPs) :
        (IsCube ? Ex->SurfaceCubePs : Ex->SurfacePs);''')
edit('src/RP9/RP9Ex.cpp', 'const std::string PixelSource = IsCube ? "#define SURFACE_ENV_CUBE 1\\n" + Source : Source;',
'''const std::string PixelSource = std::string(LowDetail ? "#define SURFACE_LOW_DETAIL 1\\n" : "") +
            (IsCube ? "#define SURFACE_ENV_CUBE 1\\n" : "") + Source;''')
edit('src/RP9/RP9Ex.cpp', '    Ex_->bInstanceScope=Scope;',
'''    Ex_->SurfaceDistanceTier=(Enabled&16u) ? 2u : ((Enabled&8u) ? 1u : 0u);
    Ex_->bInstanceScope=Scope;''')
edit('src/freelancer/Client/space_scene_obj_draw.cpp', 'if(!SurfaceScope && PortConfigInt("Render","surface_instancing",1)!=0 && DALib::Pipeline)',
     'if(!SurfaceScope && DALib::Pipeline)')
edit('src/freelancer/Client/space_scene_obj_draw.cpp', '                if(Go && Go->ManagerKind==2) Receiver|=4u;',
'''                if(Go && Go->ManagerKind==2)
                {
                    static const float FullDistance=static_cast<float>(PortConfigInt("Render","surface_static_full_distance",2000));
                    static const float OffDistance=static_cast<float>(PortConfigInt("Render","surface_static_off_distance",20000));
                    static const bool Instances=PortConfigInt("Render","surface_instancing",0)!=0;
                    Vector Center; const float Radius=std::fmax(0.0f,Go->Slot178(Center));
                    const float* Eye=Cam->GetPosition();
                    const float X=Center.x-Eye[0],Y=Center.y-Eye[1],Z=Center.z-Eye[2];
                    const float DistanceSquared=X*X+Y*Y+Z*Z;
                    const float Full=std::fmax(0.0f,FullDistance)+Radius;
                    const float Off=std::fmax(std::fmax(0.0f,FullDistance),OffDistance)+Radius;
                    if(DistanceSquared>Off*Off) Receiver|=16u;
                    else if(DistanceSquared>Full*Full) Receiver|=8u;
                    if(Instances) Receiver|=4u;
                }''')
edit('src/include/render/IRPLocalShadows.h', '    // Existing callers passing 0/1 retain their meaning and vtable layout.',
'''    // Bit 3 selects diffuse/env-only static surfaces; bit 4 uses native materials.
    // Existing callers passing 0/1 retain their meaning and vtable layout.''')
for name,old,new in [
    ('src/RP9/RP9Ex.cpp','ReadShadowSetting("surface_instancing",1,0,1)','ReadShadowSetting("surface_instancing",0,0,1)'),
    ('src/RP9/RP9.cpp','"state_cache",1,PortIni','"state_cache",0,PortIni'),
    ('src/RP9/RP9Ex.h','bSurfaceInstancing=true','bSurfaceInstancing=false')]:
    edit(name,old,new)

shader='DATA_EXTRA/SHADERS/surface_material.hlsl'
edit(shader,'    float SunVisibility=SolarVisibility(In.ViewPosition,N);',
'''#ifdef SURFACE_LOW_DETAIL
    const float SunVisibility=1.0;
#else
    float SunVisibility=SolarVisibility(In.ViewPosition,N);
#endif''')
edit(shader,'    float3 FinishStyle=SurfaceFinish.w', '#ifndef SURFACE_LOW_DETAIL\n    float3 FinishStyle=SurfaceFinish.w')
edit(shader,'    float3 DiffuseLighting = Albedo.rgb * MaterialAmbient.rgb;',
'''#endif
    float3 DiffuseLighting = Albedo.rgb * MaterialAmbient.rgb;''')
edit(shader,'        float3 H = SafeNormal(V + L);',
'''#ifdef SURFACE_LOW_DETAIL
        DiffuseLighting += Attenuation * NoL * Albedo.rgb * Light.DiffuseFalloff.rgb;
#else
        float3 H = SafeNormal(V + L);''')
edit(shader,'    }\n    float3 R = reflect(-V, N);','#endif\n    }\n    float3 R = reflect(-V, N);')
edit(shader,'    // A visible reflection across face-on panels as well as grazing edges.',
'''#ifndef SURFACE_LOW_DETAIL
    // A visible reflection across face-on panels as well as grazing edges.''')
edit(shader,'    Colour += MaterialEmission.rgb;','#endif\n    Colour += MaterialEmission.rgb;')
edit(shader,'    [branch] if(Glass)\n    {\n        float Shine=',
'''#ifndef SURFACE_LOW_DETAIL
    [branch] if(Glass)
    {
        float Shine=''')
edit(shader,'    float4 Result = float4(Colour, Alpha);','#endif\n    float4 Result = float4(Colour, Alpha);')
