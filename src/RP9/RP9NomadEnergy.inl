// Included by RP9Ex.cpp: the original material has already drawn successfully.
void FDirectX9::ExNomadEnergyPrepare()
{
    auto* E=Ex_;
    if(!E || !Device_ || E->bNomadEnergyPrepared) return;
    E->bNomadEnergyPrepared=true;
    E->bNomadEnergyEnabled=ReadShadowSetting("nomad_energy_fx",1,0,1)>0.5f &&
        ReadShadowSetting("nomad_shader",1,0,1)>0.5f && ReadPortFade("surface_shaders")>0.5f;
    E->NomadEnergyStrength=ReadShadowSetting("nomad_energy_glow",0.7f,0,2);
    if(E->bNomadEnergyEnabled && E->NomadEnergyStrength>0 &&
       !ExCompileShaderPair("nomad_energy.hlsl",&E->NomadEnergyVs,&E->NomadEnergyPs))
        ExLogf(kExFdumpWarning,"WARNING",__LINE__,"Nomad energy: overlay unavailable; native material retained");
}

bool FDirectX9::ExNomadEnergyBegin()
{
    auto* E=Ex_;
    if(!E || !Device_ || !IsNomadEnergy(E->SurfaceShader) || E->bInPass ||
       E->bShadowDrawing || E->bRoomFrame || E->bSurfaceActive || E->bSoftActive ||
       !E->bSurfaceMaterialValid || E->NomadEnergySaved ||
       !RenderStates_.GetPending(D3DRS_COLORWRITEENABLE)) return false;
    unsigned Fvf=StreamCache_.Fvf;
    if(!Fvf && StreamCache_.VertexBuffer) Fvf=StreamCache_.VertexBuffer->Fvf;
    if((Fvf&D3DFVF_POSITION_MASK)!=D3DFVF_XYZ || !(Fvf&D3DFVF_NORMAL) ||
       !(Fvf&D3DFVF_TEXCOUNT_MASK)) return false;
    auto tss=[&](unsigned t)->unsigned {auto const& S=DeviceStates_.TextureStates[0][t];return S.bValid?S.Value:0;};
    const unsigned Transform=tss(D3DTSS_TEXTURETRANSFORMFLAGS);
    if(tss(D3DTSS_TEXCOORDINDEX)!=0 || (Transform!=0 && Transform!=D3DTTFF_COUNT2)) return false;
    if(!E->bNomadEnergyPrepared) ExNomadEnergyPrepare();
    if(!E->bNomadEnergyEnabled || !E->NomadEnergyVs || !E->NomadEnergyPs || E->NomadEnergyStrength<=0) return false;
    IDirect3DBaseTexture9* Base=nullptr;
    Device_->GetTexture(0,&Base);
    if(!Base) return false;
    D3DSURFACE_DESC Desc={};
    const bool HasTexture=Base->GetType()==D3DRTYPE_TEXTURE &&
        SUCCEEDED(static_cast<IDirect3DTexture9*>(Base)->GetLevelDesc(0,&Desc));
    Base->Release();
    if(!HasTexture) return false;
    float Vs[68]={};
    MulMatrix4(Transforms_.World.Values,Transforms_.View.Values,Vs);
    memcpy(Vs+16,Transforms_.Projection.Values,64);
    D3DXMATRIX Wv,Inverse,Normal;
    memcpy(&Wv,Vs,64);
    if(!D3DXMatrixInverse(&Inverse,nullptr,&Wv)) return false;
    D3DXMatrixTranspose(&Normal,&Inverse);memcpy(Vs+32,&Normal,64);
    memcpy(Vs+48,DeviceStates_.TextureTransforms[0].Values,64);
    Vs[64]=Transform ? 1.0f:0.0f;
    Vs[65]=(Fvf&D3DFVF_DIFFUSE) && RenderStates_.GetPending(D3DRS_COLORVERTEX) &&
        RenderStates_.GetPending(D3DRS_DIFFUSEMATERIALSOURCE)==D3DMCS_COLOR1 ? 1.0f:0.0f;
    unsigned FogMode=RenderStates_.GetPending(D3DRS_FOGTABLEMODE);
    if(!FogMode) FogMode=RenderStates_.GetPending(D3DRS_FOGVERTEXMODE);
    if(!RenderStates_.GetPending(D3DRS_FOGENABLE)) FogMode=0;
    const bool Membrane=E->SurfaceShader==RPSurfaceLairMembrane;
    float Ps[16]={0,E->NomadEnergyStrength,
        Membrane?1.0f:0.0f,E->SurfaceMaterial.Diffuse.a,
        8.0f/Desc.Width,8.0f/Desc.Height,0,0,
        FloatBits(RenderStates_.GetPending(D3DRS_FOGSTART)),FloatBits(RenderStates_.GetPending(D3DRS_FOGEND)),
        FloatBits(RenderStates_.GetPending(D3DRS_FOGDENSITY)),float(FogMode),
        RenderStates_.GetPending(D3DRS_RANGEFOGENABLE)?1.0f:0.0f,Membrane?1.0f:0.0f,0,0};
    // Capture native constants, addressing, alpha test, culling, depth and FVF.
    // Scoped to a handful of authored materials, never the general surface path.
    if(FAILED(Device_->CreateStateBlock(D3DSBT_ALL,&E->NomadEnergySaved))) return false;
    HRESULT Hr=Rp9SetVertexShader(Device_,E->NomadEnergyVs);
    if(SUCCEEDED(Hr)) Hr=Rp9SetPixelShader(Device_,E->NomadEnergyPs);
    if(SUCCEEDED(Hr)) Hr=Rp9SetVertexConstants(Device_,0,Vs,17);
    if(SUCCEEDED(Hr)) Hr=Rp9SetPixelConstants(Device_,0,Ps,4);
    const D3DRENDERSTATETYPE States[]={D3DRS_ALPHABLENDENABLE,D3DRS_SRCBLEND,D3DRS_DESTBLEND,
        D3DRS_BLENDOP,D3DRS_SEPARATEALPHABLENDENABLE,D3DRS_ZWRITEENABLE,D3DRS_ZFUNC,D3DRS_FOGENABLE,D3DRS_COLORWRITEENABLE};
    const DWORD Values[]={TRUE,D3DBLEND_ONE,D3DBLEND_ONE,D3DBLENDOP_ADD,FALSE,FALSE,D3DCMP_LESSEQUAL,FALSE,
        RenderStates_.GetPending(D3DRS_COLORWRITEENABLE)&7};
    for(unsigned I=0;I<sizeof(States)/sizeof(*States) && SUCCEEDED(Hr);++I) Hr=Device_->SetRenderState(States[I],Values[I]);
    if(FAILED(Hr)) {ExNomadEnergyEnd();return false;}
    return true;
}

void FDirectX9::ExNomadEnergyEnd()
{
    if(!Ex_ || !Ex_->NomadEnergySaved) return;
    Ex_->NomadEnergySaved->Apply();
    Ex_->NomadEnergySaved->Release();Ex_->NomadEnergySaved=nullptr;
    Rp9DeviceCalls().Invalidate(); // state blocks bypass shader/constant mirrors
}
