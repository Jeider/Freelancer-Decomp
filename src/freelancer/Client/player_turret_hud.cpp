#include "player_turret_hud.h"
#ifdef FREELANCER_PLAYER_AUTO_TURRETS
#include "player_auto_turrets.h"
#include "hud_status_core.h"
#include "nn_button_control.h"
#include "nn_montage_draw.h"
#include "nn_ui_pulse.h"
#include "hud_target.h"
#include "hud_widescreen.h"
#include "common_cequip.h"
#include "common_archetype.h"
#include "common_misc.h"
#include "ids_strings.h"
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
    constexpr int Rows = 12; // two main buttons; target/free/reserve; six guns; next page
    HUD_Status* owner = nullptr;
    WinControl* background = nullptr;
    WinControl* buttons[Rows] = {};
    WinControl* captions[Rows] = {};
    FButtonMontageTile tiles[Rows] = {};
    FButtonMontageTile* originals[Rows] = {};
    std::wstring lastText[Rows];
    bool open = false, shown = false;
    unsigned page = 0;

    bool Russian() { return _stricmp(PortLanguage(), "ru") == 0; }
    std::wstring Caption(unsigned row)
    {
        bool const ru = Russian();
        if (row == 0) return GetMode() == Mode::Manual ? (ru ? L"\u0410\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0438: \u0432\u043a\u043b\u044e\u0447\u0438\u0442\u044c" : L"Auto turrets: engage")
            : (ru ? L"\u0410\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0438: \u0421\u0422\u041e\u041f" : L"Auto turrets: STOP");
        if (row == 1)
        {
            static wchar_t const* const en[] = {L"Off", L"Ready", L"No active turrets", L"No hostile contact", L"No scanner", L"Suspended", L"Energy reserve", L"Aiming", L"Obstructed", L"Firing", L"Single player only"};
            static wchar_t const* const rus[] = {L"\u0412\u044b\u043a\u043b", L"\u0413\u043e\u0442\u043e\u0432\u044b", L"\u041d\u0435\u0442 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445 \u0442\u0443\u0440\u0435\u043b\u0435\u0439", L"\u041d\u0435\u0442 \u0432\u0440\u0430\u0436\u0435\u0431\u043d\u043e\u0439 \u0446\u0435\u043b\u0438", L"\u041d\u0435\u0442 \u0441\u043a\u0430\u043d\u0435\u0440\u0430", L"\u041f\u0440\u0438\u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u044b", L"\u0420\u0435\u0437\u0435\u0440\u0432 \u044d\u043d\u0435\u0440\u0433\u0438\u0438", L"\u041d\u0430\u0432\u0435\u0434\u0435\u043d\u0438\u0435", L"\u041f\u0440\u0435\u043f\u044f\u0442\u0441\u0442\u0432\u0438\u0435", L"\u041e\u0433\u043e\u043d\u044c", L"\u0422\u043e\u043b\u044c\u043a\u043e \u0441\u0438\u043d\u0433\u043b"};
            return (ru ? rus : en)[static_cast<unsigned>(GetStatus())];
        }
        if (row == 2) return ru ? L"\u0410\u0442\u0430\u043a\u043e\u0432\u0430\u0442\u044c \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u0443\u044e \u0446\u0435\u043b\u044c" : L"Attack selected target";
        if (row == 3) return ru ? L"\u0421\u0432\u043e\u0431\u043e\u0434\u043d\u044b\u0439 \u043e\u0433\u043e\u043d\u044c \u043f\u043e \u0432\u0440\u0430\u0433\u0430\u043c" : L"Free fire on hostiles";
        if (row == 4) return (ru ? L"\u0420\u0435\u0437\u0435\u0440\u0432 \u044d\u043d\u0435\u0440\u0433\u0438\u0438: " : L"Energy reserve: ") + std::to_wstring(ReservePercent()) + L"%";
        if (row == 11) return (ru ? L"\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0435 \u0442\u0443\u0440\u0435\u043b\u0438: " : L"Next turrets: ") + std::to_wstring(page + 1);
        unsigned const index = page * 6 + row - 5;
        auto* gun = Member(index);
        if (!gun) return L"";
        wchar_t name[256] = {};
        GetIdsStringW(gun->GunArch()->IdsName, name, 256);
        std::wstring result = name;
        if (!gun->IsFunctioning()) result += ru ? L" [\u0432\u044b\u043a\u043b]" : L" [inactive]";
        return result;
    }
    bool Bind(HUD_Status* host)
    {
        if (owner) return owner == host;
        owner = host;
        char path[1024] = {};
        char const* beta = "interface\\hud\\HUD_player_auto_turret.3db";
        GetFileSysPath(path, beta, DALib::Data);
        bool const haveBeta = GetFileAttributesA(path) != INVALID_FILE_ATTRIBUTES;
        float const zero[3] = {}, half[3] = {0.012f, 0.012f, 0};
        char const* panel = "interface\\hud\\HUD_player_auto_turret_panel.cmp";
        GetFileSysPath(path, panel, DALib::Data);
        if (GetFileAttributesA(path) != INVALID_FILE_ATTRIBUTES)
        {
            background = owner->CreateStaticControl("PlayerTurretBackground", panel,
                zero, nullptr, zero, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, zero);
            if (background)
            {
                background->Flags &= ~kWin3DPickable;
                // StaticControl does not enable attachment in SetPosition like
                // ButtonControl does. Without this, panelAttach's Z is ignored.
                background->bAttached = 1;
                // Beta inventory frame: approximately 0.46 x 0.51 native units.
                float const scale[9] = {0.61f, 0, 0, 0, 0.72f, 0, 0, 0, 1};
                background->SetOrientation(scale);
            }
        }
        for (int i = 0; i < Rows; ++i)
        {
            char name[48]; sprintf_s(name, "PlayerTurretButton%d", i);
            if (i < 2) buttons[i] = owner->CreateButtonControl(name,
                i == 0 && haveBeta ? beta : i == 1 ? "interface\\neuronet\\inventory\\equipmenticon.3db" : "interface\\hud\\HUD_targetedobject.3db",
                nullptr, "ui_item_select", nullptr, zero, nullptr, half, 0, 1, 0, 0, Base+i, 0, 0);
            sprintf_s(name, "PlayerTurretText%d", i);
            captions[i] = owner->CreateTextControl(name, "HudSmall", zero, nullptr, 0.22f, 0.018f, 1, 0, 0, 0, 1);
            if ((i < 2 && !buttons[i]) || !captions[i]) { Release(host); return false; }
            if (i >= 2) captions[i]->SetProperty(0x24, 1, 0);
            else captions[i]->Flags &= ~kWin3DPickable;
            if (i >= 2) continue;
            auto* button = static_cast<NnButtonControl*>(buttons[i]);
            originals[i] = button->MontageTile;
            if (button->MontageTile)
            {
                tiles[i] = *button->MontageTile; tiles[i].Scale = 0.017f;
                button->MontageTile = &tiles[i];
            }
            if (ClientMeshHolderHasInstance(&button->MeshHolder))
            {
                float extent = 0, unused[3] = {};
                DALib::Engine->GetInstanceExtent(button->MeshHolder.EngineInstance, 1, &extent, unused);
                if (std::isfinite(extent) && extent > 0)
                {
                    float orientation[9];
                    for (int j = 0; j < 9; ++j) orientation[j] = button->Orientation[j] * 0.017f / extent;
                    button->SetOrientation(orientation);
                }
            }
        }
        return true;
    }
}

bool Text(unsigned id, std::wstring& text)
{
    if (id >= Base + 0x20 && id < Base + 0x24)
    {
        unsigned const action = id - Base - 0x20;
        if (action == 1 || action == 2) text = Caption(action + 1);
        else text = Russian() ? (action == 0 ? L"\u0410\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0438: \u0432\u043a\u043b/\u0432\u044b\u043a\u043b" : L"\u0410\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0438: \u0421\u0422\u041e\u041f")
                             : (action == 0 ? L"Auto turrets: toggle" : L"Auto turrets: STOP");
        return true;
    }
    if (id < Base || id >= Base + Rows) return false;
    unsigned const row = id - Base;
    if (row == 1) text = Russian() ? L"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u0430\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0435\u0439" : L"Auto turret settings";
    else text = Caption(row);
    return true;
}
void Release(HUD_Status const* host)
{
    if (!owner || host != owner) return;
    if (background) { background->Destroy(); delete background; background = nullptr; }
    for (int i = 0; i < Rows; ++i)
    {
        if (buttons[i])
        {
            static_cast<NnButtonControl*>(buttons[i])->MontageTile = originals[i];
            buttons[i]->Destroy(); delete buttons[i]; buttons[i] = nullptr;
        }
        if (captions[i]) { captions[i]->Destroy(); delete captions[i]; captions[i] = nullptr; }
        lastText[i].clear();
    }
    owner = nullptr; shown = open = false; page = 0;
}
void Update(HUD_Status* host, float const* attachment, bool visible)
{
    if (!Enabled() || !Bind(host)) return;
    Reconcile();
    shown = visible;
    if (!shown) open = false;
    if (page * 6 >= MemberCount()) page = 0;
    // Independent of the lower weapon panel's attachment; HUD_Status retains
    // the native widescreen right-edge shift for all these children.
    float const panelAttach[3] = {-host->Position[0], -host->Position[1], -1.0f-host->Position[2]};
    if (background)
    {
        background->SetProperty(1, !(shown && open), 0);
        std::memcpy(background->AttachPosition, panelAttach, sizeof(panelAttach));
        background->SetOffset(0.365f, 0.112f, -0.005f);
    }
    for (int i = 0; i < Rows; ++i)
    {
        bool show = shown && (i < 2 || open);
        if (i >= 5 && i <= 10) show &= Member(page*6+i-5) != nullptr;
        if (i == 11) show &= MemberCount() > 6;
        if (buttons[i]) buttons[i]->SetProperty(1, !show, 0);
        // Only the ON/OFF header remains; diagnostic status is not a panel row.
        captions[i]->SetProperty(1, !(show && open && i != 1), 0);
        bool const selected = i == 0 ? GetMode() != Mode::Manual : i == 1 ? open :
            i == 2 ? GetPreferredMode() == Mode::Target : i == 3 ? GetPreferredMode() == Mode::Hostiles :
            i >= 5 && i <= 10 && Selected(page*6+i-5);
        if (buttons[i])
        {
            buttons[i]->SetProperty(0xc, selected, 0);
            std::memcpy(buttons[i]->AttachPosition, attachment, sizeof(buttons[i]->AttachPosition));
            buttons[i]->SetOffset(0.255f, -0.323f-i*0.028f, 0);
        }
        float const y = i < 2 ? 0.260f : 0.222f - (i-2)*0.026f - (i >= 4 ? 0.016f : 0) - (i >= 5 ? 0.016f : 0);
        std::memcpy(captions[i]->AttachPosition, panelAttach, sizeof(captions[i]->AttachPosition));
        captions[i]->SetOffset(0.257f, y, 0);
        std::wstring const text = i == 0 ?
            (Russian() ? (GetMode() == Mode::Manual ? L"\u0410\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0438: \u0412\u042b\u041a\u041b" : L"\u0410\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0438: \u0412\u041a\u041b")
                        : (GetMode() == Mode::Manual ? L"Auto turrets: OFF" : L"Auto turrets: ON")) : Caption(i);
        if (text != lastText[i])
        {
            captions[i]->SetProperty(0x1d, reinterpret_cast<uintptr_t>(text.c_str()), 0);
            lastText[i] = text;
        }
        unsigned long color = selected && i != 1 ? G_NnPaletteArgb_679ba4 : G_NnPaletteArgb_679bb0;
        if (show && open && i >= 2 && !HudIsMousePickBlocked())
        {
            float ray[3];
#ifdef FREELANCER_WIDESCREEN_SUPPORT
            FWidescreenHudShiftScope scope(WidescreenHudShiftPixelsFor(captions[i]), false);
            WidescreenHudCursorRay(ray);
#else
            Win3DGetMouseRay(ray);
#endif
            if (captions[i]->HitTest(ray)) NnUiPulseBlendFromArgb(&color, color);
        }
        captions[i]->SetProperty(0x33, reinterpret_cast<uintptr_t>(&color), 1);
    }
}
bool Property(HUD_Status const* host, int msg, uintptr_t control)
{
    if (host != owner || !shown || msg != 0x26 || HudIsMousePickBlocked()) return false;
    for (int i = 0; i < Rows; ++i) if (reinterpret_cast<uintptr_t>(i < 2 ? buttons[i] : captions[i]) == control)
    {
        if (i >= 2 && !open) return true;
        Reconcile();
        if (i == 0) SetMode(GetMode() == Mode::Manual ? GetPreferredMode() : Mode::Manual);
        else if (i == 1) open = !open;
        else if (i == 2) SetPreferredMode(Mode::Target);
        else if (i == 3) SetPreferredMode(Mode::Hostiles);
        else if (i == 4) CycleReserve();
        else if (i == 11) page = (page+1)*6 >= MemberCount() ? 0 : page+1;
        else ToggleMember(page*6+i-5);
        return true;
    }
    return false;
}
}
#endif
