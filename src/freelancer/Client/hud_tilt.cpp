#include "hud_tilt.h"
#include "hud_tilt_math.h"
namespace
{
    float ConfiguredDegrees = 0;
}
float HudTilt::ConfiguredAngle() { return ConfiguredDegrees; }
void HudTilt::SetConfiguredAngle(float degrees)
{
    ConfiguredDegrees = std::isfinite(degrees) ?
        std::round(std::fmax(0.f, std::fmin(MaxAngleDegrees, degrees)) / AngleStepDegrees) * AngleStepDegrees : 0;
    SetAngle(ConfiguredDegrees);
}
#ifdef FREELANCER_RP9
#include "render_ex.h"
#include "win3d.h"
#include "win3d_renderables.h"
#include "win3d_render.h"
#include "screen_quad_state.h"
#include "space_camera.h"
#include "globals.h"
#include "DALib.h"
#include "render/IRenderPipeline.h"
#include "render/IRenderPipelineEx.h"
#include "render/shading.h"
#include <cstring>

namespace
{
    FRPExTexture* Target = nullptr;
    FRPExProgram* Program = nullptr;
    float Degrees = 0;
    bool Tried = false, Ready = false, Capturing = false, Flat = false;
    int InputSide = 0, CaptureSide = 0;

    int Side(Win3D const* object)
    {
        if (!object || !Ready || HudTilt::Angle() == 0) return 0;
        auto* root = object;
        for (auto* w = object; w; w = w->Parent)
        {
            if (!std::strcmp(w->Name,"LootButton") || !std::strcmp(w->Name,"TargetTradeButton") ||
                !std::strcmp(w->Name,"SpecialModeText") || !std::strcmp(w->Name,"SpecialModeTextCancel")) return 0;
            root = w;
        }
        if (!std::strcmp(root->Name,"HUD_Status") || !std::strcmp(root->Name,"HUD_Health")) return 1;
        if (!std::strcmp(root->Name,"HUD_Target") || !std::strcmp(root->Name,"HUD_Targeting") ||
            !std::strcmp(root->Name,"HUD_ContactList")) return -1;
        return 0;
    }
    HudTiltTransform GetTiltTransform(int side)
    {
        return HudTiltTransform::Make(static_cast<float>(G_RenderSurfaceWidth),
            static_cast<float>(G_RenderSurfaceHeight), side, HudTilt::Angle());
    }
    void Flush()
    {
        Win3DImmedBatchFlushAll(); Win3DImmedBatchReset();
        ButtonMontageFlushBatch(); ButtonMontageEnsure();
        // FontString queues glyphs in its own ScreenQuad material list. Drain that
        // list while this panel's target is still bound, including when switching
        // to/from a centred child. Otherwise Win3DDrawAll paints the text flat later.
        UiOverlayPrepPipeline();
        DALib::MaterialBatcher->FlushAll(1);
    }
    void Route(bool flat)
    {
        if (!Capturing || flat == Flat) return;
        Flush();
        RenderEx::GetPipelineEx()->SetExRenderTarget(flat ? nullptr : Target, 1);
        ScreenQuadInvalidateStateCache();
        Flat = flat;
    }
    bool Ensure()
    {
        if (Tried) return Ready;
        if (!RenderEx::IsAvailable() || HudTilt::Angle() == 0) return false;
        FRPExCaps caps = {}; caps.Size = sizeof(caps);
        auto* ex = RenderEx::GetPipelineEx();
        if (ex->GetExCaps(&caps) != GR_OK) return false;
        Tried = true;
        if (!caps.bHudSurface) return false;
        if (Program && Target) { Ready = true; return true; }
        const FRPExRenderTargetDesc desc = {0,0,1.f,RPExFormatA8R8G8B8};
        Ready = ex->CreateExProgram(RenderEx::GetExtraData(), "SHADERS\\hud_tilt.hlsl",
            "VSMain", "PSMain", &Program) == GR_OK &&
            ex->CreateExRenderTarget(&desc, &Target) == GR_OK;
        return Ready;
    }
}

float HudTilt::Angle()
{
    return Degrees;
}
void HudTilt::SetAngle(float degrees)
{
    Degrees = std::isfinite(degrees) ? (degrees < 0 ? 0 : degrees > MaxAngleDegrees ? MaxAngleDegrees : degrees) : 0;
}
void HudTilt::Shutdown()
{
    auto* ex = RenderEx::GetPipelineEx();
    if (ex && Target) ex->DestroyExTexture(Target);
    if (ex && Program) ex->DestroyExProgram(Program);
    Target = nullptr; Program = nullptr;
    Tried = Ready = Capturing = Flat = false; InputSide = CaptureSide = 0;
}
bool HudTilt::InputActive() { return InputSide != 0 && Ready && Angle() != 0; }
void HudTilt::MapCursor(int& x, int& y)
{
    if (!InputActive()) return;
    float fx = static_cast<float>(x), fy = static_cast<float>(y);
    if (GetTiltTransform(InputSide).Unproject(fx,fy))
    {
        // Capture may continue outside the panel, but avoid overflow from extreme rays.
        x = static_cast<int>(std::fmax(-100000.f,std::fmin(100000.f,std::round(fx))));
        y = static_cast<int>(std::fmax(-100000.f,std::fmin(100000.f,std::round(fy))));
    }
}
void HudTilt::ProjectTooltip(float* position)
{
    if (!InputActive()) return;
    auto* cam = Win3DGetCamera();
    float depth = -position[2];
    if (!(depth > 0)) return;
    float x = cam->ScreenCenterX + position[0] * cam->XScale / depth;
    float y = cam->ScreenCenterY - position[1] * cam->YScale / depth;
    GetTiltTransform(InputSide).Project(x,y);
    position[0] = (x - cam->ScreenCenterX) * depth / cam->XScale;
    position[1] = (cam->ScreenCenterY - y) * depth / cam->YScale;
}
HudTilt::InputScope::InputScope(Win3D const* object) : Previous(InputSide) { InputSide = Side(object); }
HudTilt::InputScope::~InputScope() { InputSide = Previous; }
HudTilt::DrawScope::DrawScope(Win3D const* object) : Input(object)
{
    if (!object) return;
    if (!Capturing && object->Parent == nullptr && Ensure() && Side(object))
    {
        Flush();
        const FRPExPassDesc pass = {Target,RPExPassKeepDepth | RPExPassClearColor | RPExPassHudSurface,0};
        if (RenderEx::GetPipelineEx()->BeginExPass(&pass) != GR_OK) { Ready = Tried = false; return; }
        Capturing = Owner = true; Flat = false; CaptureSide = Side(object);
        ScreenQuadInvalidateStateCache();
    }
    PreviousFlat = Flat;
    if (Capturing) Route(Side(object) != CaptureSide);
}
HudTilt::DrawScope::~DrawScope()
{
    if (!Owner) { Route(PreviousFlat); return; }
    Flush();
    auto* ex = RenderEx::GetPipelineEx();
    ex->EndExPass(); Capturing = false;
    const FRPExPassDesc pass = {nullptr,0,0};
    if (ex->BeginExPass(&pass) == GR_OK)
    {
        const FRPExSamplerState sampler = {RPExFilterLinear,RPExMipNone,
            RPExAddressClamp,RPExAddressClamp,RPExAddressClamp};
        if (ex->BindExProgram(Program) == GR_OK && ex->BindExTexture(0,Target,&sampler) == GR_OK)
        {
            const auto t = GetTiltTransform(CaptureSide);
            const float panel[4] = {t.PivotX,t.PivotY,t.Cos,t.K};
            const float w = static_cast<float>(G_RenderSurfaceWidth), h = static_cast<float>(G_RenderSurfaceHeight);
            const float surface[4] = {w,h,1.f/w,1.f/h};
            ex->SetExPixelConstants(0,panel,1); ex->SetExPixelConstants(1,surface,1);
            DALib::Pipeline->SetRenderState(D3DRS_ALPHABLENDENABLE,1);
            DALib::Pipeline->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE); // ONE (premultiplied RGB)
            DALib::Pipeline->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA); // INVSRCALPHA
            DALib::Pipeline->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);
            DALib::Pipeline->SetRenderState(static_cast<D3DRENDERSTATETYPE>(206),0); // SEPARATEALPHABLENDENABLE
            RenderEx::GetDrawEx()->DrawFullscreenQuad();
        }
        ex->EndExPass();
    }
    ScreenQuadInvalidateStateCache();
}
#else
float HudTilt::Angle() { return 0; }
void HudTilt::SetAngle(float) {}
void HudTilt::Shutdown() {}
bool HudTilt::InputActive() { return false; }
void HudTilt::MapCursor(int&,int&) {}
void HudTilt::ProjectTooltip(float*) {}
HudTilt::InputScope::InputScope(Win3D const*) : Previous(0) {}
HudTilt::InputScope::~InputScope() {}
HudTilt::DrawScope::DrawScope(Win3D const* object) : Input(object) {}
HudTilt::DrawScope::~DrawScope() {}
#endif
