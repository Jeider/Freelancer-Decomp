// Port radar with vector geometry extracted from the Beta radar ring.
#include "hud_radar.h"
#include "radar_projection.h"
#include "radar_frame.h"
#include "radar_contacts.h"
#include "radar_symbols.h"
#include "hud_status_core.h"
#include "globals.h"
#include "input_manager.h"
#include "nn_button_control.h"

#include "common_cequip.h"
#include "common_cobject.h"
#include "common_cobjdb.h"
#include "common_csys.h"
#include "common_iface.h"
#include "common_ini.h"
#include "common_spatial.h"
#include "DALib.h"
#include "engine/engbase.h"
#include "game_options.h"
#include "nn_modal.h"
#include "player_behavior.h"
#include "space_camera.h"
#include "space_letterbox.h"
#include "star_sys.h"
#include "win3d.h"
#include "win3d_render.h"
#include "win3d_renderables.h"
#include "render/IRenderPipeline.h"

#include <algorithm>
#include <cmath>
#include <cstring>

namespace
{
    HUDFACTORY<HUD_Radar> RadarFactory("Radar");
    HUD_Radar* ActiveRadar = nullptr;
    RadarProjection::BatchSpace DrawSpace = {};

    bool IsParentedSolar(CObject const* object)
    {
        return object && (object->ObjectClass & CObject::ClassSolar) == CObject::ClassSolar &&
            !static_cast<CSolar const*>(object)->GetParentNickname().IsEmpty();
    }

    Archetype::Solar const* SolarArch(CObject const* object)
    {
        return object && (object->ObjectClass & CObject::ClassSolar) == CObject::ClassSolar
            ? static_cast<CSolar const*>(object)->solararch() : nullptr;
    }

    bool MiningInRange(IObjRW* contact,CEScanner const* scanner,Vector const& origin,float range)
    {
        auto const* arch=contact ? SolarArch(contact->cobject()) : nullptr;
        if(!arch || !arch->bRadarMining || arch->bRadarHidden ||
           IsParentedSolar(contact->cobject()) || contact->is_dying()) return false;
        // Unlike the shared CEScanner filter this deliberately accepts explicitly
        // tagged NON_TARGETABLE solars. Detection distance/interference still apply.
        float const interference=contact->get_scanner_interference();
        float const detection=(1.f-interference)*scanner->ScannerArch()->RadarRange;
        if(!std::isfinite(detection) || detection<=0) return false;
        double const reach=(std::min)(range,detection);
        Vector const& pos=contact->get_position();
        double const x=double(pos.x)-origin.x,y=double(pos.y)-origin.y,z=double(pos.z)-origin.z;
        return x*x+y*y+z*z<=reach*reach;
    }

    struct Blip
    {
        RadarProjection::Contact point;
        unsigned color;
        bool selected;
        RadarSymbols::Kind kind;
        float physicalRadius;
    };

    void Line(float ax, float ay, float bx, float by, unsigned color, float width = 1.0f)
    {
        float a[3], b[3];
        RadarProjection::ToBatch(DrawSpace, ax, ay, a);
        RadarProjection::ToBatch(DrawSpace, bx, by, b);
        // Same pixel-space, feathered line batch used by native target brackets.
        // It owns state setup/restore and capacity flushing; no raw RP9 state.
        Win3DImmedDrawLine(a, b, color, color & 0xffffffu, width);
    }

    void DrawBlip(Blip const& b, float alpha, float size,float range,RadarProjection::Layout const& layout)
    {
        RadarSymbols::Emit(b.point,b.kind,b.physicalRadius,range,layout,b.color,b.selected,alpha,size,Line);
    }
}

HUD_Radar::~HUD_Radar()
{
    if (ActiveRadar==this) ActiveRadar=nullptr;
}

bool RadarMessageAnchor(float& x, float& y)
{
    return ActiveRadar && ActiveRadar->MessageAnchor(x,y);
}

bool HUD_Radar::MessageAnchor(float& x, float& y) const
{
    auto* camera=Win3DGetCamera();
    auto const* view=camera ? camera->GetViewport() : nullptr;
    RadarProjection::Layout layout={};
    if (!enabled || !view || camera->XScale<=0 || camera->YScale==0 ||
        !RadarProjection::MakeLayout({view[0],view[1],view[2],view[3]},
                                     centerX,centerY,radius,ellipse,elevation,layout)) return false;
    x=(layout.x-camera->ScreenCenterX)/camera->XScale;
    y=(layout.y-layout.radius*layout.ellipse-camera->ScreenCenterY)/camera->YScale+.045f;
    return true;
}

HUD_Radar::HUD_Radar(INI_Reader& reader)
{
    HUDItem::Name = "Radar";
    while (reader.read_value())
    {
        if (reader.is_value("enabled")) enabled = reader.get_value_bool(0);
        else if (reader.is_value("show_solars")) showSolars = reader.get_value_bool(0);
        else if (reader.is_value("center")) { centerX = reader.get_value_float(0); centerY = reader.get_value_float(1); }
        else if (reader.is_value("radius")) radius = reader.get_value_float(0);
        else if (reader.is_value("ellipse")) ellipse = reader.get_value_float(0);
        else if (reader.is_value("elevation")) elevation = reader.get_value_float(0);
        else if (reader.is_value("sweep_speed")) sweepSpeed = reader.get_value_float(0);
        else if (reader.is_value("opacity")) opacity = reader.get_value_float(0);
        else if (reader.is_value("range_index")) rangeIndex = reader.get_value_int(0);
        else if (reader.is_value("range_scales"))
            for (int i = 0; i < 3; ++i) ranges[i] = reader.get_value_float(i);
        else if (reader.is_value("max_contacts")) maxContacts = reader.get_value_int(0);
    }
    rangeIndex = (std::max)(0, (std::min)(2, rangeIndex));
    defaultRangeIndex = static_cast<unsigned>(rangeIndex);
    maxContacts = (std::max)(1, (std::min)(256, maxContacts));
    opacity = RadarProjection::Bounded(opacity, 0, 1, 0.8f);
    sweepSpeed = RadarProjection::Bounded(sweepSpeed, 0, 180, 45);
    for (float& value : ranges) value = RadarProjection::Bounded(value, .01f, 1.f, 1.f);
    std::sort(ranges, ranges + 3);
}

bool HUD_Radar::Init()
{
    // With no section the factory is never invoked; a disabled section creates
    // no active item, scanner work, assets or rendering work.
    FDUMP(0x100002, "HUD_RADAR Init path='%s' enabled=%d center=%.3f,%.3f radius=%.3f opacity=%.3f\n",
          GetHudIniPath(), enabled ? 1 : 0, centerX, centerY, radius, opacity);
    if (!enabled)
        return false;
    SetOffset(0.0f, 0.0f, -1.0f);
    SetPosition(Position);
    Win3D::SetName("HUD_Radar");
    ClassName = "HUD_Radar";
    Flags &= ~kWin3DPickable;
    // Register in the same late Win3D pass as DamageIndicator/CruiseProgress.
    // HUDItem::Render remains a no-op; no immediate early-camera flush occurs.
    if (!Win3D::Create(nullptr, nullptr)) return false;
    float const zero[3] = {}, half[3] = {.022f,.022f,0};
    background=CreateStaticControl("RadarBackground", "Interface\\HUD\\HUD_radar_background.3db",
        zero,nullptr,zero,0,0,0,1,0,0,1,0,0,0,zero);
    if (!background || !ClientMeshHolderHasInstance(&background->MeshHolder)) return false;
    background->Flags &= ~kWin3DPickable;
    char const* const paths[] = {"Interface\\HUD\\HUD_radar_zoomin.3db",
                                "Interface\\HUD\\HUD_radar_zoomout.3db",
                                "Interface\\HUD\\HUD_radar.3db"};
    for (int i=0;i<3;++i)
    {
        auto* control = CreateButtonControl(i==0 ? "RadarZoomIn" : i==1 ? "RadarZoomOut" : "RadarToggle",
            paths[i], nullptr, "ui_select_item", nullptr, zero, nullptr, half,
            0, 0, 0, 0, i==0 ? 0x4d5 : i==1 ? 0x4d6 : 1444, 0, 0);
        if (!control) return false;
        if (i<2) zoomButtons[i]=control; else toggleButton=control;
        auto* button = static_cast<NnButtonControl*>(control);
        // Use the real NavMap +/- meshes, with independent transforms and native input.
        button->SetMesh(paths[i], nullptr);
        button->MontageTile = nullptr;
        if (ClientMeshHolderHasInstance(&button->MeshHolder))
        {
            float extent=0, origin[3]={};
            DALib::Engine->GetInstanceExtent(button->MeshHolder.EngineInstance,1,&extent,origin);
            if (std::isfinite(extent) && extent>0)
            {
                float orientation[9];
                for(int axis=0;axis<9;++axis) orientation[axis]=button->Orientation[axis]*.022f/extent;
                button->SetOrientation(orientation);
            }
        }
    }
    ActiveRadar=this;
    UpdateButtons();
    return true;
}

void HUD_Radar::Update()
{
    float const dt=static_cast<float>(GetClientFrameTimeCapped());
    sweepAngle = std::fmod(sweepAngle + sweepSpeed * 0.01745329252f *
                         dt, 6.28318530718f);
    auto* player=static_cast<IObjRW*>(GetPlayerObjRW());
    auto const* object=player && player!=reinterpret_cast<IObjRW*>(static_cast<intptr_t>(-0xc))
        ? player->cobject() : nullptr;
    if (object && (object->ObjectClass & CObject::ClassShip)==CObject::ClassShip && !IsSpaceInitInProgress())
    {
        unsigned const system=StarSysGetActiveSystemId();
        bool const inLane=static_cast<CShip const*>(object)->is_using_tradelane();
        if ((lastSystem && system!=lastSystem) || (inLane && !wasInLane))
        {
            ringMotion.ship=player->get_id();
            ringMotion.FaceForward();
        }
        lastSystem=system;
        wasInLane=inLane;
        // Native angular velocity is world-space; steering uses ship-local X/Y.
        Vector const velocity=player->get_angular_velocity();
        auto const& r=player->get_transform().Rotation.E;
        float const pitch=velocity.x*r[0][0]+velocity.y*r[1][0]+velocity.z*r[2][0];
        float const yaw=velocity.x*r[0][1]+velocity.y*r[1][1]+velocity.z*r[2][1];
        bool const steeringActive=!inLane && (IsMouseFlightLocked() || IsMouseFlightHoldThresholdReached());
        ringMotion.Step(player->get_id(),inLane ? 0 : pitch,inLane ? 0 : yaw,player->get_angular_speed_XY(1,0),
                        player->get_angular_speed_XY(0,1),dt,steeringActive);
    }
    else ringMotion.rate=0;
    UpdateButtons();
    Win3D::Update();
}

bool HUD_Radar::CanShow() const
{
    return enabled && GetGameOption(kGameOptInterfaceGroup) && GetGameOption(kGameOptHud) &&
        !G_bNnScreenUp && !IsLetterboxVisible() && !IsSpaceInitInProgress() &&
        GetClientMouseCursorDrawFlag() && GetPlayerObjRW();
}

void HUD_Radar::UpdateButtons()
{
    // Re-read after loading another save even if this HUD instance survived.
    rangeIndex = static_cast<int>(GetSavedRadarRange(defaultRangeIndex));
    auto* camera = Win3DGetCamera();
    RadarProjection::Layout layout = {};
    auto const* view = camera ? camera->GetViewport() : nullptr;
    bool const visible = CanShow() && view && camera->XScale>0 && camera->YScale!=0 &&
        RadarProjection::MakeLayout({view[0],view[1],view[2],view[3]},
                                    centerX,centerY,radius,ellipse,elevation,layout);
    bool const on=GetSavedRadarEnabled();
    if(toggleButton)
    {
        toggleButton->SetProperty(1,visible ? 0 : 1,0);
        toggleButton->SetProperty(0xc,on ? 1 : 0,0);
        // In the gap between Targeting and HUD_Core's 100% indicator.
        toggleButton->SetOffset(-.195f,-.37f,0);
    }
    if (background)
    {
        background->SetProperty(1,visible && on ? 0 : 1,0);
        if (visible)
        {
            float const scale=layout.radius*.93f/camera->XScale;
            float const vertical=layout.radius*.93f*layout.ellipse/std::fabs(camera->YScale);
            float const orientation[9]={scale,0,0,0,vertical,0,0,0,1};
            background->SetOrientation(orientation);
            background->SetOffset((layout.x-camera->ScreenCenterX)/camera->XScale,
                                  (layout.y-camera->ScreenCenterY)/camera->YScale,-1.0f);
        }
    }
    for(int i=0;i<2;++i)
    {
        auto* button = static_cast<NnButtonControl*>(zoomButtons[i]);
        if (!button) continue;
        button->SetProperty(1,visible && on ? 0 : 1,0);
        bool const usable = RadarProjection::ZoomIndex(rangeIndex,i==0)!=rangeIndex;
        button->SetFlags331(static_cast<unsigned char>((button->GetFlags331() & ~2u) | (usable ? 2u : 0u)));
        if (!visible) continue;
        float const spacing=camera->XScale*.045f;
        float const x=layout.x+layout.radius*.63f+(i==1 ? spacing : 0);
        float const y=layout.y+layout.radius*layout.ellipse;
        button->SetOffset((x-camera->ScreenCenterX)/camera->XScale,
                          (y-camera->ScreenCenterY)/camera->YScale,0);
    }
}

intptr_t HUD_Radar::SetProperty(int msg, uintptr_t a, uintptr_t b)
{
    if (msg==0x26 && CanShow() && !HudIsMousePickBlocked())
    {
        if (a && a==reinterpret_cast<uintptr_t>(toggleButton))
        {
            SetSavedRadarRange(static_cast<unsigned>(rangeIndex));
            SetSavedRadarEnabled(!GetSavedRadarEnabled());
            UpdateButtons();
            return 1;
        }
        if (GetSavedRadarEnabled())
        for(int i=0;i<2;++i)
            if (a==reinterpret_cast<uintptr_t>(zoomButtons[i]))
            {
                rangeIndex=RadarProjection::ZoomIndex(rangeIndex,i==0);
                SetSavedRadarRange(static_cast<unsigned>(rangeIndex));
                UpdateButtons();
                return 1;
            }
    }
    return WinControl::SetProperty(msg,a,b);
}

void HUD_Radar::ReportOnce(unsigned bit, char const* reason)
{
    if (!(reportedReasons & bit))
    {
        reportedReasons |= bit;
        FDUMP(0x100002, "HUD_RADAR %s\n", reason);
    }
}

void HUD_Radar::Draw()
{
    if (!CanShow()) return;
    if (toggleButton && (toggleButton->Flags & kWin3DVisible)) toggleButton->Draw();
    // The toggle remains available while off; scanning and disk drawing stop.
    if (!GetSavedRadarEnabled()) return;
    if (background && (background->Flags & kWin3DVisible)) background->Draw();
    FSpaceCamera* const camera = Win3DGetCamera();
    if (!enabled || GetGameOption(kGameOptInterfaceGroup)==0 || GetGameOption(kGameOptHud)==0)
        return;
    if (!camera || !DALib::Pipeline)
    { ReportOnce(1, "skip: UI camera/pipeline unavailable"); return; }
    if (G_bNnScreenUp || IsLetterboxVisible() || IsSpaceInitInProgress() ||
        !GetClientMouseCursorDrawFlag())
    { ReportOnce(2, "skip: NeuroNet/letterbox overlay"); return; }
    if (!G_ImmedBatchB.Vb || !G_ImmedBatchB.Ib || !G_ImmedBatchB.Draw || !G_ImmedBatchB.VertCursor)
    { ReportOnce(4, "skip: native HUD batch unavailable"); return; }
    IObjRW* const player = static_cast<IObjRW*>(GetPlayerObjRW());
    if (!player || player == reinterpret_cast<IObjRW*>(static_cast<intptr_t>(-0xc)))
    { ReportOnce(8, "skip: player unavailable"); return; }
    CObject const* const object = player->cobject();
    if (!object || (object->ObjectClass & CObject::ClassShip) != CObject::ClassShip)
    { ReportOnce(16, "skip: player is not a ship"); return; }
    CShip const* const ship = static_cast<CShip const*>(object);
    CEScanner* const scanner = CEScanner::cast(const_cast<CEquip*>(ship->EquipManager.FindFirst(EquipTypeScanner)));
    float const range = scanner && scanner->IsFunctioning()
        ? RadarProjection::EffectiveRange(scanner->GetRadarRange(), ranges[rangeIndex]) : 0;
    if (!scanner || range <= 0)
        ReportOnce(32, "scanner absent/suppressed: drawing empty dimmed frame");
    float const frameOpacity = opacity * (scanner && range > 0 ? 1.0f : 0.55f);
    int const* const view = camera->GetViewport();
    if (!view)
    { ReportOnce(64, "skip: camera viewport unavailable"); return; }
    RadarProjection::Layout layout;
    if (!RadarProjection::MakeLayout({view[0],view[1],view[2],view[3]}, centerX, centerY, radius, ellipse, elevation, layout))
    { ReportOnce(128, "skip: invalid viewport/layout"); return; }

    unsigned const mask = RadarSymbols::ShipMask | RadarSymbols::LootMask | (showSolars ? RadarSymbols::SolarMask : 0);
    // Add only the requested types to the native cache. Never clear it: other
    // HUD consumers share it. Its own filter applies scanner interference.
    if (scanner && range > 0) scanner->scan_for_types(mask);
    ScanList const* const scans = scanner && range > 0 ? &scanner->Scans : nullptr;
    int const count = scans ? (std::max)(0, (std::min)(256, scans->Count)) : 0;
    Blip blips[256+0x800]; // Native contacts plus the bounded solar spatial query.
    int used = 0;
    IObjRW* selected = nullptr;
    player->get_target(selected);
    Transform const& transform = player->get_transform();
    unsigned const playerId = player->get_id();
    auto append=[&](IObjRW* contact,bool mining)
    {
        if (!contact || IsParentedSolar(contact->cobject()))
            return;
        auto const* solar=SolarArch(contact->cobject());
        if(solar && (solar->bRadarHidden || (!mining && solar->bRadarMining))) return;
        unsigned type = 0;
        if (contact->get_type(type) != 0 ||
            !RadarProjection::Accept(contact->get_id(), playerId, type, mining ? ~0u : mask,
                                     mining || contact->is_targetable(), contact->is_dying()))
            return;
        auto const kind=mining ? RadarSymbols::Kind::Triangle : RadarSymbols::Classify(type);
        float physicalRadius=0;
        Vector position = contact->get_position();
        if(kind==RadarSymbols::Kind::Planet)
        {
            Vector center;
            if(contact->get_physical_radius(physicalRadius,center)!=0 ||
                !std::isfinite(physicalRadius) || physicalRadius<=0) return;
            position=center; // Physical centre is world-space, including the model offset.
        }
        RadarProjection::Contact point;
        if (!RadarProjection::Project({position.x,position.y,position.z},
                                      {transform.Translation.x,transform.Translation.y,transform.Translation.z},
                                      transform.Rotation.E, range, layout, point,physicalRadius))
            return;
        // Match native HUD: the contact's attitude towards the player matters.
        int const attitude = mining ? 0 : GetAttitudeClass(player, contact);
        unsigned const color = RadarSymbols::ContactColor(kind,attitude);
        blips[used++] = {point, color, contact == selected, kind,physicalRadius};
    };
    for (int i = 0; i < count; ++i)
        append(ObjRwFromWatchable(const_cast<Watchable*>(scans->Entries[i].target())),false);
    if(showSolars && range>0 && ship->ObjectDb)
    {
        auto* bucket=static_cast<ISpatialPartition*>(ship->ObjectDb->GetBucket(0xfdffu));
        if(bucket)
        {
            Geometry::Sphere sphere;
            sphere.Center=transform.Translation;
            sphere.Radius=range;
            FSpatialQueryResult query;
            query.Capacity=0x800;query.Count=0;
            if(bucket->QuerySphere(&sphere,&query))
                for(unsigned i=0;i<(std::min)(query.Count,query.Capacity);++i)
                {
                    auto* contact=static_cast<IObjRW*>(query.Items[i]);
                    if(MiningInRange(contact,scanner,sphere.Center,range)) append(contact,true);
                }
        }
    }
    std::sort(blips, blips + used, [](Blip const& a, Blip const& b) {
        if (a.selected != b.selected) return a.selected;
        return a.point.distanceSquared < b.point.distanceSquared;
    });
    used = (std::min)(used, maxContacts);
    float const blipSize = (std::max)(2.0f, layout.radius * 0.022f);
    // The shared line batch uses Win3D camera's zero-origin ortho, whereas its
    // device viewport can have an offset or different size. Convert absolute
    // pixels into that ortho. Draw now runs inside Win3DDrawAll, which owns the
    // normal frame reset/flush; no private flush can be overwritten by that pass.
    FSpaceCamera* const batchCamera = Win3DGetCamera();
    if (!batchCamera)
        return;
    int const* const ortho = batchCamera->GetViewport();
    int left=0, top=0, width=0, height=0;
    if (!ortho || DALib::Pipeline->GetViewportRect(&left,&top,&width,&height)!=0 || width<=0 || height<=0 || width>32768 || height>32768 ||
        !RadarProjection::MakeBatchSpace({left,top,left+width-1,top+height-1}, {ortho[0],ortho[1],ortho[2],ortho[3]}, DrawSpace))
    { ReportOnce(256, "skip: device viewport/batch mapping invalid"); return; }
    // Back-to-front within each layer; selected/nearest blips draw last.
    for (int i = used - 1; i >= 0; --i)
        if (blips[i].point.below) DrawBlip(blips[i], frameOpacity * 0.72f, blipSize,range,layout);

    RadarFrame::Emit(layout, rangeIndex, frameOpacity, Line, sweepAngle, ringMotion.angle);
    for (int i = used - 1; i >= 0; --i)
        if (!blips[i].point.below) DrawBlip(blips[i], frameOpacity, blipSize,range,layout);
    if (!reportedDraw)
    {
        reportedDraw = true;
        FDUMP(0x100002, "HUD_RADAR first UI draw: contacts=%d scanner=%d range=%.1f viewport=%d,%d,%d,%d center=%.1f,%.1f radius=%.1f queued_vertices=%d\n",
              used, scanner ? 1 : 0, range, left, top, width, height, layout.x, layout.y, layout.radius, G_ImmedBatchB.VertCount);
    }
    for (auto* button : zoomButtons)
        if (button && (button->Flags & kWin3DVisible)) button->Draw();
    // Do not retain engine object pointers between frames or system loads.
}
