// New port feature, not reconstructed Beta code. No borrowed HUD source/assets.
#include "hud_starlancer_radar.h"
#include "radar_projection.h"
#include "radar_frame.h"

#include "common_cequip.h"
#include "common_cobject.h"
#include "common_csys.h"
#include "common_iface.h"
#include "common_ini.h"
#include "DALib.h"
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

namespace
{
    HUDFACTORY<HUD_StarlancerRadar> RadarFactory("StarlancerRadar");
    RadarProjection::BatchSpace DrawSpace = {};
    unsigned const ShipMask = 0x7f0000u;
    // stations, docking rings, jump gates/holes, platforms, depots, satellites.
    // Excludes planets, suns, asteroids, trade-lane rings, loot and projectiles.
    unsigned const SolarMask = 0x10u | 0x20u | 0x40u | 0x100u | 0x800u | 0x1000u | 0x2000u | 0x8000u;

    struct Blip
    {
        RadarProjection::Contact point;
        unsigned color;
        bool selected;
        bool ship;
    };

    unsigned Color(unsigned rgb, float alpha)
    {
        return (unsigned(RadarProjection::Bounded(alpha, 0, 1, 0.8f) * 255.0f) << 24) | (rgb & 0xffffffu);
    }

    void Line(float ax, float ay, float bx, float by, unsigned color, float width = 1.0f)
    {
        float a[3], b[3];
        RadarProjection::ToBatch(DrawSpace, ax, ay, a);
        RadarProjection::ToBatch(DrawSpace, bx, by, b);
        // Same pixel-space, feathered line batch used by native target brackets.
        // It owns state setup/restore and capacity flushing; no raw RP9 state.
        Win3DImmedDrawLine(a, b, color, color & 0xffffffu, width);
    }

    void DrawBlip(Blip const& b, float alpha, float size)
    {
        auto const& p = b.point;
        unsigned const color = Color(b.color, alpha);
        Line(p.x, p.baseY, p.x, p.tipY, Color(b.color, alpha * 0.48f), 0.8f);
        if (b.ship)
        {
            Line(p.x, p.tipY-size, p.x+size, p.tipY, color);
            Line(p.x+size, p.tipY, p.x, p.tipY+size, color);
            Line(p.x, p.tipY+size, p.x-size, p.tipY, color);
            Line(p.x-size, p.tipY, p.x, p.tipY-size, color);
        }
        else
        {
            Line(p.x-size, p.tipY-size, p.x+size, p.tipY-size, color);
            Line(p.x+size, p.tipY-size, p.x+size, p.tipY+size, color);
            Line(p.x+size, p.tipY+size, p.x-size, p.tipY+size, color);
            Line(p.x-size, p.tipY+size, p.x-size, p.tipY-size, color);
        }
        if (b.selected)
        {
            float const s = size + 3;
            unsigned const selected = Color(0xffefb0, alpha);
            Line(p.x-s-2, p.tipY-s, p.x-s-2, p.tipY+s, selected);
            Line(p.x+s+2, p.tipY-s, p.x+s+2, p.tipY+s, selected);
        }
    }
}

HUD_StarlancerRadar::HUD_StarlancerRadar(INI_Reader& reader)
{
    HUDItem::Name = "StarlancerRadar";
    while (reader.read_value())
    {
        if (reader.is_value("enabled")) enabled = reader.get_value_bool(0);
        else if (reader.is_value("show_solars")) showSolars = reader.get_value_bool(0);
        else if (reader.is_value("center")) { centerX = reader.get_value_float(0); centerY = reader.get_value_float(1); }
        else if (reader.is_value("radius")) radius = reader.get_value_float(0);
        else if (reader.is_value("ellipse")) ellipse = reader.get_value_float(0);
        else if (reader.is_value("elevation")) elevation = reader.get_value_float(0);
        else if (reader.is_value("opacity")) opacity = reader.get_value_float(0);
        else if (reader.is_value("range_index")) rangeIndex = reader.get_value_int(0);
        else if (reader.is_value("range_scales"))
            for (int i = 0; i < 3; ++i) ranges[i] = reader.get_value_float(i);
        else if (reader.is_value("max_contacts")) maxContacts = reader.get_value_int(0);
    }
    rangeIndex = (std::max)(0, (std::min)(2, rangeIndex));
    maxContacts = (std::max)(1, (std::min)(256, maxContacts));
    opacity = RadarProjection::Bounded(opacity, 0, 1, 0.8f);
}

bool HUD_StarlancerRadar::Init()
{
    // With no section the factory is never invoked; a disabled section creates
    // no active item, scanner work, assets or rendering work.
    FDUMP(0x100002, "STARLANCER_RADAR Init path='%s' enabled=%d center=%.3f,%.3f radius=%.3f opacity=%.3f\n",
          GetHudIniPath(), enabled ? 1 : 0, centerX, centerY, radius, opacity);
    if (!enabled)
        return false;
    SetOffset(0.0f, 0.0f, -1.0f);
    SetPosition(Position);
    Win3D::SetName("HUD_StarlancerRadar");
    ClassName = "HUD_StarlancerRadar";
    // Register in the same late Win3D pass as DamageIndicator/CruiseProgress.
    // HUDItem::Render remains a no-op; no immediate early-camera flush occurs.
    return Win3D::Create(nullptr, nullptr);
}

void HUD_StarlancerRadar::ReportOnce(unsigned bit, char const* reason)
{
    if (!(reportedReasons & bit))
    {
        reportedReasons |= bit;
        FDUMP(0x100002, "STARLANCER_RADAR %s\n", reason);
    }
}

void HUD_StarlancerRadar::Draw()
{
    FSpaceCamera* const camera = Win3DGetCamera();
    if (!enabled || GetGameOption(kGameOptInterfaceGroup)==0 || GetGameOption(kGameOptHud)==0)
        return;
    if (!camera || !DALib::Pipeline)
    { ReportOnce(1, "skip: UI camera/pipeline unavailable"); return; }
    if (G_bNnScreenUp || IsLetterboxVisible())
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
    float const range = scanner ? RadarProjection::EffectiveRange(scanner->GetRadarRange(), ranges[rangeIndex]) : 0;
    if (!scanner || range <= 0)
        ReportOnce(32, "scanner absent/suppressed: drawing empty dimmed frame");
    float const frameOpacity = opacity * (scanner && range > 0 ? 1.0f : 0.55f);
    int const* const view = camera->GetViewport();
    if (!view)
    { ReportOnce(64, "skip: camera viewport unavailable"); return; }
    RadarProjection::Layout layout;
    if (!RadarProjection::MakeLayout({view[0],view[1],view[2],view[3]}, centerX, centerY, radius, ellipse, elevation, layout))
    { ReportOnce(128, "skip: invalid viewport/layout"); return; }

    unsigned const mask = ShipMask | (showSolars ? SolarMask : 0);
    // Add only the requested types to the native cache. Never clear it: other
    // HUD consumers share it. Its own filter applies scanner interference.
    if (scanner && range > 0) scanner->scan_for_types(mask);
    ScanList const* const scans = scanner && range > 0 ? &scanner->Scans : nullptr;
    int const count = scans ? (std::max)(0, (std::min)(256, scans->Count)) : 0;
    Blip blips[256];
    int used = 0;
    IObjRW* selected = nullptr;
    player->get_target(selected);
    Transform const& transform = player->get_transform();
    unsigned const playerId = player->get_id();
    for (int i = 0; i < count; ++i)
    {
        IObjRW* const contact = ObjRwFromWatchable(const_cast<Watchable*>(scans->Entries[i].target()));
        if (!contact)
            continue;
        unsigned type = 0;
        if (contact->get_type(type) != 0 ||
            !RadarProjection::Accept(contact->get_id(), playerId, type, mask, contact->is_targetable(), contact->is_dying()))
            continue;
        Vector const& position = contact->get_position();
        RadarProjection::Contact point;
        if (!RadarProjection::Project({position.x,position.y,position.z},
                                      {transform.Translation.x,transform.Translation.y,transform.Translation.z},
                                      transform.Rotation.E, range, layout, point))
            continue;
        // Match native HUD: the contact's attitude towards the player matters.
        int const attitude = GetAttitudeClass(player, contact);
        unsigned const color = attitude < 0 ? 0xff775f : attitude > 0 ? 0x77e8ad : 0x8bc9e8;
        blips[used++] = {point, color, contact == selected, (type & ShipMask) != 0};
    }
    std::sort(blips, blips + used, [](Blip const& a, Blip const& b) {
        if (a.selected != b.selected) return a.selected;
        return a.point.distanceSquared < b.point.distanceSquared;
    });
    used = (std::min)(used, maxContacts);
    float const blipSize = (std::max)(2.0f, layout.radius * 0.026f);
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
        if (blips[i].point.below) DrawBlip(blips[i], frameOpacity * 0.72f, blipSize);

    RadarFrame::Emit(layout, rangeIndex, frameOpacity, Line);
    for (int i = used - 1; i >= 0; --i)
        if (!blips[i].point.below) DrawBlip(blips[i], frameOpacity, blipSize);
    if (!reportedDraw)
    {
        reportedDraw = true;
        FDUMP(0x100002, "STARLANCER_RADAR first UI draw: contacts=%d scanner=%d range=%.1f viewport=%d,%d,%d,%d center=%.1f,%.1f radius=%.1f queued_vertices=%d\n",
              used, scanner ? 1 : 0, range, left, top, width, height, layout.x, layout.y, layout.radius, G_ImmedBatchB.VertCount);
    }
    // Do not retain engine object pointers between frames or system loads.
}
