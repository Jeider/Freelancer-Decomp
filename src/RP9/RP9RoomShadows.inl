// Included after RP9RoomMaterials.inl. Shares the native draw and shader-cache helpers.
GENRESULT DACOM_API FDirectX9::BeginRoomShadow(const float* CameraView12, const float* Center, float Radius,
                                            unsigned long Character)
{
    auto* E=Ex_;
    if(!E || !Device_ || !E->bRoomFrame || E->bRoomShadowFailed || E->bShadowDrawing || E->bInPass ||
       !CameraView12 || !Center || !std::isfinite(Radius) || Radius<=0 || Radius>10000 || !E->SceneDepth.Texture) return GR_GENERIC;
    static const bool Enabled=ReadShadowSetting("room_object_shadows",1,0,1)>.5f;
    if(!Enabled) return GR_GENERIC;
    for(unsigned I=0;I<3;++I)if(!std::isfinite(Center[I]))return GR_GENERIC;
    for(unsigned I=0;I<12;++I)if(!std::isfinite(CameraView12[I]))return GR_GENERIC;
    float Flip[12];memcpy(Flip,CameraView12,sizeof(Flip));
    Flip[6]=-Flip[6];Flip[7]=-Flip[7];Flip[8]=-Flip[8];Flip[11]=-Flip[11];
    FRp9TransformCache Camera={};Camera.StoreAffine(Flip);
    D3DXMATRIX CameraMatrix,CameraInverse;memcpy(&CameraMatrix,Camera.Values,64);
    if(!D3DXMatrixInverse(&CameraInverse,nullptr,&CameraMatrix))return GR_GENERIC;
    memcpy(E->RoomShadowCamera,Camera.Values,64);memcpy(E->RoomShadowCameraInverse,&CameraInverse,64);
    IDirect3DSurface9* Depth=nullptr;Device_->GetDepthStencilSurface(&Depth);
    bool CorrectDepth=Depth && Depth==E->SceneDepth.Surface;
    if(Depth)Depth->Release();if(!CorrectDepth)return GR_GENERIC;
    if(!E->RoomShadowVs || !E->RoomShadowPs || !E->RoomShadowSkinVs || !E->RoomShadowApplyPs)
    {
        bool Ok=ExCompileShaderPair("room_shadow.hlsl",&E->RoomShadowVs,&E->RoomShadowPs,"VSMain","PSMain");
        if(Ok)Ok=ExCompileShaderPair("room_shadow.hlsl",&E->RoomShadowSkinVs,&E->RoomShadowApplyPs,"VSSkin","ApplyPS");
        if(!Ok){E->bRoomShadowFailed=true;return GR_GENERIC;}
    }
    HRESULT Hr=S_OK;
    if(!E->RoomShadowMap)Hr=Device_->CreateTexture(1024,1024,1,D3DUSAGE_RENDERTARGET,D3DFMT_R32F,D3DPOOL_DEFAULT,&E->RoomShadowMap,nullptr);
    if(SUCCEEDED(Hr) && !E->RoomShadowDepth)Hr=Device_->CreateDepthStencilSurface(1024,1024,D3DFMT_D24X8,D3DMULTISAMPLE_NONE,0,TRUE,&E->RoomShadowDepth,nullptr);
    if(FAILED(Hr)){E->bRoomShadowFailed=true;return GR_GENERIC;}
    ExFlushSurfaceInstances();ExSurfaceEnd();ExSurfaceRelease();FlushDrawState(Device_);
    E->ShadowSavedRenderStates=RenderStates_;E->ShadowSavedDeviceStates=DeviceStates_;
    E->ShadowSavedTransforms=Transforms_;E->ShadowSavedStream=StreamCache_;E->ShadowSavedBaseVertex=DeviceBaseVertex_;
    E->ShadowSavedMaterial=E->SurfaceMaterial;E->bShadowSavedMaterialValid=E->bSurfaceMaterialValid;
    memcpy(E->ShadowSavedPipeline,PipelineStates_,sizeof(PipelineStates_));
    memcpy(E->RoomShadowSavedBones,E->RoomBones,sizeof(E->RoomBones));
    E->bRoomShadowSavedPaletteUnsupported=E->bRoomPaletteUnsupported;
    Hr=E->ShadowSavedState ? E->ShadowSavedState->Capture() : Device_->CreateStateBlock(D3DSBT_ALL,&E->ShadowSavedState);
    if(FAILED(Hr))return GR_GENERIC;
    Hr=Device_->GetRenderTarget(0,&E->ShadowSavedColor);
    if(SUCCEEDED(Hr))Hr=Device_->GetViewport(&E->ShadowSavedViewport);
    if(FAILED(Hr)){if(E->ShadowSavedColor){E->ShadowSavedColor->Release();E->ShadowSavedColor=nullptr;}return GR_GENERIC;}
    Device_->GetDepthStencilSurface(&E->ShadowSavedDepth);
    Radius=(std::max)(.5f,Radius*1.1f);E->RoomShadowRadius=Radius;
    float* M=E->RoomShadowMatrix;memset(M,0,64);
    // A vertical standing body collapses under its head/shoulders at exact zenith.
    // Give characters a modest world-anchored downward slant (~28 degrees),
    // keeping ships vertical. Widen the map to include the complete sheared bounds.
    const float TiltX=Character ? .45f:0, TiltZ=Character ? .30f:0;
    const float Half=Radius*(Character ? 1.5f:1.f);
    M[0]=1/Half;M[4]=TiltX/Half;M[9]=1/Half;M[5]=TiltZ/Half;M[6]=-1/(2*Radius);
    M[12]=-(Center[0]+TiltX*Center[1])/Half;M[13]=-(Center[2]+TiltZ*Center[1])/Half;
    M[14]=(Center[1]+Radius)/(2*Radius);M[15]=1;
    E->bRoomShadowDrawing=E->bShadowDrawing=true;E->RoomShadowDraws=0;E->bRoomPaletteUnsupported=false;
    Rp9SetTexture(Device_,15,nullptr);
    IDirect3DSurface9* Target=nullptr;Hr=E->RoomShadowMap->GetSurfaceLevel(0,&Target);
    if(SUCCEEDED(Hr))Hr=Device_->SetDepthStencilSurface(nullptr);
    if(SUCCEEDED(Hr))Hr=Device_->SetRenderTarget(0,Target);
    if(Target)Target->Release();
    if(SUCCEEDED(Hr))Hr=Device_->SetDepthStencilSurface(E->RoomShadowDepth);
    D3DVIEWPORT9 V={0,0,1024,1024,0,1};if(SUCCEEDED(Hr))Hr=Device_->SetViewport(&V);
    if(SUCCEEDED(Hr))Hr=Device_->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xffffffff,1,0);
    if(FAILED(Hr)){EndRoomShadow();return GR_GENERIC;}
    return GR_OK;
}

bool FDirectX9::ExRoomShadowDrawBegin()
{
    auto* E=Ex_;
    unsigned Fvf=StreamCache_.Fvf ? StreamCache_.Fvf : StreamCache_.VertexBuffer ? StreamCache_.VertexBuffer->Fvf : 0;
    bool Skin=(Fvf&D3DFVF_POSITION_MASK)==D3DFVF_XYZB4 && (Fvf&D3DFVF_LASTBETA_UBYTE4) &&
        RenderStates_.GetPending(D3DRS_INDEXEDVERTEXBLENDENABLE) && RenderStates_.GetPending(D3DRS_VERTEXBLEND)==D3DVBF_3WEIGHTS;
    if((!Skin && (Fvf&D3DFVF_POSITION_MASK)!=D3DFVF_XYZ) || (Skin && E->bRoomPaletteUnsupported) ||
       RenderStates_.GetPending(D3DRS_ALPHABLENDENABLE)) return false;
    float Alpha[4]={0,0,1,0};
    if(RenderStates_.GetPending(D3DRS_ALPHATESTENABLE))
    {
        unsigned Func=RenderStates_.GetPending(D3DRS_ALPHAFUNC);
        if(Func!=D3DCMP_GREATER && Func!=D3DCMP_GREATEREQUAL)return false;
        Alpha[0]=1;Alpha[1]=RenderStates_.GetPending(D3DRS_ALPHAREF)/255.f;
        Alpha[2]=E->bSurfaceMaterialValid ? E->SurfaceMaterial.Diffuse.a:1;
    }
    auto Tss=[&](unsigned T,unsigned Default){auto& V=DeviceStates_.TextureStates[0][T];return V.bValid ? V.Value:Default;};
    float Mode[4]={(float)Tss(D3DTSS_TEXCOORDINDEX,0),(float)Tss(D3DTSS_TEXTURETRANSFORMFLAGS,0),0,0};
    if(Alpha[0] && (Mode[0]>2 || (Mode[1]!=0 && Mode[1]!=D3DTTFF_COUNT2)))return false;
    Rp9SetRenderState(Device_,D3DRS_ZENABLE,TRUE);Rp9SetRenderState(Device_,D3DRS_ZWRITEENABLE,TRUE);
    Rp9SetRenderState(Device_,D3DRS_ZFUNC,D3DCMP_LESSEQUAL);Rp9SetRenderState(Device_,D3DRS_ALPHABLENDENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_ALPHATESTENABLE,FALSE);Rp9SetRenderState(Device_,D3DRS_CULLMODE,D3DCULL_NONE);
    Rp9SetRenderState(Device_,D3DRS_COLORWRITEENABLE,15);Rp9SetRenderState(Device_,D3DRS_FOGENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_SCISSORTESTENABLE,FALSE);Rp9SetRenderState(Device_,D3DRS_STENCILENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_CLIPPLANEENABLE,0);Rp9SetRenderState(Device_,D3DRS_SRGBWRITEENABLE,FALSE);
    Rp9SetRenderState(Device_,D3DRS_DEPTHBIAS,0);Rp9SetRenderState(Device_,D3DRS_SLOPESCALEDEPTHBIAS,0);
    HRESULT Hr=Rp9SetVertexShader(Device_,Skin ? E->RoomShadowSkinVs:E->RoomShadowVs);
    if(SUCCEEDED(Hr))Hr=Rp9SetPixelShader(Device_,E->RoomShadowPs);
    if(SUCCEEDED(Hr))Hr=Rp9SetVertexConstants(Device_,0,Transforms_.World.Values,4);
    // Legacy room draws can precompose camera into WORLD (SetModelview) or
    // leave it in VIEW. Undo the real camera after WORLD*VIEW in both cases.
    float ToWorld[16],ToShadow[16];
    MulMatrix4(Transforms_.View.Values,E->RoomShadowCameraInverse,ToWorld);
    MulMatrix4(ToWorld,E->RoomShadowMatrix,ToShadow);
    if(SUCCEEDED(Hr))Hr=Rp9SetVertexConstants(Device_,4,ToShadow,4);
    if(SUCCEEDED(Hr))Hr=Rp9SetVertexConstants(Device_,8,DeviceStates_.TextureTransforms[0].Values,4);
    if(SUCCEEDED(Hr))Hr=Rp9SetVertexConstants(Device_,12,Mode,1);
    if(Skin && SUCCEEDED(Hr))
    {
        float Rows[192*4];
        for(unsigned I=0;I<64;++I)for(unsigned R=0;R<3;++R)for(unsigned C=0;C<4;++C)
            Rows[I*12+R*4+C]=(I ? E->RoomBones[I]:Transforms_.World.Values)[C*4+R];
        Hr=Rp9SetVertexConstants(Device_,24,Rows,192);
    }
    if(SUCCEEDED(Hr))Hr=Rp9SetPixelConstants(Device_,0,Alpha,1);
    if(SUCCEEDED(Hr))++E->RoomShadowDraws;
    return SUCCEEDED(Hr);
}

GENRESULT DACOM_API FDirectX9::EndRoomShadow()
{
    auto* E=Ex_;if(!E || !Device_ || !E->bRoomShadowDrawing)return GR_GENERIC;
    E->bRoomShadowDrawing=E->bShadowDrawing=false;
    HRESULT Hr=Device_->SetDepthStencilSurface(nullptr);
    if(SUCCEEDED(Hr))Hr=Device_->SetRenderTarget(0,E->ShadowSavedColor);
    if(SUCCEEDED(Hr))Hr=Device_->SetViewport(&E->ShadowSavedViewport);
    if(SUCCEEDED(Hr) && !E->RoomShadowDraws)Hr=E_FAIL;
    if(SUCCEEDED(Hr))
    {
        float Params[44]={},Vp[16];
        MulMatrix4(E->RoomShadowCamera,E->ShadowSavedTransforms.Projection.Values,Vp);
        D3DXMATRIX M,Inv;memcpy(&M,Vp,64);
        if(D3DXMatrixInverse(&Inv,nullptr,&M))
        {
            memcpy(Params,&Inv,64);memcpy(Params+16,E->RoomShadowMatrix,64);
            D3DSURFACE_DESC Desc={};E->SceneDepth.Surface->GetDesc(&Desc);
            auto& V=E->ShadowSavedViewport;
            Params[32]=1.f/Desc.Width;Params[33]=1.f/Desc.Height;Params[34]=(float)Desc.Width;Params[35]=(float)Desc.Height;
            Params[36]=(float)V.X;Params[37]=(float)V.Y;Params[38]=(float)V.Width;Params[39]=(float)V.Height;
            Params[40]=V.MinZ;Params[41]=V.MaxZ;Params[42]=1.f/1024;Params[43]=.45f;
            struct Vertex{float X,Y,Z,W,U,V;};float X=(float)V.X,Y=(float)V.Y,W=(float)V.Width,H=(float)V.Height;
            Vertex Q[]={{X-.5f,Y-.5f,0,1,X*Params[32],Y*Params[33]},
                {X+W-.5f,Y-.5f,0,1,(X+W)*Params[32],Y*Params[33]},
                {X-.5f,Y+H-.5f,0,1,X*Params[32],(Y+H)*Params[33]},
                {X+W-.5f,Y+H-.5f,0,1,(X+W)*Params[32],(Y+H)*Params[33]}};
            Rp9SetVertexShader(Device_,nullptr);Rp9SetFvf(Device_,D3DFVF_XYZRHW|D3DFVF_TEX1);
            Rp9SetPixelShader(Device_,E->RoomShadowApplyPs);Rp9SetPixelConstants(Device_,0,Params,11);
            Device_->SetTextureStageState(0,D3DTSS_TEXCOORDINDEX,0);Device_->SetTextureStageState(0,D3DTSS_TEXTURETRANSFORMFLAGS,0);
            Rp9SetRenderState(Device_,D3DRS_ZENABLE,FALSE);Rp9SetRenderState(Device_,D3DRS_ZWRITEENABLE,FALSE);
            Rp9SetRenderState(Device_,D3DRS_ALPHATESTENABLE,FALSE);Rp9SetRenderState(Device_,D3DRS_FOGENABLE,FALSE);
            Rp9SetRenderState(Device_,D3DRS_ALPHABLENDENABLE,TRUE);Rp9SetRenderState(Device_,D3DRS_SRCBLEND,D3DBLEND_ZERO);
            Rp9SetRenderState(Device_,D3DRS_DESTBLEND,D3DBLEND_SRCCOLOR);Rp9SetRenderState(Device_,D3DRS_BLENDOP,D3DBLENDOP_ADD);
            Rp9SetRenderState(Device_,D3DRS_COLORWRITEENABLE,7);Rp9SetRenderState(Device_,D3DRS_CULLMODE,D3DCULL_NONE);
            Rp9SetRenderState(Device_,D3DRS_SCISSORTESTENABLE,FALSE);Rp9SetRenderState(Device_,D3DRS_STENCILENABLE,FALSE);
            Rp9SetRenderState(Device_,D3DRS_CLIPPLANEENABLE,0);Rp9SetRenderState(Device_,D3DRS_SRGBWRITEENABLE,FALSE);
            Rp9SetRenderState(Device_,D3DRS_FILLMODE,D3DFILL_SOLID);
            for(unsigned S : {14u,15u})
            {
                Rp9SetSamplerState(Device_,S,D3DSAMP_MINFILTER,D3DTEXF_POINT);Rp9SetSamplerState(Device_,S,D3DSAMP_MAGFILTER,D3DTEXF_POINT);
                Rp9SetSamplerState(Device_,S,D3DSAMP_MIPFILTER,D3DTEXF_NONE);Rp9SetSamplerState(Device_,S,D3DSAMP_SRGBTEXTURE,FALSE);
                Rp9SetSamplerState(Device_,S,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);Rp9SetSamplerState(Device_,S,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);
            }
            Rp9SetTexture(Device_,14,E->SceneDepth.Texture);Rp9SetTexture(Device_,15,E->RoomShadowMap);
            Hr=Device_->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,Q,sizeof(Vertex));
        }
        else Hr=E_FAIL;
    }
    Rp9SetTexture(Device_,14,nullptr);Rp9SetTexture(Device_,15,nullptr);
    HRESULT Restore=Device_->SetDepthStencilSurface(E->ShadowSavedDepth);
    if(SUCCEEDED(Restore))Restore=E->ShadowSavedState->Apply();Rp9DeviceCalls().Invalidate();
    if(E->ShadowSavedColor){E->ShadowSavedColor->Release();E->ShadowSavedColor=nullptr;}
    if(E->ShadowSavedDepth){E->ShadowSavedDepth->Release();E->ShadowSavedDepth=nullptr;}
    RenderStates_=E->ShadowSavedRenderStates;DeviceStates_=E->ShadowSavedDeviceStates;
    Transforms_=E->ShadowSavedTransforms;StreamCache_=E->ShadowSavedStream;DeviceBaseVertex_=E->ShadowSavedBaseVertex;
    E->SurfaceMaterial=E->ShadowSavedMaterial;E->bSurfaceMaterialValid=E->bShadowSavedMaterialValid;
    memcpy(PipelineStates_,E->ShadowSavedPipeline,sizeof(PipelineStates_));
    memcpy(E->RoomBones,E->RoomShadowSavedBones,sizeof(E->RoomBones));E->bRoomPaletteUnsupported=E->bRoomShadowSavedPaletteUnsupported;
    E->RoomCurrent=nullptr;
    return (GENRESULT)(FAILED(Hr) ? Hr:Restore);
}

void FDirectX9::ExRoomShadowRelease()
{
    auto* E=Ex_;if(!E)return;
    if(E->bRoomShadowDrawing && Device_){E->RoomShadowDraws=0;EndRoomShadow();}
    if(Device_)Rp9SetTexture(Device_,15,nullptr);
    if(E->RoomShadowMap){E->RoomShadowMap->Release();E->RoomShadowMap=nullptr;}
    if(E->RoomShadowDepth){E->RoomShadowDepth->Release();E->RoomShadowDepth=nullptr;}
    if(E->RoomShadowVs){E->RoomShadowVs->Release();E->RoomShadowVs=nullptr;}
    if(E->RoomShadowSkinVs){E->RoomShadowSkinVs->Release();E->RoomShadowSkinVs=nullptr;}
    if(E->RoomShadowPs){E->RoomShadowPs->Release();E->RoomShadowPs=nullptr;}
    if(E->RoomShadowApplyPs){E->RoomShadowApplyPs->Release();E->RoomShadowApplyPs=nullptr;}
    E->bRoomShadowFailed=false;
}
