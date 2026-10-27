// Included by RP9Ex.cpp: shares the compiler/cache and legacy state helpers.
static std::string RoomDataPath(const char* Relative)
{
    char Module[MAX_PATH] = {}; GetModuleFileNameA(nullptr, Module, MAX_PATH);
    char* Slash = strrchr(Module, '\\'); if (!Slash) return {};
    Slash[1] = 0; return std::string(Module) + "../DATA_EXTRA/ROOM_MATERIALS/" + Relative;
}

GENRESULT DACOM_API FDirectX9::SetRoomMaterialFrame(unsigned long Enabled)
{
    auto* E = Ex_; if (!E) return GR_GENERIC;
    ExFlushSurfaceInstances(); ExSurfaceEnd(); ExSurfaceRelease();
    E->RoomCurrent = nullptr; E->bRoomFrame = Enabled != 0;
    if (!Enabled && Device_) Rp9SetTexture(Device_,14,nullptr);
    if (Enabled && !E->bRoomRead)
    {
        E->bRoomRead = true;
        E->bRoomEnabled = ReadShadowSetting("room_materials", 1, 0, 1) > .5f;
        FILE* File = fopen(RoomDataPath("profiles.txt").c_str(), "rb");
        if (File)
        {
            char Line[2048], Map[65], Key[1536];
            while (fgets(Line, sizeof(Line), File))
            {
                FRp9ExState::RoomProfile P;
                if (sscanf(Line, "%f %f %f %f %64s %1535[^\r\n]", &P.Normal, &P.Roughness,
                           &P.Specular, &P.Skin, Map, Key) != 6) continue;
                // Only generated hexadecimal filenames; no paths from a profile.
                if (strlen(Map) != 36 || strspn(Map, "0123456789abcdef") != 32 || strcmp(Map+32,".dds")) continue;
                if (!std::isfinite(P.Normal) || !std::isfinite(P.Roughness) || !std::isfinite(P.Specular) || !std::isfinite(P.Skin) ||
                    P.Normal < 0 || P.Normal > 1 || P.Roughness < .16f || P.Roughness > 1 ||
                    P.Specular < 0 || P.Specular > 2 || P.Skin < -1 || P.Skin > 1) continue;
                P.Map = Map; E->RoomProfiles[LowerString(Key)] = P;
            }
            fclose(File);
        }
        ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "room materials: %u profiles, %s; authored room lights and UVs retained",
            (unsigned)E->RoomProfiles.size(), E->bRoomEnabled ? "enabled" : "disabled");
    }
    if (Enabled)
    {
        E->bRoomPaletteUnsupported = false;
        ++E->RoomFrame;
        if ((E->RoomFrame % 120) == 0)
            for (auto& Item : E->RoomProfiles)
                if (Item.second.Texture && E->RoomFrame - Item.second.LastFrame > 120)
                { Item.second.Texture->Release(); Item.second.Texture = nullptr; Item.second.Tried = false; }
    }
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::SetRoomMaterial(const char* Name, const char* Texture)
{
    auto* E = Ex_; if (!E) return GR_GENERIC;
    E->RoomCurrent = nullptr;
    E->ShipNormalCurrent = nullptr;
    if (E->bShipNormalScope && !E->bRoomFrame && Name)
    {
        auto& Profiles=E->bSolarNormalScope ? E->SolarNormalProfiles : E->ShipNormalProfiles;
        auto Found=Profiles.find(LowerString(std::string(Name)+"|"+(Texture?Texture:"")));
        if(Found!=Profiles.end()) E->ShipNormalCurrent=Found->second;
    }
    if (!E->bRoomFrame || !E->bRoomEnabled || !Name) return GR_OK;
    auto Found = E->RoomProfiles.find(LowerString(std::string(Name) + "|" + (Texture ? Texture : "")));
    if (Found != E->RoomProfiles.end()) E->RoomCurrent = &Found->second;
    return GR_OK;
}

void FDirectX9::ExRoomMaterialRelease()
{
    auto* E = Ex_; if (!E) return;
    for (auto& Item : E->RoomProfiles)
    {
        if (Item.second.Texture) Item.second.Texture->Release();
        Item.second.Texture = nullptr; Item.second.Tried = false;
    }
    if (E->RoomVs) E->RoomVs->Release(); E->RoomVs = nullptr;
    if (E->RoomSkinVs) E->RoomSkinVs->Release(); E->RoomSkinVs = nullptr;
    if (E->RoomPs) E->RoomPs->Release(); E->RoomPs = nullptr;
    if (E->RoomAoPs) E->RoomAoPs->Release(); E->RoomAoPs = nullptr;
    E->bRoomAoFailed = false;
    E->RoomCurrent = nullptr; E->bRoomFrame = E->bRoomFailed = false;
}

bool FDirectX9::ExRoomMaterialBegin()
{
    auto* E = Ex_;
    if (!E || !Device_ || !E->bRoomFrame || !E->RoomCurrent || !E->bRoomEnabled || E->bRoomFailed ||
        E->bInPass || E->bShadowDrawing || E->bSurfaceActive || !E->bSurfaceMaterialValid) return false;
    // Restore native face shading, including its per-vertex lighting. Merely
    // zeroing the generated normal would retain the new per-pixel facial shading.
    if (E->RoomCurrent->Skin > .5f) return false;
    const unsigned Fvf = StreamCache_.Fvf ? StreamCache_.Fvf : StreamCache_.VertexBuffer ? StreamCache_.VertexBuffer->Fvf : 0;
    const unsigned Uvs = (Fvf & D3DFVF_TEXCOUNT_MASK) >> D3DFVF_TEXCOUNT_SHIFT;
    const bool Skin = (Fvf & D3DFVF_POSITION_MASK) == D3DFVF_XYZB4 && (Fvf & D3DFVF_LASTBETA_UBYTE4) &&
                     RenderStates_.GetPending(D3DRS_INDEXEDVERTEXBLENDENABLE) && RenderStates_.GetPending(D3DRS_VERTEXBLEND) == D3DVBF_3WEIGHTS;
    if ((!Skin && (Fvf & D3DFVF_POSITION_MASK) != D3DFVF_XYZ) || !(Fvf & D3DFVF_NORMAL) ||
        !Uvs || Uvs > 3 || (Fvf & 0xffff0000u) || RenderStates_.GetPending(D3DRS_ALPHABLENDENABLE)) return false;
    if (Skin && E->bRoomPaletteUnsupported) return false;
    // Never reinterpret authored reflection vectors or unusual multipass blends.
    auto Tss = [&](unsigned S, unsigned T, unsigned Default) {
        auto& V = DeviceStates_.TextureStates[S][T]; return V.bValid ? V.Value : Default;
    };
    unsigned Stages = 0;
    for (unsigned S = 0; S < 3; ++S)
    {
        unsigned Op = Tss(S, D3DTSS_COLOROP, S ? D3DTOP_DISABLE : D3DTOP_MODULATE);
        if (Op == D3DTOP_DISABLE) break;
        if (S == 2 || Op < 2 || Op > 16 || Tss(S,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1) > 16 ||
            Tss(S,D3DTSS_TEXCOORDINDEX,S) >= Uvs ||
            (Tss(S,D3DTSS_TEXTURETRANSFORMFLAGS,0) != 0 && Tss(S,D3DTSS_TEXTURETRANSFORMFLAGS,0) != D3DTTFF_COUNT2) ||
            Tss(S,D3DTSS_RESULTARG,D3DTA_CURRENT) != D3DTA_CURRENT) return false;
        for (unsigned A : {D3DTSS_COLORARG1, D3DTSS_COLORARG2, D3DTSS_ALPHAARG1, D3DTSS_ALPHAARG2})
            if ((Tss(S,A,A == D3DTSS_COLORARG1 || A == D3DTSS_ALPHAARG1 ? D3DTA_TEXTURE : D3DTA_CURRENT) & 15) > 3) return false;
        if (!DeviceStates_.TextureBindings[S].bValid) return false;
        auto* Tex = PipelineTextureFromHandle(DeviceStates_.TextureBindings[S].Handle);
        if (!Tex || Tex->GetType() != D3DRTYPE_TEXTURE) return false;
        ++Stages;
    }
    if (!Stages) return false;
    if (!E->RoomVs || !E->RoomPs)
        if (!ExCompileShaderPair("room_material.hlsl", &E->RoomVs, &E->RoomPs, "VSMain", "PSMain"))
        { E->bRoomFailed = true; return false; }
    if (Skin && !E->RoomSkinVs)
    {
        // Compile the same PS too through the shared helper, release the temporary reference.
        IDirect3DPixelShader9* Ps = nullptr;
        bool Ok = ExCompileShaderPair("room_material.hlsl", &E->RoomSkinVs, &Ps, "VSSkin", "PSMain");
        if (Ps) Ps->Release(); if (!Ok) return false;
    }
    auto& P = *E->RoomCurrent;
    P.LastFrame = E->RoomFrame;
    if (!P.Tried)
    {
        RuntimeHitchScope Hitch("room_texture", P.Map.c_str());
        P.Tried = true;
        D3DXCreateTextureFromFileExA(Device_, RoomDataPath(P.Map.c_str()).c_str(), D3DX_DEFAULT, D3DX_DEFAULT,
            D3DX_DEFAULT, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, D3DX_FILTER_NONE, D3DX_FILTER_NONE, 0, nullptr, nullptr, &P.Texture);
        if (!P.Texture) ExLogf(kExFdumpWarning,"WARNING",__LINE__,"room map unavailable: %s; native material retained",P.Map.c_str());
    }
    if (!P.Texture) return false;
    float Vs[22*4] = {};
    MulMatrix4(Transforms_.World.Values, Transforms_.View.Values, Vs);
    memcpy(Vs+16,Transforms_.Projection.Values,64);
    D3DXMATRIX M,Inv,N; memcpy(&M,Vs,64);
    if (!D3DXMatrixInverse(&Inv,nullptr,&M)) return false; D3DXMatrixTranspose(&N,&Inv); memcpy(Vs+32,&N,64);
    memcpy(Vs+48,DeviceStates_.TextureTransforms[0].Values,64);memcpy(Vs+64,DeviceStates_.TextureTransforms[1].Values,64);
    Vs[80]=(float)Tss(0,D3DTSS_TEXCOORDINDEX,0);Vs[81]=Stages>1 ? (float)Tss(1,D3DTSS_TEXCOORDINDEX,1) : 0;
    Vs[82]=(float)Tss(0,D3DTSS_TEXTURETRANSFORMFLAGS,0);Vs[83]=(float)Tss(1,D3DTSS_TEXTURETRANSFORMFLAGS,0);
    Vs[84]=(Fvf&D3DFVF_DIFFUSE) ? 1.f : 0.f;Vs[85]=(Fvf&D3DFVF_SPECULAR) ? 1.f : 0.f;
    float Ps[54*4] = {};
    auto Set = [&](unsigned R,float X,float Y,float Z,float W){float* V=Ps+R*4;V[0]=X;V[1]=Y;V[2]=Z;V[3]=W;};
    auto Colour = [&](unsigned R,unsigned C){Set(R,((C>>16)&255)/255.f,((C>>8)&255)/255.f,(C&255)/255.f,((C>>24)&255)/255.f);};
    const auto& Mat=E->SurfaceMaterial;
    memcpy(Ps,&Mat.Diffuse,16);memcpy(Ps+4,&Mat.Ambient,16);memcpy(Ps+8,&Mat.Emissive,16);memcpy(Ps+12,&Mat.Specular,16);
    D3DLIGHT9 Lights[8];unsigned Count=ExCollectSurfaceLights(Lights,8);
    Set(4,(float)Count,RenderStates_.GetPending(D3DRS_LIGHTING) ? 1.f : 0.f,1,(float)Stages);
    unsigned FogMode=RenderStates_.GetPending(D3DRS_FOGTABLEMODE);
    if (!FogMode) FogMode=RenderStates_.GetPending(D3DRS_FOGVERTEXMODE);
    if (!RenderStates_.GetPending(D3DRS_FOGENABLE)) FogMode=0;
    Set(5,FloatBits(RenderStates_.GetPending(D3DRS_FOGSTART)),FloatBits(RenderStates_.GetPending(D3DRS_FOGEND)),
        FloatBits(RenderStates_.GetPending(D3DRS_FOGDENSITY)),(float)FogMode);
    Colour(6,RenderStates_.GetPending(D3DRS_FOGCOLOR));Ps[27]=RenderStates_.GetPending(D3DRS_RANGEFOGENABLE) ? 1.f : 0.f;
    for (unsigned S=0;S<Stages;++S)
    {
        Set(7+S,(float)Tss(S,D3DTSS_COLOROP,D3DTOP_MODULATE),(float)Tss(S,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1),
            (float)Tss(S,D3DTSS_COLORARG1,D3DTA_TEXTURE),(float)Tss(S,D3DTSS_COLORARG2,D3DTA_CURRENT));
        Ps[36+S*2]=(float)Tss(S,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);Ps[37+S*2]=(float)Tss(S,D3DTSS_ALPHAARG2,D3DTA_CURRENT);
    }
    Colour(10,RenderStates_.GetPending(D3DRS_TEXTUREFACTOR));Set(11,P.Normal,P.Roughness,P.Specular,P.Skin);
    Colour(53,RenderStates_.GetPending(D3DRS_AMBIENT));
    memcpy(&M,Transforms_.View.Values,64);
    for (unsigned I=0;I<Count;++I)
    {
        auto& L=Lights[I];D3DXVECTOR3 Pos,Dir;
        D3DXVec3TransformCoord(&Pos,reinterpret_cast<const D3DXVECTOR3*>(&L.Position),&M);
        D3DXVec3TransformNormal(&Dir,reinterpret_cast<const D3DXVECTOR3*>(&L.Direction),&M);
        unsigned R=12+I*5;Set(R,Pos.x,Pos.y,Pos.z,(float)L.Type);Set(R+1,Dir.x,Dir.y,Dir.z,L.Range);
        Set(R+2,L.Diffuse.r,L.Diffuse.g,L.Diffuse.b,L.Falloff);
        bool S=L.Specular.r>0 || L.Specular.g>0 || L.Specular.b>0;
        Set(R+3,S?L.Specular.r:L.Diffuse.r,S?L.Specular.g:L.Diffuse.g,S?L.Specular.b:L.Diffuse.b,std::cos(L.Phi*.5f));
        Set(R+4,L.Attenuation0,L.Attenuation1,L.Attenuation2,std::cos(L.Theta*.5f));
        Ps[212]+=L.Ambient.r;Ps[213]+=L.Ambient.g;Ps[214]+=L.Ambient.b;
    }
    const bool ColourVertex=RenderStates_.GetPending(D3DRS_COLORVERTEX)!=0;
    auto Source=[&](unsigned State){unsigned S=RenderStates_.GetPending(State);return ColourVertex &&
        ((S==D3DMCS_COLOR1 && (Fvf&D3DFVF_DIFFUSE)) || (S==D3DMCS_COLOR2 && (Fvf&D3DFVF_SPECULAR))) ? (float)S : 0.f;};
    Set(52,Source(D3DRS_DIFFUSEMATERIALSOURCE),Source(D3DRS_AMBIENTMATERIALSOURCE),Source(D3DRS_EMISSIVEMATERIALSOURCE),0);
    HRESULT Hr=Rp9SetVertexShader(Device_,Skin ? E->RoomSkinVs : E->RoomVs);
    if(SUCCEEDED(Hr))Hr=Rp9SetPixelShader(Device_,E->RoomPs);
    if(SUCCEEDED(Hr))Hr=Rp9SetVertexConstants(Device_,0,Vs,22);
    if(Skin && SUCCEEDED(Hr))
    {
        float Rows[192*4];
        for(unsigned I=0;I<64;++I)for(unsigned R=0;R<3;++R)for(unsigned C=0;C<4;++C)
            Rows[I*12+R*4+C]=(I ? E->RoomBones[I] : Transforms_.World.Values)[C*4+R];
        Hr=Rp9SetVertexConstants(Device_,24,Rows,192);
        if(SUCCEEDED(Hr))Hr=Rp9SetVertexConstants(Device_,216,Transforms_.View.Values,4);
    }
    if(SUCCEEDED(Hr))Hr=Rp9SetPixelConstants(Device_,0,Ps,54);
    if(SUCCEEDED(Hr))Hr=Rp9SetTexture(Device_,14,P.Texture);
    // Match the diffuse address mode for the existing (possibly mirrored) UVs.
    for(unsigned S : {D3DSAMP_ADDRESSU,D3DSAMP_ADDRESSV})
    {
        auto& A=Rp9DeviceCalls();
        unsigned V=A.SamplerValid[0][S] ? A.Samplers[0][S] : D3DTADDRESS_WRAP;
        Rp9SetSamplerState(Device_,14,(D3DSAMPLERSTATETYPE)S,V);
    }
    Rp9SetSamplerState(Device_,14,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);Rp9SetSamplerState(Device_,14,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);
    Rp9SetSamplerState(Device_,14,D3DSAMP_MIPFILTER,D3DTEXF_LINEAR);Rp9SetSamplerState(Device_,14,D3DSAMP_SRGBTEXTURE,FALSE);
    if(FAILED(Hr)){ExSurfaceRelease();return false;}
    E->bSurfaceActive=true;
    if(E->RoomLoggedMaps.size()<16 && E->RoomLoggedMaps.insert(P.Map).second)
        ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"room material active: map %s, FVF 0x%x, lights %u, normal %.2f, roughness %.2f, skin %.1f",
            P.Map.c_str(),Fvf,Count,P.Normal,P.Roughness,P.Skin);
    return true;
}

GENRESULT DACOM_API FDirectX9::ApplyRoomContactShadows()
{
    auto* E=Ex_;
    if(!Device_ || !E || !E->bRoomFrame || !E->bRoomEnabled || E->bRoomAoFailed ||
       E->bInPass || E->bShadowDrawing || !E->SceneDepth.Texture || !E->SceneDepth.Surface) return GR_OK;
    static const float Strength=ReadShadowSetting("room_contact_shadows",.32f,0,.6f);
    if(Strength<=0) return GR_OK;
    IDirect3DSurface9* Depth=nullptr;
    if(FAILED(Device_->GetDepthStencilSurface(&Depth)))return GR_OK;
    if(Depth!=E->SceneDepth.Surface){if(Depth)Depth->Release();return GR_OK;}
    D3DVIEWPORT9 V={};Device_->GetViewport(&V);
    D3DXMATRIX Proj,Inv;memcpy(&Proj,Transforms_.Projection.Values,64);
    if(!D3DXMatrixInverse(&Inv,nullptr,&Proj)){Depth->Release();return GR_OK;}
    if(!E->RoomAoPs)
    {
        std::string Path=RoomDataPath("../SHADERS/room_contact.hlsl"),Source;
        FILE* File=fopen(Path.c_str(),"rb");
        if(File){char Bytes[4096];size_t N;while((N=fread(Bytes,1,sizeof(Bytes),File)))Source.append(Bytes,N);fclose(File);}
        std::vector<unsigned char> Code;
        if(Source.empty() || !CompileStage(Source,Path,nullptr,"PSMain","ps_3_0",&Code) ||
           FAILED(Device_->CreatePixelShader((DWORD*)Code.data(),&E->RoomAoPs)))
        {E->bRoomAoFailed=true;Depth->Release();return GR_GENERIC;}
    }
    ExSurfaceEnd();ExSurfaceRelease();FlushDrawState(Device_);
    HRESULT Hr=E->RoomAoState ? E->RoomAoState->Capture() : Device_->CreateStateBlock(D3DSBT_ALL,&E->RoomAoState);
    if(FAILED(Hr)){Depth->Release();return (GENRESULT)Hr;}
    D3DSURFACE_DESC Desc={};Depth->GetDesc(&Desc);
    float Params[32]={};memcpy(Params,&Inv,64);
    Params[16]=1.f/Desc.Width;Params[17]=1.f/Desc.Height;Params[18]=(float)Desc.Width;Params[19]=(float)Desc.Height;
    Params[20]=(float)V.X;Params[21]=(float)V.Y;Params[22]=(float)V.Width;Params[23]=(float)V.Height;
    Params[24]=V.MinZ;Params[25]=V.MaxZ;Params[26]=.4f;Params[27]=Strength;Params[28]=Proj._22;
    struct Vertex{float X,Y,Z,W,U,V;};
    float X=(float)V.X,Y=(float)V.Y,W=(float)V.Width,H=(float)V.Height,Iw=Params[16],Ih=Params[17];
    Vertex Q[]={{X-.5f,Y-.5f,0,1,X*Iw,Y*Ih},{X+W-.5f,Y-.5f,0,1,(X+W)*Iw,Y*Ih},
                {X-.5f,Y+H-.5f,0,1,X*Iw,(Y+H)*Ih},{X+W-.5f,Y+H-.5f,0,1,(X+W)*Iw,(Y+H)*Ih}};
    Hr=Device_->SetDepthStencilSurface(nullptr);
    if(SUCCEEDED(Hr))Hr=Rp9SetTexture(Device_,14,E->SceneDepth.Texture);
    Rp9SetVertexShader(Device_,nullptr);Rp9SetFvf(Device_,D3DFVF_XYZRHW|D3DFVF_TEX1);
    Rp9SetPixelShader(Device_,E->RoomAoPs);Rp9SetPixelConstants(Device_,0,Params,8);
    Device_->SetTextureStageState(0,D3DTSS_TEXCOORDINDEX,0);Device_->SetTextureStageState(0,D3DTSS_TEXTURETRANSFORMFLAGS,0);
    Rp9SetRenderState(Device_,D3DRS_ZENABLE,FALSE);Rp9SetRenderState(Device_,D3DRS_ZWRITEENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_ALPHATESTENABLE,FALSE);Rp9SetRenderState(Device_,D3DRS_FOGENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_ALPHABLENDENABLE,TRUE);Rp9SetRenderState(Device_,D3DRS_SRCBLEND,D3DBLEND_ZERO);
    Rp9SetRenderState(Device_,D3DRS_DESTBLEND,D3DBLEND_SRCCOLOR);Rp9SetRenderState(Device_,D3DRS_BLENDOP,D3DBLENDOP_ADD);
    Rp9SetRenderState(Device_,D3DRS_COLORWRITEENABLE,7);Rp9SetRenderState(Device_,D3DRS_CULLMODE,D3DCULL_NONE);
    Rp9SetRenderState(Device_,D3DRS_SCISSORTESTENABLE,FALSE);Rp9SetRenderState(Device_,D3DRS_STENCILENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_CLIPPLANEENABLE,0);Rp9SetRenderState(Device_,D3DRS_SRGBWRITEENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_FILLMODE,D3DFILL_SOLID);
    Rp9SetSamplerState(Device_,14,D3DSAMP_MINFILTER,D3DTEXF_POINT);Rp9SetSamplerState(Device_,14,D3DSAMP_MAGFILTER,D3DTEXF_POINT);
    Rp9SetSamplerState(Device_,14,D3DSAMP_MIPFILTER,D3DTEXF_NONE);Rp9SetSamplerState(Device_,14,D3DSAMP_SRGBTEXTURE,FALSE);
    Rp9SetSamplerState(Device_,14,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);Rp9SetSamplerState(Device_,14,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
    if(SUCCEEDED(Hr))Hr=Device_->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,Q,sizeof(Vertex));
    Rp9SetTexture(Device_,14,nullptr);HRESULT Restore=Device_->SetDepthStencilSurface(Depth);
    if(SUCCEEDED(Restore))Restore=E->RoomAoState->Apply();
    Depth->Release();Rp9DeviceCalls().Invalidate();
    if(SUCCEEDED(Hr) && !E->bRoomAoLogged)
    {E->bRoomAoLogged=true;ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"room contact shading active: strength %.2f, radius 0.4, opaque depth before translucency",Strength);}
    return (GENRESULT)(FAILED(Hr) ? Hr : Restore);
}
