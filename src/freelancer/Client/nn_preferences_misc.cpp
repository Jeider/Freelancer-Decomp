#include "nn_preferences.h"
#include "nn_button_control.h"
#include "nn_text_control.h"
#include "nn_dropdown.h"
#include "nn_ui_pulse.h"
#include "wire_controls.h"
#include "ui_scroll.h"
#include "ids_strings.h"
#include "game_options.h"
#include "perf_options.h"
#include "player_auto_turrets.h"
#include "port_config.h"
#include "navigation_settings.h"
#include "hud_tilt.h"
#include "common_misc.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <string>

namespace
{
    constexpr int HudTiltSetting = 8;
    constexpr int WeaponGroupsSetting = 9;
    bool Russian() { return _stricmp(PortLanguage(), "ru") == 0; }
    void Visible(WinControl* c, bool show) { if (c) c->SetProperty(1, !show, 0); }
    std::wstring IdText(unsigned id)
    {
        wchar_t text[256] = {};
        GetIdsStringWWithRawFallback(id, text, 256);
        return text;
    }
    bool Available(NnPreferences const& page, FPrefMiscRow const& row)
    {
        if (row.Setting < 0) return FindPerfOptionByIds(row.Option.Id) && !(row.Option.Byte15 && page.bInGame);
        if (row.Setting == HudTiltSetting) {
#if defined(FREELANCER_RP9) && defined(FREELANCER_WIDESCREEN_SUPPORT)
            return true;
#else
            return false;
#endif
        }
        if (row.Setting >= 5 && row.Setting <= 7) {
#ifdef FREELANCER_PLAYER_FLIGHT_ACTIONS
            return true;
#else
            return false;
#endif
        }
        if (row.Setting < 3 || row.Setting == WeaponGroupsSetting) return true;
#ifdef FREELANCER_PLAYER_AUTO_TURRETS
        return PlayerAutoTurrets::Enabled();
#else
        return false;
#endif
    }
    float ReadValue(FPrefMiscRow const& row)
    {
        if (row.Setting < 0)
        {
            auto* option = FindPerfOptionByIds(row.Option.Id);
            return option ? option->Applied : 0;
        }
        switch (row.Setting)
        {
        case WeaponGroupsSetting: return GetShowWeaponGroups();
        case HudTiltSetting: return HudTilt::ConfiguredAngle();
        case 5: case 6: case 7: return float(NavigationSettings::Get(NavigationSettings::Setting(row.Setting-5)));
        case 0: return float(GetSavedRadarAutoMode());
        case 1: return !GetSavedTargetingWindowLocked();
        case 2: return !GetSavedHealthWindowLocked();
#ifdef FREELANCER_PLAYER_AUTO_TURRETS
        case 3: return PlayerAutoTurrets::GetMode() != PlayerAutoTurrets::Mode::Manual;
        case 4: return float(PlayerAutoTurrets::ReservePercent());
#endif
        default: return 0;
        }
    }
    bool ApplyValue(FPrefMiscRow const& row)
    {
        if (row.Setting < 0)
        {
            if (auto* option = FindPerfOptionByIds(row.Option.Id))
            {
                option->Value = row.Value;
                if (option->Applied != row.Value)
                {
                    option->Applied = row.Value;
                    if (option->Apply) option->Apply(row.Value);
                }
            }
            return true;
        }
        switch (row.Setting)
        {
        case WeaponGroupsSetting: SetShowWeaponGroups(row.Value != 0); return HudPreferencesSaved();
        case HudTiltSetting: HudTilt::SetConfiguredAngle(row.Value); break;
        case 5: case 6: case 7: return NavigationSettings::Set(NavigationSettings::Setting(row.Setting-5),int(row.Value));
        case 0: SetSavedRadarAutoMode(unsigned(row.Value)); break;
        case 1: SetSavedTargetingWindowLocked(row.Value == 0); break;
        case 2: SetSavedHealthWindowLocked(row.Value == 0); break;
#ifdef FREELANCER_PLAYER_AUTO_TURRETS
        case 3: SetSavedAutoTurretsEnabled(row.Value != 0); break;
        case 4: PlayerAutoTurrets::SetReservePercent(unsigned(row.Value)); break;
#endif
        }
        return row.Setting == HudTiltSetting || HudPreferencesSaved();
    }
    bool IsPercentage(FPrefMiscRow const& row)
    {
        return row.Setting < 0 && row.Option.bSlider;
    }
    int CycleMaximum(FPrefMiscRow const& row)
    {
        if (row.Setting == HudTiltSetting) return int(HudTilt::MaxAngleDegrees);
        return row.Setting == 0 ? 2 : row.Setting == 4 ? 18 : IsPercentage(row) ? 100 : 1;
    }
    bool IsDropdown(FPrefMiscRow const& row) { return row.Setting==0 || row.Setting==5; }
    bool IsToggle(FPrefMiscRow const& row) { return !IsDropdown(row) && row.Setting!=4 && row.Setting!=HudTiltSetting && !IsPercentage(row); }
    std::wstring Label(FPrefMiscRow const& row)
    {
        if (row.Setting < 0) return IdText(row.Option.Id);
        if (row.Setting == WeaponGroupsSetting) return Russian()?L"\u041f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0442\u044c \u0433\u0440\u0443\u043f\u043f\u044b \u043e\u0440\u0443\u0434\u0438\u0439":L"Show weapon groups";
        if (row.Setting == HudTiltSetting) return Russian()?L"\u041d\u0430\u043a\u043b\u043e\u043d HUD":L"HUD tilt";
        if (row.Setting >= 5 && row.Setting <= 7) {
            wchar_t const* const ru[]={L"\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440 \u043c\u0430\u0440\u0448\u0440\u0443\u0442\u0430",L"\u0410\u0432\u0442\u043e\u043f\u0440\u043e\u043b\u0451\u0442 \u043c\u0430\u0440\u0448\u0440\u0443\u0442\u0430 \u043f\u043e F2",L"\u0410\u0432\u0442\u043e\u0441\u0442\u044b\u043a\u043e\u0432\u043a\u0430 \u0441 \u0431\u0430\u0437\u0430\u043c\u0438"};
            wchar_t const* const en[]={L"Route generator",L"Follow route with F2",L"Auto-dock with bases"};
            return (Russian()?ru:en)[row.Setting-5];
        }
        wchar_t const* const ru[] = {L"\u0410\u0432\u0442\u043e\u043f\u043e\u043a\u0430\u0437 \u0440\u0430\u0434\u0430\u0440\u0430",L"\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043e\u0442\u043a\u0440\u044b\u0432\u0430\u0442\u044c \u0441\u0442\u0430\u0442\u0443\u0441 \u0432\u0440\u0430\u0433\u0430",
            L"\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0442\u044c \u0441\u0442\u0430\u0442\u0443\u0441 \u043a\u043e\u0440\u0430\u0431\u043b\u044f",L"\u0412\u043a\u043b\u044e\u0447\u0438\u0442\u044c \u0430\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0438",L"\u0420\u0435\u0437\u0435\u0440\u0432 \u044d\u043d\u0435\u0440\u0433\u0438\u0438 \u0430\u0432\u0442\u043e\u0442\u0443\u0440\u0435\u043b\u0435\u0439"};
        wchar_t const* const en[] = {L"Show radar automatically",L"Open enemy status automatically",
            L"Show ship status automatically",L"Enable auto turrets",L"Auto turret energy reserve"};
        return (Russian() ? ru : en)[row.Setting];
    }
    std::wstring ValueText(FPrefMiscRow const& row)
    {
        if (row.Setting == HudTiltSetting) return std::to_wstring(int(row.Value)) + L"\u00b0";
        if (row.Setting == 5) return row.Value ? (Russian()?L"\u041e\u0431\u0445\u043e\u0434 \u043f\u0440\u0435\u043f\u044f\u0442\u0441\u0442\u0432\u0438\u0439":L"Avoid obstacles") : (Russian()?L"\u0421\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u044b\u0439":L"Standard");
        if (row.Setting == 0)
        {
            wchar_t const* const ru[] = {L"\u041d\u0435\u0442",L"\u041f\u0440\u0438 \u043f\u043e\u044f\u0432\u043b\u0435\u043d\u0438\u0438 \u043b\u044e\u0431\u043e\u0439 \u0446\u0435\u043b\u0438",L"\u041f\u0440\u0438 \u043f\u043e\u044f\u0432\u043b\u0435\u043d\u0438\u0438 \u043f\u0440\u043e\u0442\u0438\u0432\u043d\u0438\u043a\u0430"};
            wchar_t const* const en[] = {L"No",L"When any contact appears",L"When an enemy appears"};
            return (Russian() ? ru : en)[(std::max)(0,(std::min)(2,int(row.Value)))];
        }
        if (row.Setting == 4) return std::to_wstring(int(row.Value)) + L"%";
        if (IsPercentage(row)) return std::to_wstring(int(row.Value * 100)) + L"%";
        return IdText(row.Value > .999f ? 0x65f : 0x67a);
    }
}

bool NnPreferences::CreateMiscPage(float columnX, float columnY, float step)
{
    float const buttonAt[3] = {columnX,columnY-step*4,0}, half[3] = {.13f,.026f,0};
    MiscButton = static_cast<NnButtonControl*>(CreateButtonControl("MiscButton",
        "Interface\\NeuroNet\\Inventory\\FRONT_button.cmp",nullptr,"ui_select_item",nullptr,
        buttonAt,nullptr,half,0,0,0,0,0,0,0));
    float const captionAt[3] = {columnX-.13f,buttonAt[1]+.015f,0};
    MiscText = static_cast<NnTextControl*>(CreateTextControl("MiscText","ButtonText",captionAt,
        nullptr,.258f,.03f,1.25f,1897,1,0,1));
    if (!MiscButton || !MiscText) return false;
    MiscButton->SetMontageMode(1);
    MiscText->SetProperty(0x24,1,0);
    for (auto const& option : MiscOptions)
    {
        FPrefMiscRow row; row.Option = option;
        row.Tab=(option.Id==1400 || option.Id==1401)?1:0;
        MiscRows.push_back(row);
    }
    for (int setting=0;setting<10;++setting)
    {
        FPrefMiscRow row; row.Setting=setting; row.Tab=(setting>=5 && setting<=7)?1:0; MiscRows.push_back(row);
    }
    auto text = [&](char const* name,wchar_t const* value,float x,float y,float width,int align,float scale=1.f)
    {
        float const at[3] = {x,y,0};
        auto* c = static_cast<NnTextControl*>(CreateTextControl(name,"ItemName",at,nullptr,width,.027f,scale,0,align,0,1));
        if (c) { c->SetText(value);c->Flags &= ~kWin3DPickable;MiscWidgets.push_back(c); }
        return c;
    };
    for (int tab=0;tab<2;++tab) {
        char name[40]; sprintf_s(name,"MiscTab%d",tab);
        float const at[3]={.02f+tab*.27f,.197f,0},halfTab[3]={.13f,.015f,0};
        MiscTabButtons[tab]=static_cast<WireButtonControl*>(CreateWireButtonControl(
            name,"ui_select_item",at,halfTab,0,0,0,0,0xf));
        sprintf_s(name,"MiscTabText%d",tab);
        MiscTabTexts[tab]=text(name,tab ? (Russian()?L"\u041d\u0430\u0432\u0438\u0433\u0430\u0446\u0438\u044f":L"Navigation") :
            (Russian()?L"\u041e\u0431\u0449\u0435\u0435":L"General"),at[0]-.125f,.211f,.25f,1);
        if (!MiscTabButtons[tab] || !MiscTabTexts[tab]) return false;
        MiscTabButtons[tab]->WireState &= ~0x40;
        MiscWidgets.push_back(MiscTabButtons[tab]);
    }
    MiscSaveHint=text("MiscSaveHint",L"",-.11f,-.275f,.54f,0);
    if (!MiscSaveHint) return false;
    for (int slot=0;slot<MiscVisibleRows;++slot)
    {
        auto& cell = MiscCells[slot];
        float const y = .120f - slot*.035f;
        char name[48];
        sprintf_s(name,"MiscLabel%d",slot); cell.Label=text(name,L"",-.11f,y,.28f,0);
        sprintf_s(name,"MiscValue%d",slot); cell.Value=text(name,L"",.188f,y,.193f,1,.9f);
        float const valueAt[3] = {.2845f,y-.0135f,0},valueHalf[3] = {.1045f,.0145f,0};
        sprintf_s(name,"MiscValueRule%d",slot);
        cell.ValueRule=static_cast<WireStaticControl*>(CreateWireStaticControl(name,valueAt,valueHalf,0,0,0,0xf));
        float const arrowAt[3] = {.4f,y-.0135f,0},arrowHalf[3] = {.0105f,.0145f,0};
        sprintf_s(name,"MiscArrowRule%d",slot);
        cell.ArrowRule=static_cast<WireStaticControl*>(CreateWireStaticControl(name,arrowAt,arrowHalf,0,0,0,0xf));
        // Same vertical UICycle, arrow dimensions and separate frames as the
        // native resolution selector. UIScroll owns its absolute depth.
        float const cycleAt[3] = {.394f,y-.001f,-1};
        sprintf_s(name,"MiscCycle%d",slot);
        cell.Cycle=CreateUICycle(name,cycleAt,.012f,.025f,0,1,0,0);
        float const toggleAt[3]={.395f,y-.0135f,0},toggleHalf[3]={.015f,.015f,0};
        sprintf_s(name,"MiscToggle%d",slot);
        cell.Toggle=static_cast<NnButtonControl*>(CreateToggleButtonControl(name,
            "Interface\\NeuroNet\\Inventory\\check.3db","Interface\\NeuroNet\\Inventory\\repairblackbox.3db",
            "ui_shipview_select",nullptr,toggleAt,nullptr,toggleHalf,0,0,0,0,0x65f,0x67a));
        float const choiceAt[3]={.295f,y-.0135f,0},choiceHalf[3]={.115f,.0145f,0};
        sprintf_s(name,"MiscChoice%d",slot);
        cell.Choice=static_cast<WireButtonControl*>(CreateWireButtonControl(
            name,"ui_select_item",choiceAt,choiceHalf,0,0,0,0,0xf));
        if (!cell.Label || !cell.Value || !cell.ValueRule || !cell.ArrowRule || !cell.Cycle ||
            !cell.Toggle || !cell.Choice) return false;
        cell.Toggle->SetProperty(0x35,1,0);
        memcpy(cell.Toggle->Colour,&G_NnPaletteArgb_679b94,4);
        cell.Value->SetProperty(0x24,1,0);
        cell.Cycle->SetStepMode(true);cell.Cycle->SetPageField(1);
        for (WinControl* c : {static_cast<WinControl*>(cell.ValueRule),static_cast<WinControl*>(cell.ArrowRule),
                             static_cast<WinControl*>(cell.Cycle),static_cast<WinControl*>(cell.Toggle),
                             static_cast<WinControl*>(cell.Choice)}) MiscWidgets.push_back(c);
    }
    MiscDropdown=CreateNnDropdownPopup(this);
    if (!MiscDropdown) return false;
    float const scrollAt[3] = {.415f,.124f,-1};
    MiscScroll=CreateUIScroll("MiscScroll",scrollAt,.012f,.385f,0,0,MiscVisibleRows,0);
    if (!MiscScroll) return false;
    MiscScroll->SetStepMode(true);
    MiscScroll->SetPageField(float(MiscVisibleRows));
    MiscWidgets.push_back(MiscScroll);
    SetMiscHidden(true);
    return true;
}

void NnPreferences::SnapshotMisc()
{
    for (auto& row : MiscRows) row.Original=row.Value;
}

bool NnPreferences::CommitMisc()
{
    // Global options are staged until the native Apply confirmation accepts them.
    for (auto const& row : MiscRows)
        if (row.Setting >= 0 && Available(*this,row) && row.Value != row.Original && !ApplyValue(row)) {
            MiscSaveFailed=true;return false;
        }
    MiscSaveFailed=false;
    return true;
}

void NnPreferences::RevertMisc()
{
    MiscSaveFailed=false;
    for (auto& row : MiscRows)
    {
        bool const changed=row.Value!=row.Original;
        row.Value=row.Original;
        if (changed && row.Setting < 0) ApplyValue(row);
    }
    RefreshMiscRows();
}

void NnPreferences::SetMiscHidden(bool hidden)
{
    CloseMiscDropdown();
    for (auto* c : MiscWidgets) Visible(c,!hidden);
    if (!hidden) RefreshMiscRows();
}

void NnPreferences::RefreshMiscRows()
{
    CloseMiscDropdown();
    MiscRowIndices.clear();
    for (int i=0;i<int(MiscRows.size());++i) if (MiscRows[i].Tab==MiscTab) MiscRowIndices.push_back(i);
    for (int tab=0;tab<2;++tab) {
        auto colour=tab==MiscTab?G_NnPaletteArgb_679ba4:G_NnPaletteArgb_679bb0;
        MiscTabTexts[tab]->TextColour=colour;
        MiscTabButtons[tab]->bUseColour=true;
        memcpy(MiscTabButtons[tab]->Colour,&colour,4);
    }
    MiscSaveHint->SetText(MiscSaveFailed ?
        (Russian()?L"\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0441\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438":L"Could not save settings") : L"");
    MiscTop=(std::max)(0,(std::min)(MiscTop,int(MiscRowIndices.size())-MiscVisibleRows));
    for (int slot=0;slot<MiscVisibleRows;++slot)
    {
        auto& cell=MiscCells[slot];
        int const visibleIndex=MiscTop+slot;
        bool const exists=visibleIndex<int(MiscRowIndices.size());
        for (WinControl* c : {static_cast<WinControl*>(cell.Label),static_cast<WinControl*>(cell.Value)}) Visible(c,exists);
        for (WinControl* c : {static_cast<WinControl*>(cell.ValueRule),static_cast<WinControl*>(cell.ArrowRule),
                             static_cast<WinControl*>(cell.Cycle),static_cast<WinControl*>(cell.Toggle),
                             static_cast<WinControl*>(cell.Choice)}) Visible(c,false);
        if (!exists) continue;
        auto const& row=MiscRows[MiscRowIndices[visibleIndex]];
        bool const available=Available(*this,row);
        cell.Label->SetText(Label(row).c_str());
        cell.Value->SetText(available ? ValueText(row).c_str() : (Russian()?L"\u041d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e":L"Unavailable"));
        cell.Label->TextColour=cell.Value->TextColour=available?G_NnPaletteArgb_679bb0:G_NnPaletteArgb_679b94;
        if (IsDropdown(row)) {
            cell.Choice->ButtonState=static_cast<unsigned char>((cell.Choice->ButtonState&~4u)|(available?4u:0));
            Visible(cell.Choice,true);
        } else if (IsToggle(row)) {
            cell.Toggle->SetProperty(0x30,row.Value>.999f,0);
            Visible(cell.Toggle,available);
        } else {
            int const current=row.Setting==HudTiltSetting?int(row.Value):row.Setting==4?int(row.Value/5):int(std::round(row.Value*100));
            cell.Cycle->SetProperty(0x37,0,CycleMaximum(row));
            cell.Cycle->SetProperty(0x38,current,0);
            // Native vertical cycles subtract Step on the upper arrow, including
            // hold-repeat and wheel input. Reverse only these numeric settings.
            cell.Cycle->SetStep(row.Setting==HudTiltSetting ? -HudTilt::AngleStepDegrees : row.Setting==4 ? -1.f : 1.f);
            Visible(cell.Cycle,available);
            Visible(cell.ValueRule,true);Visible(cell.ArrowRule,true);
        }
    }
    int const maximum=(std::max)(0,int(MiscRowIndices.size())-MiscVisibleRows);
    MiscScroll->SetProperty(0x37,0,(std::max)(0,int(MiscRowIndices.size())-1));
    MiscScroll->SetProperty(0x38,MiscTop,0);
    Visible(MiscScroll,maximum>0);
    bDirty=0;
    for (auto const& row : MiscRows) if (row.Value!=row.Original) bDirty=1;
    CancelText->TextColour=bDirty?G_NnPaletteArgb_679bb0:G_NnPaletteArgb_679b94;
    CancelButton->bUseColour=!bDirty;
    CancelButton->ButtonState=static_cast<unsigned char>((CancelButton->ButtonState&~4u)|(bDirty?4u:0));
}

void NnPreferences::EnterMiscPage()
{
    if (CurPage==7 && !bFlipping) return;
    if (!bFlipping)
    {
        CurPage=7;bFlipping=1;MiscText->TextColour=G_NnPaletteArgb_679ba4;return;
    }
#ifdef FREELANCER_PLAYER_AUTO_TURRETS
    if (bInGame) PlayerAutoTurrets::Reconcile();
#endif
    for (auto& row : MiscRows) row.Value=ReadValue(row);
    SnapshotMisc();MiscTop=0;
    Title->SetText(IdText(1897).c_str());
    for (WinControl* c : {static_cast<WinControl*>(Title),static_cast<WinControl*>(CancelButton),
                         static_cast<WinControl*>(CancelText),static_cast<WinControl*>(DefaultsButton),
                         static_cast<WinControl*>(DefaultsText)}) Visible(c,true);
    SetMiscHidden(false);
}

void NnPreferences::LeaveMiscPage()
{
    if (bDirty) { ShowConfirmDialog(true);return; }
    SetMiscHidden(true);
    for (WinControl* c : {static_cast<WinControl*>(Title),static_cast<WinControl*>(CancelButton),
                         static_cast<WinControl*>(CancelText),static_cast<WinControl*>(DefaultsButton),
                         static_cast<WinControl*>(DefaultsText)}) Visible(c,false);
    MiscText->TextColour=G_NnPaletteArgb_679bb0;
}

bool NnPreferences::MiscProperty(int msg, Win3D* source, uintptr_t value)
{
    if (source==MiscDropdown && msg==0x3e) {
        int const index=MiscDropdownRow;
        CloseMiscDropdown();
        if (index<0 || index>=int(MiscRows.size())) return true;
        auto& row=MiscRows[index];
        if (CurPage!=7 || row.Tab!=MiscTab || !Available(*this,row) || !IsDropdown(row) ||
            value>unsigned(CycleMaximum(row))) return true;
        row.Value=float(value);
        RefreshMiscRows();return true;
    }
    for (int tab=0;tab<2;++tab) if (msg==0x26 && source==MiscTabButtons[tab]) {
        MiscTab=tab;MiscTop=0;RefreshMiscRows();return true;
    }
    if (msg==0x3e && source==MiscScroll) { MiscTop=int(value);RefreshMiscRows();return true; }
    if (msg==0x26 && source==CancelButton) { RevertMisc();return true; }
    if (msg==0x26 && source==DefaultsButton)
    {
        for (auto& row : MiscRows) if (row.Tab==MiscTab && Available(*this,row))
        {
            if (row.Setting < 0)
            {
                if (row.Option.Default < 0) continue;
                row.Value=row.Option.bSlider?row.Option.Default*.01f:float(row.Option.Default!=0);
                ApplyValue(row);
            }
            else if (row.Setting==HudTiltSetting) row.Value=0;
            else if (row.Setting==WeaponGroupsSetting) row.Value=1;
            else if (row.Setting>=5 && row.Setting<=7) row.Value=float(NavigationSettings::Default(NavigationSettings::Setting(row.Setting-5)));
            else row.Value=row.Setting==4 ? float((std::max)(0,(std::min)(90,PortConfigInt("AutoTurrets","reserve_percent",35)))/5*5) :
                float(row.Setting==1 || row.Setting==2);
        }
        RefreshMiscRows();return true;
    }
    for (int slot=0;slot<MiscVisibleRows;++slot)
    {
        int const visibleIndex=MiscTop+slot;
        if (visibleIndex>=int(MiscRowIndices.size())) break;
        int const index=MiscRowIndices[visibleIndex];
        auto const& cell=MiscCells[slot];auto& row=MiscRows[index];
        if (source==cell.Choice) {
            if (msg!=0x26 || !Available(*this,row) || !IsDropdown(row)) return true;
            CloseMiscDropdown();
            std::vector<std::wstring> choices;
            auto choice=row;
            for (int i=0;i<=CycleMaximum(row);++i) {choice.Value=float(i);choices.push_back(ValueText(choice));}
            if (MiscDropdown->Open(.18f,.120f-slot*.035f,.23f,choices,int(row.Value))) MiscDropdownRow=index;
            return true;
        }
        if (source!=cell.Cycle && source!=cell.Toggle) continue;
        if (!Available(*this,row)) return true;
        if (source==cell.Toggle && IsToggle(row) && msg==0x30) row.Value=value==0?1.f:0.f;
        else if (source==cell.Cycle && !IsToggle(row) && !IsDropdown(row) && msg==0x3e) {
            float const selected=float((std::min)(unsigned(CycleMaximum(row)),unsigned(value)));
            row.Value=row.Setting==HudTiltSetting?selected:row.Setting==4?selected*5:selected*.01f;
        } else return true;
        if (row.Setting < 0) ApplyValue(row);
        RefreshMiscRows();return true;
    }
    return false;
}

void NnPreferences::CloseMiscDropdown()
{
    if (MiscDropdown) MiscDropdown->Close();
    MiscDropdownRow=-1;
}

void NnPreferences::DrawMiscDropdown()
{
    if (CurPage!=7 || bConfirmMode) return;
    for (auto const& cell:MiscCells)
        if (cell.Choice && (cell.Choice->Flags&kWin3DVisible) && (cell.Choice->ButtonState&4))
            DrawNnDropdownCaret(cell.Choice);
    if (MiscDropdown) MiscDropdown->Draw();
}
