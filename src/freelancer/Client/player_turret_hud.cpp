#include "player_turret_hud.h"
#ifdef FREELANCER_PLAYER_AUTO_TURRETS
#include "player_auto_turrets.h"
#include "hud_status_core.h"
#include "nn_button_control.h"
#include "nn_montage_draw.h"
#include "hud_target.h"
#include "common_cequip.h"
#include "common_misc.h"
#include "port_config.h"
#include "DALib.h"
#include "engine/engbase.h"
#include <cmath>
#include <cstring>

namespace PlayerTurretHud
{
namespace
{
    using namespace PlayerAutoTurrets;
    constexpr unsigned Base = 0x7fee0000;
    constexpr int Controls = 11; // master, then ten visible weapon slots
    HUD_Status* owner = nullptr;
    WinControl* buttons[Controls] = {};
    FButtonMontageTile tiles[Controls] = {};
    FButtonMontageTile* originals[Controls] = {};
    unsigned short rowIds[10] = {};

    bool Russian() { return _stricmp(PortLanguage(), "ru") == 0; }
    bool Bind(HUD_Status* host)
    {
        if (owner) return owner == host;
        owner = host;
        char path[1024] = {};
        char const* mesh = "interface\\hud\\HUD_player_auto_turret.3db";
        GetFileSysPath(path, mesh, DALib::Data);
        if (GetFileAttributesA(path) == INVALID_FILE_ATTRIBUTES)
            mesh = "interface\\hud\\HUD_targetedobject.3db";
        for (int i = 0; i < Controls; ++i)
        {
            char name[48]; sprintf_s(name, "PlayerTurretButton%d", i);
            float const radius = i == 0 ? 0.017f : 0.007f;
            float const zero[3] = {}, half[3] = {radius, radius, 0};
            buttons[i] = owner->CreateButtonControl(name, mesh, nullptr, "ui_item_select",
                nullptr, zero, nullptr, half, 0, 1, 0, 0, Base+i, 0, 0);
            if (!buttons[i]) { Release(host); return false; }
            buttons[i]->SetProperty(1, 1, 0);
            auto* button = static_cast<NnButtonControl*>(buttons[i]);
            originals[i] = button->MontageTile;
            if (button->MontageTile)
            {
                tiles[i] = *button->MontageTile; tiles[i].Scale = radius;
                button->MontageTile = &tiles[i];
            }
            if (ClientMeshHolderHasInstance(&button->MeshHolder))
            {
                float extent = 0, unused[3] = {};
                DALib::Engine->GetInstanceExtent(button->MeshHolder.EngineInstance, 1, &extent, unused);
                if (std::isfinite(extent) && extent > 0)
                {
                    float orientation[9];
                    for (int j = 0; j < 9; ++j) orientation[j] = button->Orientation[j] * radius / extent;
                    button->SetOrientation(orientation);
                }
            }
        }
        return true;
    }
    int FindMember(unsigned short id)
    {
        for (unsigned i = 0; i < MemberCount(); ++i)
            if (auto* gun = Member(i)) if (gun->GetID() == id) return int(i);
        return -1;
    }
}

bool Text(unsigned id, std::wstring& text)
{
    if (id == Base || id == Base + 0x20)
        text = Russian() ? L"\u0410\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0438: \u0432\u043a\u043b/\u0432\u044b\u043a\u043b (\u043f\u043e \u0432\u0441\u0435\u043c \u0432\u0440\u0430\u0433\u0430\u043c)" : L"Auto turrets: on/off (all hostiles)";
    else if (id == Base + 0x23)
        text = Russian() ? L"\u0410\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0438: \u0432\u044b\u043a\u043b\u044e\u0447\u0438\u0442\u044c" : L"Auto turrets: off";
    else if (id == Base + 0x21 || id == Base + 0x22)
        text = Russian() ? L"\u0410\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0438: \u0432\u043a\u043b\u044e\u0447\u0438\u0442\u044c" : L"Auto turrets: on";
    else if (id > Base && id < Base + Controls)
        text = Russian() ? L"\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u043e\u0433\u043e\u043d\u044c \u044d\u0442\u043e\u0439 \u0442\u0443\u0440\u0435\u043b\u0438: \u0432\u043a\u043b/\u0432\u044b\u043a\u043b" : L"This turret: automatic fire on/off";
    else return false;
    return true;
}

void Release(HUD_Status const* host)
{
    if (!owner || host != owner) return;
    for (int i = 0; i < Controls; ++i)
        if (buttons[i])
        {
            static_cast<NnButtonControl*>(buttons[i])->MontageTile = originals[i];
            buttons[i]->Destroy(); delete buttons[i]; buttons[i] = nullptr;
        }
    owner = nullptr;
    std::memset(rowIds, 0, sizeof(rowIds));
}

void Update(HUD_Status* host, float const* attachment, bool visible, float x, float y)
{
    if (!Enabled() || !Bind(host)) return;
    Reconcile();
    buttons[0]->SetProperty(1, !visible, 0);
    buttons[0]->SetProperty(0xc, GetMode() != Mode::Manual, 0);
    std::memcpy(buttons[0]->AttachPosition, attachment, sizeof(buttons[0]->AttachPosition));
    buttons[0]->SetOffset(x, y, 0);
}

void UpdateRows(HUD_Status* host)
{
    if (!Enabled() || !Bind(host)) return;
    Reconcile();
    bool const visible = host->bExpanded && host->Field5a0 &&
        !host->ButtonMover::IsActive() && !host->ButtonScaler::IsActive();
    for (int slot = 0; slot < 10; ++slot)
    {
        auto* button = buttons[slot+1];
        rowIds[slot] = 0;
        int const row = host->WeaponTopRow + slot;
        int member = -1;
        if (visible && row >= 0 && row < int(host->Weapons.size()) &&
            (host->WeaponNumberText[slot]->Flags & kWin3DVisible))
            member = FindMember(host->Weapons[row].SubId);
        button->SetProperty(1, member < 0, 0);
        if (member < 0) continue;
        auto* gun = Member(unsigned(member));
        rowIds[slot] = gun->GetID();
        // Armed indicator, not a muzzle-flash light: stays on while waiting for an enemy.
        button->SetProperty(0xc, Owns(gun) && gun->IsFunctioning(), 0);
        auto* anchor = host->WeaponNumberText[slot];
        std::memcpy(button->AttachPosition, anchor->AttachPosition, sizeof(button->AttachPosition));
        button->SetOffset(anchor->Offset[0] - 0.014f, anchor->Offset[1] - 0.008f, anchor->Offset[2]);
    }
}

bool Property(HUD_Status const* host, int msg, uintptr_t control)
{
    if (host != owner || msg != 0x26 || HudIsMousePickBlocked()) return false;
    for (int i = 0; i < Controls; ++i)
        if (reinterpret_cast<uintptr_t>(buttons[i]) == control)
        {
            if (!(buttons[i]->Flags & kWin3DVisible)) return true;
            Reconcile();
            if (i == 0) SetMode(GetMode() == Mode::Manual ? Mode::Hostiles : Mode::Manual);
            else
            {
                int const row = host->WeaponTopRow + i - 1;
                // Ignore stale clicks after scrolling or equipment replacement.
                if (row >= 0 && row < int(host->Weapons.size()) && host->Weapons[row].SubId == rowIds[i-1])
                {
                    int const member = FindMember(rowIds[i-1]);
                    if (member >= 0) ToggleMember(unsigned(member));
                }
            }
            return true;
        }
    return false;
}
}
#endif
