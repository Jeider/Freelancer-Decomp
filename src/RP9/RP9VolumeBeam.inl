// ALE volume beams: connected round tube with shared rings and smooth normals.
#include "RP9BeamMesh.h"
namespace
{
    const DWORD kVolumeBeamFvf = D3DFVF_XYZ | D3DFVF_NORMAL | D3DFVF_TEX4 |
        D3DFVF_TEXCOORDSIZE4(0) | D3DFVF_TEXCOORDSIZE2(1) | D3DFVF_TEXCOORDSIZE4(2) | D3DFVF_TEXCOORDSIZE2(3);
    bool VolumeNameMatches(std::string const& list, const char* name)
    {
        if (!name) return false;
        std::string lower(name);
        for (char& c : lower) if (c >= 'A' && c <= 'Z') c += 'a' - 'A';
        size_t pos = 0;
        while (pos < list.size())
        {
            size_t end = list.find(',', pos);
            if (end == std::string::npos) end = list.size();
            std::string token = list.substr(pos, end - pos);
            size_t a = token.find_first_not_of(" \t"), b = token.find_last_not_of(" \t");
            if (a != std::string::npos)
            {
                token = token.substr(a, b - a + 1);
                if (token == "*" || lower.find(token) != std::string::npos) return true;
            }
            pos = end + 1;
        }
        return false;
    }
}

void FDirectX9::ExVolumeBeamPrepare()
{
    auto* ex = Ex_;
    ex->VolumeBeamEnabled = ReadShadowSetting("beam_volume", 1, 0, 1) > .5f;
    ex->VolumeBeamNodes = ReadLowerRenderString("beam_volume_nodes", "laser");
    ex->VolumeBeamCore = ReadShadowSetting("beam_volume_core", .18f, .03f, .7f);
    ex->VolumeBeamStrength = ReadShadowSetting("beam_volume_strength", 1, 0, 4);
    ex->VolumeBeamTrailNodes = ReadLowerRenderString("beam_volume_trail_nodes", "trail");
    ex->VolumeBeamTrailFade = ReadShadowSetting("beam_volume_trail_fade", 10, 0, 1000);
    D3DCAPS9 caps = {};
    if (!ex->VolumeBeamEnabled || !Device_ || FAILED(Device_->GetDeviceCaps(&caps)) ||
        caps.VertexShaderVersion < D3DVS_VERSION(3, 0) || caps.PixelShaderVersion < D3DPS_VERSION(3, 0)) return;
    if (ex->VolumeBeamVs && ex->VolumeBeamPs) return;
    if (!ExCompileShaderPair("beam_volume.hlsl", &ex->VolumeBeamVs, &ex->VolumeBeamPs, "VSMain", "PSMain"))
        ExLogf(kExFdumpWarning, "WARNING", __LINE__, "ALE volume beam unavailable; keeping native ribbons");
    else ExLogf(kExFdumpNotice, "NOTICE", __LINE__, "ALE volume beams ready; node filters: %s", ex->VolumeBeamNodes.c_str());
}

GENRESULT DACOM_API FDirectX9::VolumeBeamAvailable(const char* name, unsigned long src, unsigned long dst)
{
    // ALE probes immediately before the synchronous draw. Every probe resets
    // the classification, including rejected/empty effects, so it cannot leak.
    if (Ex_) Ex_->VolumeBeamPendingTrail = false;
    if (!Ex_ || !Device_ || !Ex_->VolumeBeamEnabled || !Ex_->VolumeBeamVs || !Ex_->VolumeBeamPs ||
        Ex_->bInPass || Ex_->bShadowDrawing || dst != D3DBLEND_ONE ||
        (src != D3DBLEND_ONE && src != D3DBLEND_SRCALPHA) || !VolumeNameMatches(Ex_->VolumeBeamNodes, name))
        return GR_GENERIC;
    Ex_->VolumeBeamPendingTrail = VolumeNameMatches(Ex_->VolumeBeamTrailNodes, name);
    return GR_OK;
}

GENRESULT DACOM_API FDirectX9::DrawVolumeBeam(const FRPVolumeBeamPoint* points, unsigned long count,
                                            float textureU, unsigned long src)
{
    float const trailFade = Ex_ && Ex_->VolumeBeamPendingTrail ? Ex_->VolumeBeamTrailFade : 0.f;
    if (Ex_) Ex_->VolumeBeamPendingTrail = false; // consume once, even if this draw fails
    if (!Device_ || !Ex_ || !Ex_->VolumeBeamVs || !Ex_->VolumeBeamPs || Ex_->bInPass ||
        Ex_->bShadowDrawing || !points || count < 2 || count > 65535) return GR_GENERIC;
    ExFlushSurfaceInstances();
    D3DXMATRIX view, projection;
    MulMatrix4(Transforms_.World.Values, Transforms_.View.Values, &view.m[0][0]);
    memcpy(&projection, Transforms_.Projection.Values, sizeof(projection));
    const float scale = std::fmax(D3DXVec3Length(reinterpret_cast<const D3DXVECTOR3*>(&view._11)),
        std::fmax(D3DXVec3Length(reinterpret_cast<const D3DXVECTOR3*>(&view._21)),
                  D3DXVec3Length(reinterpret_cast<const D3DXVECTOR3*>(&view._31))));
    std::vector<Rp9BeamMesh::Point> path;
    path.reserve(count);
    float minV=points[0].V,maxV=minV;
    for(unsigned long i=0;i<count;++i)
    {
        auto const& p=points[i];
        Rp9BeamMesh::Point q;
        D3DXVec3TransformCoord(&q.position,reinterpret_cast<const D3DXVECTOR3*>(p.Position),&view);
        q.radius=p.Radius*scale;
        q.colour=D3DXVECTOR4(float((p.Colour>>16)&255)/255,float((p.Colour>>8)&255)/255,
                            float(p.Colour&255)/255,float((p.Colour>>24)&255)/255);
        path.push_back(q);
        minV=std::fmin(minV,p.V);maxV=std::fmax(maxV,p.V);
    }
    bool inside=false;
    // Sample the frame centre for tint, rather than repeating the texture's
    // bright/dark end caps at every particle. The transverse profile is analytic.
    auto vertices=Rp9BeamMesh::Build(path,textureU,(minV+maxV)*.5f,inside);
    if(vertices.empty()) return GR_GENERIC;
    // Opt-in scene capture for reproducing ALE-only failures outside the game.
    // 2 also uses the original ribbon after recording, so diagnosis is playable.
    static int const debug=int(ReadShadowSetting("beam_volume_debug",0,0,2));
    static unsigned captured=0;
    if(debug && captured<8)
    {
        char temp[MAX_PATH]={};
        if(GetTempPathA(MAX_PATH,temp))
        {
            char file[MAX_PATH]={};
            _snprintf_s(file,sizeof(file),_TRUNCATE,"%sfreelancer_beam_%u.txt",temp,captured);
            FILE* out=nullptr;
            if(fopen_s(&out,file,"w")==0 && out)
            {
                fprintf(out,"%lu %.9g %.9g %lu %d\n",count,textureU,(minV+maxV)*.5f,src,inside);
                for(int i=0;i<16;++i)fprintf(out,"%.9g%c",(&projection.m[0][0])[i],i==15?'\n':' ');
                for(auto const& p:path)fprintf(out,"%.9g %.9g %.9g %.9g %.9g %.9g %.9g %.9g\n",
                    p.position.x,p.position.y,p.position.z,p.radius,p.colour.x,p.colour.y,p.colour.z,p.colour.w);
                for(unsigned s=0;s<FRp9RenderStateCache::StateCount;++s)
                    fprintf(out,"rs %u %lu\n",s,RenderStates_.GetPending(s));
                fclose(out);
                IDirect3DBaseTexture9* texture=nullptr;
                if(SUCCEEDED(Device_->GetTexture(0,&texture)) && texture)
                {
                    _snprintf_s(file,sizeof(file),_TRUNCATE,"%sfreelancer_beam_%u.dds",temp,captured);
                    D3DXSaveTextureToFileA(file,D3DXIFF_DDS,texture,nullptr);
                    texture->Release();
                }
                ExLogf(kExFdumpNotice,"NOTICE",__LINE__,"ALE beam scene captured: %s (%lu points, %u vertices)",file,count,unsigned(vertices.size()));
            }
        }
        ++captured;
    }
    if(debug==2) return GR_GENERIC;
    float fog[4] = {FloatBits(RenderStates_.GetPending(kRsFogStart)), FloatBits(RenderStates_.GetPending(kRsFogEnd)),
        FloatBits(RenderStates_.GetPending(kRsFogDensity)), 0};
    if (RenderStates_.GetPending(kRsFogEnable))
    {
        fog[3] = float(RenderStates_.GetPending(kRsFogTableMode));
        if (!fog[3]) fog[3] = float(RenderStates_.GetPending(kRsFogVertexMode));
    }
    FlushDrawState(Device_); // commit ALE's texture and modelview before the scoped pass
    FRPExPassDesc pass = {}; pass.Flags = RPExPassKeepDepth;
    if (BeginExPass(&pass) != GR_OK) return GR_GENERIC;
    // A null pass target retains the caller's target and depth (including HDR).
    // SetRenderTarget resets the hardware viewport; restore its original subrect.
    HRESULT hr = Device_->SetViewport(&Ex_->SavedViewport);
    if (FAILED(hr)) { EndExPass(); return GR_GENERIC; }
    ExSetPassState(this,D3DRS_ZENABLE,Ex_->SavedDepth ? TRUE : FALSE);
    ExSetPassState(this,D3DRS_ZWRITEENABLE,FALSE);
    ExSetPassState(this,D3DRS_CULLMODE,D3DCULL_NONE);
    ExSetPassState(this,D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
    ExSetPassState(this,D3DRS_ALPHABLENDENABLE,TRUE);
    ExSetPassState(this,D3DRS_SRCBLEND,D3DBLEND_ONE);
    ExSetPassState(this,D3DRS_DESTBLEND,D3DBLEND_ONE);
    ExSetPassState(this,D3DRS_BLENDOP,D3DBLENDOP_ADD);
    ExSetPassState(this,D3DRS_COLORWRITEENABLE,7);
    StreamCache_.SelectVertexStream(nullptr,kVolumeBeamFvf);
    FlushDrawState(Device_);
    Rp9SetVertexShader(Device_,Ex_->VolumeBeamVs);
    Rp9SetPixelShader(Device_,Ex_->VolumeBeamPs);
    Rp9SetVertexConstants(Device_,0,&projection.m[0][0],4);
    float style[4]={Ex_->VolumeBeamCore,Ex_->VolumeBeamStrength,src==D3DBLEND_SRCALPHA?1.f:0.f,inside?-1.f:1.f};
    Rp9SetPixelConstants(Device_,4,style,1);
    Rp9SetPixelConstants(Device_,5,fog,1);
    float const nearPlane = projection._33 != 0 ? std::fmax(0.f,-projection._43/projection._33) : 0.f;
    float cameraFade[4]={nearPlane,trailFade>0 ? 1.f/trailFade : 0.f,0,0};
    Rp9SetPixelConstants(Device_,6,cameraFade,1);
    for (size_t first=0; first<vertices.size(); first+=1536)
    {
        unsigned const n = unsigned((std::min)(size_t(1536),vertices.size()-first));
        hr=Device_->DrawPrimitiveUP(D3DPT_TRIANGLELIST,n/3,vertices.data()+first,sizeof(Rp9BeamMesh::Vertex));
        if (FAILED(hr)) break;
        ExNoteDraw(n/3);
    }
    StreamCache_.Reset();
    EndExPass();
    // Never draw the old ribbon over a partially submitted volume on failure.
    if (FAILED(hr)) ExLogf(kExFdumpWarning,"WARNING",__LINE__,"ALE volume beam draw failed: 0x%08x",unsigned(hr));
    return GR_OK;
}
